"""Minimal provider-independent API foundation."""

from datetime import date
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from apps.api.auth import AuthSettings, authenticate, issue_token, require_session
from apps.api.copy_formulas import approach_for_formula, select_copy_approach
from apps.api.drafting import ChannelAdaptedDraftService, EditableTextDraft
from apps.api.editorial_review import (
    EditorialContent,
    EditorialReviewService,
    EditorialTransitionError,
    HumanReview,
    RegenerationRequest,
)
from apps.api.editorial_store import EditorialContentStore, EditorialPlanStore
from apps.api.llm import LlmConfigurationError, build_text_generator
from apps.api.models import GuidedBrief
from apps.api.config import EditorialPersistenceSettings, RagLocalSettings
from apps.api.drafting import RagGroundedDraftService
from apps.api.editorial_planning import EditorialPlan, reschedule_item
from apps.api.rag import LocalChromaIndex


class ReadinessResponse(BaseModel):
    """Stable response returned by the local readiness endpoint."""

    status: Literal["ready"] = "ready"
    service: Literal["api"] = "api"


class DraftRequest(BaseModel):
    """Validated request for one or more channel-adapted text drafts."""

    brief: GuidedBrief
    rag_enabled: bool = False
    brand_id: str | None = None
    business_id: str | None = None
    top_k: int = 3
    formula: Literal["AIDA", "PAS", "4CS", "BAB", "4PS", "OPEN_LOOP"] | None = None


class DraftResponse(BaseModel):
    """Reviewable drafts returned before any approval or publication action."""

    drafts: list[EditableTextDraft]
    content_ids: list[str]
    content_id: str | None = None
    provider: str
    model: str
    review_state: Literal["pending_human_review"] = "pending_human_review"


class ReviewRequest(BaseModel):
    decision: Literal["approve", "request_regeneration"]
    reviewer_ref: str = Field(min_length=1)
    feedback: str | None = Field(default=None, min_length=1)


class RegenerateRequest(BaseModel):
    """Inputs needed to regenerate one draft after human feedback was recorded."""

    brief: GuidedBrief
    feedback: str = Field(min_length=1)
    formula: Literal["AIDA", "PAS", "4CS", "BAB", "4PS", "OPEN_LOOP"] | None = None
    rag_enabled: bool = False
    top_k: int = 3


class ManualEditRequest(BaseModel):
    caption: str = Field(min_length=1)
    cta: str | None = None


class ReviewStatusResponse(BaseModel):
    content_id: str
    state: Literal["generated_draft", "pending_human_review", "approved_final"]
    review: HumanReview | None = None


app = FastAPI(
    title="Generador de contenido API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3004",
        "http://127.0.0.1:3004",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
)

persistence_settings = EditorialPersistenceSettings.from_environment()
editorial_store = EditorialContentStore(persistence_settings.database_path)
editorial_plan_store = EditorialPlanStore(persistence_settings.database_path)


@app.get("/readiness", response_model=ReadinessResponse)
def readiness() -> ReadinessResponse:
    """Report local API readiness without contacting external providers."""

    return ReadinessResponse()


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    username: str
    expires_at: int


@app.post("/auth/login", response_model=LoginResponse)
def login(request: LoginRequest) -> LoginResponse:
    """Exchange the local credentials for a signed, expiring session token."""

    settings = AuthSettings.from_environment()
    if settings is None:
        raise HTTPException(status_code=503, detail="authentication is not configured")
    if not authenticate(settings, request.username, request.password):
        raise HTTPException(status_code=401, detail="invalid credentials")
    token, expires_at = issue_token(settings)
    return LoginResponse(access_token=token, username=settings.username, expires_at=expires_at)


@app.get("/auth/me")
def current_user(username: str = Depends(require_session)) -> dict[str, str]:
    return {"username": username}


@app.post("/drafts", response_model=DraftResponse, dependencies=[Depends(require_session)])
def create_drafts(request: DraftRequest) -> DraftResponse:
    """Generate editable drafts through the configured provider.

    The API owns provider credentials. The browser receives only reviewable
    draft data and never receives the configured API key.
    """

    try:
        generator = build_text_generator()
    except LlmConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    try:
        approach_override = (
            approach_for_formula(request.formula, request.brief)
            if request.formula
            else None
        )
        if request.rag_enabled:
            if not request.business_id:
                raise HTTPException(
                    status_code=422,
                    detail="business_id is required when rag_enabled=true",
                )
            if request.top_k <= 0:
                raise HTTPException(status_code=422, detail="top_k must be positive")
            try:
                index = LocalChromaIndex(RagLocalSettings())
                drafts = RagGroundedDraftService(index, generator).draft(
                    request.brief,
                    business_id=request.business_id,
                    top_k=request.top_k,
                    approach_override=approach_override,
                )
            except (ValueError, RuntimeError) as error:
                raise HTTPException(status_code=503, detail=str(error)) from error
        else:
            drafts = ChannelAdaptedDraftService(generator).draft(
                request.brief, approach_override=approach_override
            )
    except LlmConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    from apps.api.config import LlmSettings

    llm_settings = LlmSettings.from_environment()
    provider = llm_settings.provider
    model = ("deterministic-mock" if provider == "mock" else llm_settings.ollama_model if provider == "ollama" else llm_settings.groq_model)
    content_ids: list[str] = []
    for draft in drafts:
        content_id = editorial_store.create_id()
        content = EditorialReviewService.from_generated_draft(
            draft,
            content_id=content_id,
            brand_id=request.brand_id,
            business_id=request.business_id,
        )
        editorial_store.create(EditorialReviewService.submit_for_review(content))
        content_ids.append(content_id)
    return DraftResponse(
        drafts=drafts,
        content_ids=content_ids,
        content_id=content_ids[0] if len(content_ids) == 1 else None,
        provider=provider,
        model=model,
    )


def _get_editorial_content(content_id: str) -> EditorialContent:
    """Resolve a record ID; session authentication does not authorize a tenant.

    Routes apply the signed session dependency, but this MVP still has no
    per-business access control. Treat ``content_id`` as an identifier only.
    """
    content = editorial_store.get(content_id)
    if content is None:
        raise HTTPException(status_code=404, detail="content_id not found")
    return content


@app.get("/drafts/{content_id}", response_model=EditorialContent, dependencies=[Depends(require_session)])
def get_draft(content_id: str) -> EditorialContent:
    return _get_editorial_content(content_id)


@app.get("/drafts/{content_id}/review", response_model=ReviewStatusResponse, dependencies=[Depends(require_session)])
def get_review_status(content_id: str) -> ReviewStatusResponse:
    content = _get_editorial_content(content_id)
    return ReviewStatusResponse(
        content_id=content.content_id,
        state=content.state,
        review=content.review,
    )


@app.post("/drafts/{content_id}/review", response_model=EditorialContent, dependencies=[Depends(require_session)])
def record_review(content_id: str, request: ReviewRequest) -> EditorialContent:
    content = _get_editorial_content(content_id)
    if not request.reviewer_ref.strip():
        raise HTTPException(status_code=422, detail="reviewer_ref must contain text")
    try:
        if request.decision == "approve":
            updated = EditorialReviewService.approve(
                content, reviewer_ref=request.reviewer_ref
            )
        else:
            if request.feedback is None or not request.feedback.strip():
                raise HTTPException(
                    status_code=422,
                    detail="feedback must contain text when requesting regeneration",
                )
            updated = EditorialReviewService.record_feedback(
                content,
                feedback=request.feedback,
                reviewer_ref=request.reviewer_ref,
            )
    except EditorialTransitionError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return editorial_store.save(updated)


@app.post(
    "/drafts/{content_id}/regenerate",
    response_model=EditorialContent,
    dependencies=[Depends(require_session)],
)
def regenerate_draft(content_id: str, request: RegenerateRequest) -> EditorialContent:
    """Regenerate from the exact recorded feedback without approving the result."""

    content = _get_editorial_content(content_id)
    if not request.feedback.strip():
        raise HTTPException(status_code=422, detail="feedback must contain text")
    if request.top_k <= 0:
        raise HTTPException(status_code=422, detail="top_k must be positive")
    brief = request.brief.model_copy(update={"platforms": [content.draft.channel]})
    approach = (
        approach_for_formula(request.formula, brief)
        if request.formula
        else select_copy_approach(brief)
    )

    try:
        generator = build_text_generator()
    except LlmConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    def draft_factory(
        source: EditorialContent, _regeneration: RegenerationRequest
    ) -> EditableTextDraft:
        if request.rag_enabled:
            if not source.business_id:
                raise ValueError("business_id is required when rag_enabled=true")
            index = LocalChromaIndex(RagLocalSettings())
            return RagGroundedDraftService(index, generator).draft(
                brief,
                business_id=source.business_id,
                top_k=request.top_k,
                approach_override=approach,
                reviewer_feedback=request.feedback,
            )[0]
        return ChannelAdaptedDraftService(generator).draft(
            brief,
            approach_override=approach,
            reviewer_feedback=request.feedback,
        )[0]

    try:
        regenerated = EditorialReviewService.regenerate(
            content,
            RegenerationRequest(trigger="human_feedback", feedback=request.feedback),
            draft_factory=draft_factory,
        )
    except EditorialTransitionError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return editorial_store.create(regenerated)


@app.patch("/drafts/{content_id}", response_model=EditorialContent, dependencies=[Depends(require_session)])
def edit_draft(content_id: str, request: ManualEditRequest) -> EditorialContent:
    content = _get_editorial_content(content_id)
    try:
        updated = EditorialReviewService.manual_edit(
            content, caption=request.caption, cta=request.cta
        )
    except EditorialTransitionError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return editorial_store.save(updated)


class StoredEditorialPlan(BaseModel):
    """Validated plan plus its stable local identifier."""

    plan_id: str
    plan: EditorialPlan


class PlanItemDayRequest(BaseModel):
    day: date


@app.post("/plans", response_model=StoredEditorialPlan, dependencies=[Depends(require_session)])
def save_plan(plan: EditorialPlan) -> StoredEditorialPlan:
    """Persist an already validated plan for later calendar rendering."""

    plan_id = editorial_plan_store.create_id()
    editorial_plan_store.save(plan_id, plan)
    return StoredEditorialPlan(plan_id=plan_id, plan=plan)


@app.get("/plans/{plan_id}", response_model=StoredEditorialPlan, dependencies=[Depends(require_session)])
def get_plan(plan_id: str) -> StoredEditorialPlan:
    plan = editorial_plan_store.get(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="plan_id not found")
    return StoredEditorialPlan(plan_id=plan_id, plan=plan)


@app.get("/plans", response_model=list[StoredEditorialPlan], dependencies=[Depends(require_session)])
def list_plans() -> list[StoredEditorialPlan]:
    return [
        StoredEditorialPlan(plan_id=plan_id, plan=plan)
        for plan_id, plan in editorial_plan_store.list()
    ]


@app.patch(
    "/plans/{plan_id}/items/{item_index}/day",
    response_model=StoredEditorialPlan,
    dependencies=[Depends(require_session)],
)
def update_plan_item_day(
    plan_id: str,
    request: PlanItemDayRequest,
    item_index: int = Path(ge=0),
) -> StoredEditorialPlan:
    plan = editorial_plan_store.get(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="plan_id not found")
    try:
        updated = reschedule_item(plan, item_index, request.day)
    except IndexError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    editorial_plan_store.save(plan_id, updated)
    return StoredEditorialPlan(plan_id=plan_id, plan=updated)
