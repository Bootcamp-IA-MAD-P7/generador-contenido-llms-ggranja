import type { BriefForm, DraftEvidence } from "./types.ts";

export type ApiEditorialState = "generated_draft" | "pending_human_review" | "approved_final";
export type ReviewDecision = "approve" | "request_regeneration";
export type ApiDraft = {
  template_id: string;
  template_version: string;
  channel: "instagram" | "facebook";
  format: string;
  caption: string;
  cta?: string | null;
  evidence_provenance: DraftEvidence[];
  supported_claims: string[];
  unsupported_claims: string[];
  copy_approach?: string | null;
  copy_formula?: string | null;
  approach_rationale?: string | null;
};
export type ApiEditorialContent = {
  content_id: string;
  state: ApiEditorialState;
  draft: ApiDraft;
  brand_id?: string | null;
  business_id?: string | null;
  review?: { decision: ReviewDecision; reviewer_ref: string; feedback?: string | null } | null;
};
export type DraftApiResponse = {
  detail?: string;
  drafts?: ApiDraft[];
  content_ids?: string[];
  content_id?: string | null;
  review_state?: ApiEditorialState;
};

export class ReviewApiError extends Error {
  readonly status: number | null;
  constructor(message: string, status: number | null = null) {
    super(message);
    this.name = "ReviewApiError";
    this.status = status;
  }
}

export function apiBaseUrl(): string {
  return (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
}

export function mapBriefToApi(brief: BriefForm, businessContextRef: string) {
  return {
    topic_or_offer: brief.campaign.trim(), objective: brief.objective.trim(), audience_context: brief.audience.trim(),
    business_context_refs: [businessContextRef], platforms: [brief.platform.toLowerCase()],
    format: brief.format === "Reel" ? "reel" : brief.format === "Carrusel" ? "carousel" : "single_image",
    brand_and_constraints: brief.restrictions.trim() || undefined, notes: "Generated from Content Studio.", facts: [],
  };
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl()}${path}`, { ...init, signal: init.signal ?? AbortSignal.timeout(10000) });
  } catch (error) {
    throw new ReviewApiError(error instanceof Error && error.name === "TimeoutError" ? "La API agotó el tiempo de espera." : "No se pudo conectar con la API.");
  }
  let payload: unknown = null;
  try { payload = await response.json(); } catch { /* HTTP errors may have no JSON body. */ }
  if (!response.ok) {
    const detail = payload && typeof payload === "object" && typeof (payload as { detail?: unknown }).detail === "string"
      ? (payload as { detail: string }).detail : `La API respondió con estado ${response.status}.`;
    const prefix = response.status === 404 ? "Borrador inexistente. " : response.status === 409 ? "Transición editorial inválida. "
      : response.status === 422 ? "Entrada inválida. " : response.status === 503 ? "Servicio o proveedor no disponible. " : "";
    throw new ReviewApiError(prefix + detail, response.status);
  }
  return payload as T;
}

export function createDraft(body: { brief: ReturnType<typeof mapBriefToApi>; brandId?: string; businessId?: string; ragEnabled: boolean }) {
  return request<DraftApiResponse>("/drafts", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({
    brief: body.brief, rag_enabled: body.ragEnabled, ...(body.brandId ? { brand_id: body.brandId } : {}),
    ...(body.businessId ? { business_id: body.businessId, top_k: 3 } : {}),
  }) });
}
export function getDraft(contentId: string) { return request<ApiEditorialContent>(`/drafts/${encodeURIComponent(contentId)}`); }
export function getReview(contentId: string) { return request<{ content_id: string; state: ApiEditorialState; review: ApiEditorialContent["review"] }>(`/drafts/${encodeURIComponent(contentId)}/review`); }
export function updateDraft(contentId: string, caption: string) { return request<ApiEditorialContent>(`/drafts/${encodeURIComponent(contentId)}`, {
  method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ caption }),
}); }
export function reviewDraft(contentId: string, decision: ReviewDecision, reviewerRef: string, feedback?: string) { return request<ApiEditorialContent>(`/drafts/${encodeURIComponent(contentId)}/review`, {
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ decision, reviewer_ref: reviewerRef, ...(feedback !== undefined ? { feedback } : {}) }),
}); }
