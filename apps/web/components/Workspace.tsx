"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type {
  BrandId,
  BriefForm,
  CommerceId,
  CopyApproachInfo,
  DraftPreparationStatus,
  HistoryEntry,
  LocalDraft,
  DraftEvidence,
  ViewId,
} from "../domain/types.ts";
import { canStartGeneration, parseCopyApproach, parseDraftResponse, type GenerationState } from "../domain/draft-generation.ts";
import { createDraft, getDraft, reviewDraft, updateDraft, mapBriefToApi, type ApiEditorialContent } from "../domain/review-api.ts";
import { savePlan, type EditorialPlan } from "../domain/plans-api.ts";
import { brandContexts, dashboardFixtures, draftFixtures, getBriefDefaults, historyFixtures } from "../domain/fixtures.ts";
import {
  afterBriefChange,
  afterTextChange,
  approve,
  missingBriefFields,
  requestChanges,
  resubmit,
  missingReviewer,
  statusFromDraft,
} from "../domain/editorial.ts";
import { AppShell } from "./shell/AppShell";
import { BrandSwitcher } from "./shell/BrandSwitcher";
import { Dashboard } from "./dashboard/Dashboard";
import { DraftsView } from "./drafts/DraftsView";
import { HistoryView } from "./history/HistoryView";
import { ContentStudio } from "./studio/ContentStudio";
import { CalendarView } from "./calendar/CalendarView";
import { PlaceholderView } from "./ui/PlaceholderView";

type DraftApiResponse = { detail?: string; drafts?: Array<{ caption?: string; evidence_provenance?: unknown; supported_claims?: unknown; unsupported_claims?: unknown }>; review_state?: "pending_human_review" };

const viewTitles: Record<ViewId, string> = {
  dashboard: "Dashboard",
  "content-studio": "Content Studio",
  drafts: "Borradores",
  history: "Historial",
  calendar: "Calendar",
  library: "Library",
  analytics: "Analytics",
  brands: "Brands & Stores",
  settings: "Settings",
};

const placeholders: Partial<Record<ViewId, string>> = {
  library: "Biblioteca de contenidos y materiales de la marca.",
  analytics: "Rendimiento real de las publicaciones. Requiere cuentas conectadas, que no existen en el MVP.",
  brands: "Gestión de marcas, comercios asociados y perfiles sociales.",
  settings: "Configuración de la plataforma y de cada marca, incluidos sus materiales y fuentes.",
};

export function Workspace() {
  const [view, setView] = useState<ViewId>("dashboard");
  const [brandId, setBrandId] = useState<BrandId>("panaderia");
  const [commerceId, setCommerceId] = useState<CommerceId | null>(null);

  const brand = useMemo(
    () => brandContexts.find((context) => context.id === brandId) ?? brandContexts[0],
    [brandId],
  );
  const activeCommerce = useMemo(
    () => brand.commerceOptions?.find((commerce) => commerce.id === commerceId),
    [brand, commerceId],
  );
  const activeContext = activeCommerce ?? brand;
  const theme = activeCommerce?.theme ?? brand.theme;
  const dashboard = dashboardFixtures[activeContext.account] ?? dashboardFixtures.talenthive;
  const contextName = activeCommerce ? brand.name + " · " + activeCommerce.name : brand.name;
  const [sessionDraftsByContext, setSessionDraftsByContext] = useState<Record<string, LocalDraft[]>>({});
  const [sessionHistoryByContext, setSessionHistoryByContext] = useState<Record<string, HistoryEntry[]>>({});
  const [activeSessionDraftId, setActiveSessionDraftId] = useState<string | null>(null);
  const sessionDraftSequence = useRef(0);
  const sessionHistorySequence = useRef(0);
  const drafts = [
    ...(sessionDraftsByContext[activeContext.account] ?? []),
    ...(draftFixtures[activeContext.account] ?? []),
  ];
  const historyEntries = [
    ...(sessionHistoryByContext[activeContext.account] ?? []),
    ...(historyFixtures[activeContext.account] ?? []),
  ];
  const dashboardWithSessionState = {
    ...dashboard,
    drafts: dashboard.drafts + drafts.filter((draft) => draft.id.startsWith("session-") && draft.status === "draft").length,
    review: dashboard.review + drafts.filter((draft) => draft.id.startsWith("session-") && draft.status === "review").length,
    approved: dashboard.approved + drafts.filter((draft) => draft.id.startsWith("session-") && draft.status === "approved").length,
  };

  const [brief, setBrief] = useState<BriefForm>(() => getBriefDefaults(activeContext.account));
  const [previewCopy, setPreviewCopy] = useState("");
  const [status, setStatus] = useState<DraftPreparationStatus>("not-prepared");
  const [validationMessage, setValidationMessage] = useState("");
  const [generationState, setGenerationState] = useState<GenerationState>("idle");
  const [previewEvidence, setPreviewEvidence] = useState<DraftEvidence[]>([]);
  const [supportedClaims, setSupportedClaims] = useState<string[]>([]);
  const [unsupportedClaims, setUnsupportedClaims] = useState<string[]>([]);
  const [copyApproach, setCopyApproach] = useState<CopyApproachInfo | null>(null);
  const [reviewerName, setReviewerName] = useState("");
  const [reviewMessage, setReviewMessage] = useState("");
  const [reviewFeedback, setReviewFeedback] = useState("");
  const [planSaveMessage, setPlanSaveMessage] = useState("");
  const [activeBackendId, setActiveBackendId] = useState<string | null>(null);
  const requestSequence = useRef(0);

  useEffect(() => {
    setBrief(getBriefDefaults(activeContext.account));
    setPreviewCopy("");
    setStatus("not-prepared");
    setValidationMessage("");
    setGenerationState("idle");
    setPreviewEvidence([]);
    setSupportedClaims([]);
    setUnsupportedClaims([]);
    setCopyApproach(null);
    setReviewerName("");
    setReviewMessage("");
    setReviewFeedback("");
    setPlanSaveMessage("");
    setActiveBackendId(null);
    setActiveSessionDraftId(null);
    requestSequence.current += 1;
  }, [activeContext.account, contextName]);

  function updateBrief(field: keyof BriefForm, value: string) {
    const nextBrief = { ...brief, [field]: value };
    setBrief(nextBrief);
    setStatus(afterBriefChange);
    updateSessionDraft({ brief: nextBrief, title: nextBrief.campaign.trim() || nextBrief.objective.trim(), status: "draft" });
    setValidationMessage("");
  }

  function updateSessionDraft(patch: Partial<LocalDraft>) {
    if (!activeSessionDraftId) return;
    setSessionDraftsByContext((current) => ({
      ...current,
      [activeContext.account]: (current[activeContext.account] ?? []).map((draft) =>
        draft.id === activeSessionDraftId ? { ...draft, ...patch } : draft,
      ),
    }));
  }

  function recordSessionHistory(draftId: string, eventStatus: HistoryEntry["status"], text: string) {
    if (!draftId.startsWith("session-")) return;
    const entry: HistoryEntry = {
      id: `session-history-${activeContext.account}-${++sessionHistorySequence.current}`,
      text,
      time: "Ahora",
      status: eventStatus,
      draftId,
      source: "session",
    };
    setSessionHistoryByContext((current) => ({
      ...current,
      [activeContext.account]: [entry, ...(current[activeContext.account] ?? [])],
    }));
  }

  function updateCopy(value: string) {
    setPreviewCopy(value);
    if (activeBackendId) {
      updateSessionDraft({ copy: value });
      return;
    }
    setStatus(afterTextChange);
    const nextStatus = status === "approved" ? "draft" : status === "pending-review" ? "review" : undefined;
    updateSessionDraft({ copy: value, ...(nextStatus ? { status: nextStatus } : {}) });
  }

  async function approveCurrentDraft() {
    if (activeBackendId) {
      if (missingReviewer(reviewerName)) { setReviewMessage("Indica quién revisa el borrador antes de aprobarlo."); return; }
      const requestVersion = ++requestSequence.current;
      try {
        const content = await reviewDraft(activeBackendId, "approve", reviewerName.trim());
        if (requestVersion !== requestSequence.current) return;
        applyBackendContent(content);
        setReviewMessage("");
      } catch (error) { setReviewMessage(error instanceof Error ? error.message : "No se pudo aprobar el borrador."); }
      return;
    }
    if (missingReviewer(reviewerName)) {
      setReviewMessage("Indica quién revisa el borrador antes de aprobarlo.");
      return;
    }
    const nextStatus = approve(status, reviewerName);
    if (nextStatus === status) return;
    setStatus(nextStatus);
    updateSessionDraft({ status: "approved", reviewer: reviewerName.trim() });
    setReviewMessage("");
    if (activeSessionDraftId) recordSessionHistory(activeSessionDraftId, "approved", "El borrador fue aprobado en esta sesión.");
  }

  async function requestCurrentChanges() {
    if (activeBackendId) {
      if (missingReviewer(reviewerName)) { setReviewMessage("Indica quién revisa el borrador antes de solicitar cambios."); return; }
      if (!reviewFeedback.trim()) { setReviewMessage("Indica el feedback para solicitar cambios."); return; }
      const requestVersion = ++requestSequence.current;
      try {
        const content = await reviewDraft(activeBackendId, "request_regeneration", reviewerName.trim(), reviewFeedback.trim());
        if (requestVersion !== requestSequence.current) return;
        applyBackendContent(content);
        setReviewMessage("");
      } catch (error) { setReviewMessage(error instanceof Error ? error.message : "No se pudo registrar el feedback."); }
      return;
    }
    if (missingReviewer(reviewerName)) {
      setReviewMessage("Indica quién revisa el borrador antes de solicitar cambios.");
      return;
    }
    const nextStatus = requestChanges(status, reviewerName);
    if (nextStatus === status) return;
    setStatus(nextStatus);
    updateSessionDraft({ status: "draft" });
    setReviewMessage("");
    if (activeSessionDraftId) recordSessionHistory(activeSessionDraftId, "changes-requested", "Se solicitaron cambios para este borrador.");
  }

  function resubmitCurrentDraft() {
    if (activeBackendId) { setReviewMessage("La API registra la solicitud de cambios; no genera contenido automáticamente."); return; }
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
    setStatus(content.state === "approved_final" ? "approved" : "pending-review");
    setReviewFeedback(content.review?.feedback ?? "");
    updateSessionDraft({ copy: content.draft.caption, status: content.state === "approved_final" ? "approved" : "review", reviewer: content.review?.reviewer_ref });
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
    setReviewerName("");
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
      const payload = await createDraft({ brief: mapBriefToApi({ ...brief, restrictions: brief.restrictions.trim() || activeContext.summary }, activeContext.account), brandId: brand.id, businessId: ragBusinessId, ragEnabled: Boolean(ragBusinessId) });
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
    setBrief(draft.brief);
    setPreviewCopy(draft.copy);
    setPreviewEvidence(draft.evidenceProvenance ?? []);
    setSupportedClaims(draft.supportedClaims ?? []);
    setUnsupportedClaims(draft.unsupportedClaims ?? []);
    setCopyApproach(draft.copyApproach ?? null);
    setReviewerName(draft.reviewer ?? "");
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
          contextName={contextName}
          handle={activeContext.account}
          theme={theme}
          drafts={drafts}
          onOpenDraft={openDraft}
        />
      )}
      {view === "history" && (
        <HistoryView
          contextName={contextName}
          entries={historyEntries}
          drafts={drafts}
          onOpenDraft={openDraft}
        />
      )}
      {view === "content-studio" && (
        <ContentStudio
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
          reviewerName={reviewerName}
          reviewMessage={reviewMessage}
           reviewFeedback={reviewFeedback}
           onReviewFeedbackChange={(value) => { setReviewFeedback(value); setReviewMessage(""); }}
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
      {view === "calendar" && <CalendarView />}
      {placeholders[view] && <PlaceholderView title={viewTitles[view]} description={placeholders[view]!} />}
    </AppShell>
  );
}
