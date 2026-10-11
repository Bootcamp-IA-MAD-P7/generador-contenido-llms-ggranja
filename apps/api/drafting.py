"""Channel-adapted editable text drafting service."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from pydantic import BaseModel, Field

from apps.api.copy_formulas import CopyApproach, approach_prompt_block, select_copy_approach
from apps.api.llm import TextGenerator
from apps.api.models import GuidedBrief, Platform
from apps.api.rag import LocalChromaIndex, RetrievedBusinessContext, ground_claim


@dataclass(frozen=True)
class TextTemplate:
    template_id: str
    version: str
    channel: Platform
    instructions: str


TEMPLATES: dict[Platform, TextTemplate] = {
    "instagram": TextTemplate(
        template_id="social.instagram.text-draft",
        version="1.0.0",
        channel="instagram",
        instructions=(
            "Use a concise hook, scannable caption, direct credible CTA and "
            "functional keywords only when grounded. Keep the draft concise, "
            "in Spanish by default or Catalan when configured; preserve source "
            "grounding and never invent prices, opening hours, promotions or dates."
        ),
    ),
    "facebook": TextTemplate(
        template_id="social.facebook.text-draft",
        version="1.0.0",
        channel="facebook",
        instructions=(
            "Use a conversational opening, enough context for the feed, a "
            "readable structure and a direct credible CTA. Keep it concise, "
            "in Spanish by default or Catalan when configured; preserve source "
            "grounding and never invent prices, opening hours, promotions or dates."
        ),
    ),
}


class EditableTextDraft(BaseModel):
    """Reviewable text output for one selected channel."""

    template_id: str
    template_version: str
    channel: Platform
    format: str
    caption: str = Field(min_length=1)
    cta: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    review_notes: list[str] = Field(default_factory=list)
    evidence_provenance: list[dict[str, object]] = Field(default_factory=list)
    supported_claims: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    copy_approach: str | None = None
    copy_formula: str | None = None
    approach_rationale: str | None = None


class ChannelAdaptedDraftService:
    """Select a versioned channel template and request one editable draft."""

    def __init__(self, generator: TextGenerator) -> None:
        self._generator = generator

    def draft(
        self,
        brief: GuidedBrief,
        *,
        retrieved_contexts: Sequence[RetrievedBusinessContext] = (),
        business_id: str | None = None,
        grounding_enabled: bool = False,
        approach_override: tuple[CopyApproach, str] | None = None,
        reviewer_feedback: str | None = None,
    ) -> list[EditableTextDraft]:
        """Return one grounded, editable text draft for every selected channel."""

        contexts = tuple(retrieved_contexts)
        if business_id is not None and any(
            context.business_id != business_id for context in contexts
        ):
            raise ValueError("retrieved context must match the requested business_id")
        return [
            self._draft_for_channel(
                brief,
                channel,
                contexts,
                grounding_enabled,
                approach_override,
                reviewer_feedback,
            )
            for channel in brief.platforms
        ]

    def _draft_for_channel(
        self,
        brief: GuidedBrief,
        channel: Platform,
        retrieved_contexts: Sequence[RetrievedBusinessContext] = (),
        grounding_enabled: bool = False,
        approach_override: tuple[CopyApproach, str] | None = None,
        reviewer_feedback: str | None = None,
    ) -> EditableTextDraft:
        template = TEMPLATES[channel]
        supported_claims, unsupported_claims = _ground_brief_claims(
            brief, retrieved_contexts, grounding_enabled
        )
        selection = approach_override or select_copy_approach(brief)
        prompt = self._build_prompt(
            brief,
            template,
            approach=selection[0] if selection else None,
            reviewer_feedback=reviewer_feedback,
            retrieved_contexts=retrieved_contexts,
            supported_claims=supported_claims,
            unsupported_claims=unsupported_claims,
            grounding_enabled=grounding_enabled,
        )
        generated_text = self._generator.generate(prompt).strip()
        if not generated_text:
            raise ValueError("text generator returned an empty draft")

        evidence_refs = (
            [context.text for context in retrieved_contexts]
            if grounding_enabled
            else [fact.statement for fact in brief.facts if fact.status == "CONFIRMED"]
        )
        assumptions = [
            fact.statement
            for fact in brief.facts
            if fact.status in {"INFERRED", "UNKNOWN"}
        ]
        review_notes = [
            "Review all inferred or unknown facts before approval.",
            "This draft is not a publication request.",
        ]
        if unsupported_claims:
            review_notes.append("Unsupported claims must not be presented as retrieved facts.")

        return EditableTextDraft(
            template_id=template.template_id,
            template_version=template.version,
            channel=channel,
            format=brief.format,
            caption=generated_text,
            evidence_refs=evidence_refs,
            assumptions=assumptions,
            review_notes=review_notes,
            evidence_provenance=[_provenance_dict(context) for context in retrieved_contexts],
            supported_claims=supported_claims,
            unsupported_claims=unsupported_claims,
            copy_approach=selection[0].label if selection else None,
            copy_formula=selection[0].formula if selection else None,
            approach_rationale=selection[1] if selection else None,
        )

    @staticmethod
    def _build_prompt(
        brief: GuidedBrief,
        template: TextTemplate,
        *,
        retrieved_contexts: Sequence[RetrievedBusinessContext] = (),
        supported_claims: Sequence[str] = (),
        unsupported_claims: Sequence[str] = (),
        grounding_enabled: bool = False,
        approach: CopyApproach | None = None,
        reviewer_feedback: str | None = None,
    ) -> str:
        approach_block = f"{approach_prompt_block(approach)}\n" if approach else ""
        if reviewer_feedback and reviewer_feedback.strip():
            approach_block += (
                "Reviewer feedback to apply as editing guidance only; it never authorizes "
                f"new facts or claims: {reviewer_feedback}\n"
            )
        facts = "\n".join(
            f"- [{fact.status}] {fact.statement} (source: {fact.source}; "
            f"scope: {fact.scope})"
            for fact in brief.facts
        ) or "- No business facts supplied."

        retrieval = "\n".join(
            "- "
            f"[{context.source_type}] {context.text} "
            f"(source_id: {context.source_id}; version: {context.source_version}; "
            f"chunk_id: {context.chunk_id}; business_id: {context.business_id}; "
            f"source_file: {context.source_file or 'n/a'}; "
            f"page_number: {context.page_number or 'n/a'}; "
            f"source_uri: {context.source_uri or 'n/a'})"
            for context in retrieved_contexts
        ) or "- No retrieved business evidence."
        grounded_claims = "\n".join(f"- SUPPORTED: {claim}" for claim in supported_claims)
        rejected_claims = "\n".join(
            f"- UNSUPPORTED: {claim}" for claim in unsupported_claims
        ) or "- None"
        if not grounding_enabled:
            evidence_block = "Facts and evidence status:\n" + facts
        else:
            evidence_block = (
                "Retrieved evidence (the only business evidence allowed in this draft):\n"
 …10979 tokens truncated….current) return;
        applyBackendContent(recorded);
        const regenerated = await regenerateDraft(activeBackendId, {
          brief: apiBrief,
          feedback: reviewFeedback,
          ...(formulaCode !== "AUTO" ? { formula: formulaCode } : {}),
          businessId: ragBusinessId,
          ragEnabled: Boolean(ragBusinessId),
        });
        if (requestVersion !== requestSequence.current) return;
        applyBackendContent(regenerated);
        setStatus("pending-review");
        setGenerationState("success");
        setReviewFeedback("");
        setReviewMessage("");
        if (activeSessionDraftId) recordSessionHistory(activeSessionDraftId, "review", "Se generó una nueva versión con el feedback indicado; queda pendiente de revisión humana.");
      } catch (error) {
        if (requestVersion === requestSequence.current) {
          setGenerationState("error");
          setReviewMessage(error instanceof Error ? error.message : "No se pudo regenerar el borrador.");
        }
      }
      return;
    }
    if (missingReviewer(reviewerName)) {
      setReviewMessage("Indica quién revisa el borrador antes de devolverlo a revisión.");
      return;
    }
    const nextStatus = resubmit(status, reviewerName);
    if (nextStatus === status) return;
    setStatus(nextStatus);
    updateSessionDraft({ status: "review" });
    setReviewMessage("");
    if (activeSessionDraftId) recordSessionHistory(activeSessionDraftId, "review", "El borrador volvió a revisión humana.");
  }

  function applyBackendContent(content: ApiEditorialContent) {
    setActiveBackendId(content.content_id);
    setPreviewCopy(content.draft.caption);
    setPreviewEvidence(content.draft.evidence_provenance ?? []);
    setSupportedClaims(content.draft.supported_claims ?? []);
    setUnsupportedClaims(content.draft.unsupported_claims ?? []);
    setCopyApproach(parseCopyApproach(content.draft));
    setStatus(content.state === "approved_final" ? "approved" : content.review?.decision === "request_regeneration" ? "changes-requested" : "pending-review");
    setReviewFeedback(content.review?.feedback ?? "");
    updateSessionDraft({ backendId: content.content_id, copy: content.draft.caption, status: content.state === "approved_final" ? "approved" : content.review?.decision === "request_regeneration" ? "draft" : "review", reviewer: content.review?.reviewer_ref });
  }

  function buildValidatedPlan(): EditorialPlan | null {
    if (!activeBackendId || status === "not-prepared") return null;
    const format = brief.format === "Reel" ? "reel" : brief.format === "Carrusel" ? "carousel" : "single_image";
    const platform = brief.platform.toLowerCase() === "facebook" ? "facebook" : "instagram";
    const today = new Date().toISOString().slice(0, 10);
    return {
      strategy_id: "eighty_twenty",
      strategy_version: "1.0.0",
      total_slots: 1,
      starts_on: today,
      ends_on: today,
      targets: { VALUE: 1 },
      items: [{
        source_ref: activeBackendId,
        source_kind: "editorial_content",
        strategy_version: "1.0.0",
        bucket_key: "VALUE",
        platform,
        format,
        scheduled_on: today,
        review_state: status === "approved" ? "approved_final" : "pending_human_review",
        evidence: {},
      }],
    };
  }

  async function saveValidatedPlan() {
    const plan = buildValidatedPlan();
    if (!plan) {
      setPlanSaveMessage("Prepara primero un borrador validado.");
      return;
    }
    try {
      const stored = await savePlan(plan);
      setPlanSaveMessage(`Plan guardado: ${stored.plan_id.slice(0, 8)}. Ya está disponible en Calendario.`);
    } catch (error) {
      setPlanSaveMessage(error instanceof Error ? error.message : "No se pudo guardar el plan.");
    }
  }
  async function saveCurrentEdit() {
    if (!activeBackendId || status === "approved") return;
    const requestVersion = ++requestSequence.current;
    try { const content = await updateDraft(activeBackendId, previewCopy.trim()); if (requestVersion !== requestSequence.current) return; applyBackendContent(content); setValidationMessage(""); }
    catch (error) { setValidationMessage(error instanceof Error ? error.message : "No se pudo guardar la edición."); }
  }

  async function prepareDraft() {
    if (!canStartGeneration(generationState)) return;
    if (missingBriefFields(brief)) {
      setValidationMessage("Completa el objetivo, la audiencia y la campaña para preparar el borrador.");
      return;
    }
    setGenerationState("loading");
    setValidationMessage("");
    setReviewerName(sessionReviewer);
    setReviewMessage("");
    setPreviewEvidence([]);
    setSupportedClaims([]);
    setUnsupportedClaims([]);
    setCopyApproach(null);
    const apiBaseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
    const format = brief.format === "Reel" ? "reel" : brief.format === "Carrusel" ? "carousel" : "single_image";
    const ragBusinessId = brand.id === "coll-amunt" ? activeCommerce?.businessId : undefined;
    const requestVersion = ++requestSequence.current;

    try {
      {
      const payload = await createDraft({ brief: mapBriefToApi({ ...brief, restrictions: brief.restrictions.trim() || activeContext.summary }, activeContext.account), brandId: brand.id, businessId: ragBusinessId, ragEnabled: Boolean(ragBusinessId), ...(formulaCode !== "AUTO" ? { formula: formulaCode } : {}) });
      if (requestVersion !== requestSequence.current) return;
      const parsed = await parseDraftResponse({ ok: true, status: 200, json: async () => payload }, ragBusinessId);
      const parsedDrafts = await Promise.all(payload.drafts!.map((_, index) => parseDraftResponse({ ok: true, status: 200, json: async () => ({ ...payload, drafts: [payload.drafts?.[index]], content_ids: [payload.content_ids?.[index]] }) }, ragBusinessId)));
      if (payload.review_state !== "pending_human_review" || !payload.drafts?.length || !payload.content_ids?.length) throw new Error("La API no confirmó los borradores pendientes de revisión humana.");
      if (payload.content_ids.length !== payload.drafts.length) throw new Error("La API no devolvió identificadores para todos los borradores.");
      const sessionDraft: LocalDraft = {
        id: `session-${activeContext.account}-${++sessionDraftSequence.current}`,
        backendId: parsed.contentIds[0], title: brief.campaign.trim() || brief.objective.trim(), platform: brief.platform,
        format: brief.format, status: "review", updatedAt: "Ahora · sesión actual", brief, copy: parsed.copy,
        evidenceProvenance: parsed.evidenceProvenance, supportedClaims: parsed.supportedClaims, unsupportedClaims: parsed.unsupportedClaims, copyApproach: parsed.copyApproach,
      };
      const associatedDrafts = parsedDrafts.map((draft, index) => index === 0 ? sessionDraft : ({ ...sessionDraft, id: `session-${activeContext.account}-${++sessionDraftSequence.current}`, backendId: draft.contentIds[0], copy: draft.copy, evidenceProvenance: draft.evidenceProvenance, supportedClaims: draft.supportedClaims, unsupportedClaims: draft.unsupportedClaims, copyApproach: draft.copyApproach }));
      setSessionDraftsByContext((current) => ({ ...current, [activeContext.account]: [...associatedDrafts, ...(current[activeContext.account] ?? [])] }));
      setActiveSessionDraftId(sessionDraft.id); setActiveBackendId(parsed.contentIds[0]);
      setPreviewCopy(parsed.copy); setPreviewEvidence(parsed.evidenceProvenance); setSupportedClaims(parsed.supportedClaims); setUnsupportedClaims(parsed.unsupportedClaims); setCopyApproach(parsed.copyApproach);
      setStatus("pending-review"); setGenerationState("success");
      recordSessionHistory(sessionDraft.id, "review", "Se preparó el borrador con la API y quedó pendiente de revisión humana.");
      return;
      }

      const response = await fetch(`${apiBaseUrl}/drafts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          brief: {
            topic_or_offer: brief.campaign.trim(),
            objective: brief.objective.trim(),
            audience_context: brief.audience.trim(),
            business_context_refs: [activeContext.account],
            platforms: [brief.platform.toLowerCase()],
            format,
            brand_and_constraints: brief.restrictions.trim() || activeContext.summary,
            notes: "Generated from Content Studio local workspace.",
            facts: [],
          },
          rag_enabled: Boolean(ragBusinessId),
          ...(ragBusinessId ? { business_id: ragBusinessId, top_k: 3 } : {}),
        }),
      });
      const payload = (await response.json()) as DraftApiResponse;
      const parsed = await parseDraftResponse(
        { ok: response.ok, status: response.status, json: async () => payload },
        ragBusinessId,
      );
      if (!response.ok) {
        throw new Error(payload.detail || `La API respondió con estado ${response.status}.`);
      }
      if (payload.review_state !== "pending_human_review") {
        throw new Error("La API no confirm\u00f3 que el borrador quede pendiente de revisi\u00f3n humana.");
      }
      const copy = parsed.copy;
      if (!copy) throw new Error("La API no devolvió un borrador editable.");

      const sessionDraft: LocalDraft = {
        id: `session-${activeContext.account}-${++sessionDraftSequence.current}`,
        title: brief.campaign.trim() || brief.objective.trim(),
        platform: brief.platform,
        format: brief.format,
        status: "review",
        updatedAt: "Ahora · sesión actual",
        brief,
        copy,
        evidenceProvenance: parsed.evidenceProvenance,
        supportedClaims: parsed.supportedClaims,
        unsupportedClaims: parsed.unsupportedClaims,
      };
      setSessionDraftsByContext((current) => ({
        ...current,
        [activeContext.account]: [sessionDraft, ...(current[activeContext.account] ?? [])],
      }));
      setActiveSessionDraftId(sessionDraft.id);
      setPreviewCopy(copy);
      setPreviewEvidence(parsed.evidenceProvenance);
      setSupportedClaims(parsed.supportedClaims);
      setUnsupportedClaims(parsed.unsupportedClaims);
      setStatus("pending-review");
      setGenerationState("success");
      recordSessionHistory(sessionDraft.id, "review", "Se preparó el borrador con la API y quedó pendiente de revisión humana.");
    } catch (error) {
      setGenerationState("error");
      setValidationMessage(error instanceof Error ? error.message : "No se pudo conectar con la API de generación.");
    }
  }

  async function openDraft(draft: LocalDraft) {
    setFormulaCode("AUTO");
    setBrief(draft.brief);
    setPreviewCopy(draft.copy);
    setPreviewEvidence(draft.evidenceProvenance ?? []);
    setSupportedClaims(draft.supportedClaims ?? []);
    setUnsupportedClaims(draft.unsupportedClaims ?? []);
    setCopyApproach(draft.copyApproach ?? null);
    setReviewerName(draft.reviewer ?? sessionReviewer);
    setReviewFeedback("");
    setReviewMessage("");
    setStatus(statusFromDraft(draft.status));
    setActiveSessionDraftId(draft.id.startsWith("session-") ? draft.id : null);
    setActiveBackendId(draft.backendId ?? null);
    setValidationMessage("");
    setView("content-studio");
    if (draft.backendId) {
      const requestVersion = ++requestSequence.current;
      try {
        const content = await getDraft(draft.backendId);
        if (requestVersion === requestSequence.current) applyBackendContent(content);
      } catch (error) {
        if (requestVersion === requestSequence.current) setValidationMessage(error instanceof Error ? error.message : "No se pudo recuperar el borrador.");
      }
    }
  }

  function selectBrand(nextBrandId: BrandId) {
    const next = brandContexts.find((context) => context.id === nextBrandId);
    if (!next) return;
    setBrandId(next.id);
    setCommerceId(next.commerceOptions?.[0]?.id ?? null);
  }

  function selectCommerce(nextCommerceId: CommerceId) {
    if (brand.commerceOptions?.some((commerce) => commerce.id === nextCommerceId)) {
      setCommerceId(nextCommerceId);
    }
  }

  const trail = [brand.name, ...(activeCommerce ? [activeCommerce.name] : []), viewTitles[view]];

  return (
    <AppShell
      view={view}
      onNavigate={setView}
      draftCount={drafts.length}
      theme={theme}
      trail={trail}
      switcher={
        <BrandSwitcher
          brands={brandContexts}
          brand={brand}
          commerceId={commerceId}
          onSelectBrand={selectBrand}
          onSelectCommerce={selectCommerce}
        />
      }
    >
      {view === "dashboard" && (
        <Dashboard
          welcomeName={welcomeName}
          contextName={contextName}
          kind={activeCommerce ? activeCommerce.sector : brand.kind}
          summary={activeContext.summary}
          handle={activeContext.account}
          theme={theme}
          fixture={dashboardWithSessionState}
          onCreate={() => setView("content-studio")}
        />
      )}
      {view === "drafts" && (
        <DraftsView
          welcomeName={welcomeName}
          contextName={contextName}
          handle={activeContext.account}
          theme={theme}
          drafts={drafts}
          onOpenDraft={openDraft}
        />
      )}
      {view === "history" && (
        <HistoryView
          welcomeName={welcomeName}
          contextName={contextName}
          entries={historyEntries}
          drafts={drafts}
          onOpenDraft={openDraft}
        />
      )}
      {view === "content-studio" && (
        <ContentStudio
          welcomeName={welcomeName}
          contextName={contextName}
          contextSummary={activeContext.summary}
          contextSector={activeCommerce?.sector}
          handle={activeContext.account}
          theme={theme}
          brief={brief}
          previewCopy={previewCopy}
          status={status}
          validationMessage={validationMessage}
          generationState={generationState}
          evidenceProvenance={previewEvidence}
          supportedClaims={supportedClaims}
          unsupportedClaims={unsupportedClaims}
          copyApproach={copyApproach}
          formulaCode={formulaCode}
          hasConfirmedFacts={false}
          isRegenerating={generationState === "loading"}
          reviewerName={reviewerName}
          reviewMessage={reviewMessage}
           reviewFeedback={reviewFeedback}
           onReviewFeedbackChange={(value) => { setReviewFeedback(value); setReviewMessage(""); }}
          onFormulaChange={setFormulaCode}
          onReviewerChange={(value) => { setReviewerName(value); setReviewMessage(""); }}
          onBriefChange={updateBrief}
          onCopyChange={updateCopy}
           onCopyBlur={saveCurrentEdit}
          onPrepare={prepareDraft}
          isPreparing={generationState === "loading"}
          onApprove={approveCurrentDraft}
          onRequestChanges={requestCurrentChanges}
          onResubmit={resubmitCurrentDraft}
          canSavePlan={Boolean(activeBackendId)}
          planSaveMessage={planSaveMessage}
          onSavePlan={saveValidatedPlan}
        />
      )}
      {view === "calendar" && <CalendarView welcomeName={welcomeName} />}
      {placeholders[view] && <PlaceholderView title={viewTitles[view]} description={placeholders[view]!} />}
    </AppShell>
  );
}
