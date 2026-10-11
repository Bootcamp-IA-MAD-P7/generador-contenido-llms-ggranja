import type { BrandTheme, BriefForm, CopyApproachInfo, DraftEvidence, DraftPreparationStatus } from "../../domain/types.ts";
import { generationStateLabels, type GenerationState } from "../../domain/draft-generation.ts";
import { statusCopy } from "../../domain/editorial.ts";
import { Kicker, SyntheticNotice } from "../ui/Kicker";
import { EditorialProgress, StudioStatus } from "../ui/EditorialStatus";
import { BriefEditor } from "./BriefEditor";
import { ContentPreview } from "./ContentPreview";
import { ReviewActions } from "./ReviewActions";
import type { FormulaCode } from "../../domain/review-api.ts";
import styles from "./studio.module.css";

export function ContentStudio({
  welcomeName,
  contextName,
  contextSummary,
  contextSector,
  handle,
  theme,
  brief,
  previewCopy,
  status,
  validationMessage,
  generationState,
  evidenceProvenance,
  supportedClaims,
  unsupportedClaims,
  copyApproach,
  formulaCode,
  hasConfirmedFacts,
  isRegenerating,
  reviewerName,
  reviewMessage,
  reviewFeedback,
  onReviewFeedbackChange,
  onFormulaChange,
  onReviewerChange,
  onBriefChange,
  onCopyChange,
  onCopyBlur,
  onPrepare,
  isPreparing,
  onApprove,
  onRequestChanges,
  onResubmit,
  canSavePlan,
  planSaveMessage,
  onSavePlan,
}: {
  welcomeName: string;
  contextName: string;
  contextSummary: string;
  contextSector?: string;
  handle: string;
  theme: BrandTheme;
  brief: BriefForm;
  previewCopy: string;
  status: DraftPreparationStatus;
  validationMessage: string;
  generationState: GenerationState;
  evidenceProvenance: DraftEvidence[];
  supportedClaims: string[];
  unsupportedClaims: string[];
  copyApproach: CopyApproachInfo | null;
  formulaCode: FormulaCode | "AUTO";
  hasConfirmedFacts: boolean;
  isRegenerating: boolean;
  reviewerName: string;
  reviewMessage: string;
  reviewFeedback: string;
  onReviewFeedbackChange: (value: string) => void;
  onFormulaChange: (value: FormulaCode | "AUTO") => void;
  onReviewerChange: (value: string) => void;
  onBriefChange: (field: keyof BriefForm, value: string) => void;
  onCopyChange: (value: string) => void;
  onCopyBlur: () => void | Promise<void>;
  onPrepare: () => void | Promise<void>;
  isPreparing: boolean;
  onApprove: () => void;
  onRequestChanges: () => void;
  onResubmit: () => void;
  canSavePlan: boolean;
  planSaveMessage: string;
  onSavePlan: () => void | Promise<void>;
}) {
  return (
    <section aria-labelledby="view-title">
      <header className={styles.head}>
        <div>
          <Kicker>Content Studio</Kicker>
          <p className={styles.greeting}>Hola, {welcomeName}</p>
          <h1 id="view-title" className={styles.title}>¿Qué historia contamos hoy?</h1>
          <p className={styles.context}>Marca activa: <strong>{contextName}</strong>. Cuéntame tu idea en el primer paso; tú decides qué se aprueba.</p>
        </div>
        <SyntheticNotice>API local · revisión humana · persistencia local</SyntheticNotice>
      </header>

      <div className={styles.grid}>
        <BriefEditor
          brief={brief}
          status={status}
          validationMessage={validationMessage}
          onChange={onBriefChange}
          onPrepare={onPrepare}
          isPreparing={isPreparing}
        />

        <ContentPreview
          contextName={contextName}
          handle={handle}
          theme={theme}
          brief={brief}
          copy={previewCopy}
          status={status}
          evidenceProvenance={evidenceProvenance}
          supportedClaims={supportedClaims}
          unsupportedClaims={unsupportedClaims}
           onCopyChange={onCopyChange}
           onCopyBlur={onCopyBlur}
        />

        <aside className={styles.side} aria-label="Estado editorial y contexto">
          <section aria-labelledby="state-title">
            <h2 id="state-title" className={styles.colTitle}>3 · Revisión</h2>
            <div className={styles.statusBlock}>
              <EditorialProgress status={status} />
              <StudioStatus status={status} />
              <p className={styles.generationState} aria-live="polite">
                Generación: {generationStateLabels[generationState]}
              </p>
              <p className={styles.hint}>{statusCopy[status].hint}</p>
            </div>
            {status !== "not-prepared" && (
              <div className={styles.approach} aria-labelledby="approach-title">
                <h3 id="approach-title" className={styles.approachTitle}>Enfoque del texto</h3>
                <p className={styles.approachName}>{copyApproach?.approach ?? "Estructura opcional"}</p>
                <label className={styles.label} htmlFor="copy-formula">Fórmula de copy</label>
                <select id="copy-formula" className={styles.input} value={formulaCode} onChange={(event) => onFormulaChange(event.target.value as FormulaCode | "AUTO")}>
                  <option value="AUTO">Automática</option>
                  <option value="AIDA">AIDA</option>
                  <option value="PAS">PAS</option>
                  <option value="4CS">4 Cs</option>
                  <option value="BAB">BAB</option>
                  <option value="4PS">4 Ps</option>
                  <option value="OPEN_LOOP">Bucle abierto</option>
                </select>
                {!hasConfirmedFacts && ["PAS", "BAB", "4PS"].includes(formulaCode) && (
                  <p className={styles.alert} role="status">Esta fórmula se apoya en hechos confirmados. El brief aún no los incluye; el texto deberá mantener un planteamiento general y no inventar pruebas ni resultados.</p>
                )}
                {copyApproach?.rationale && <p className={styles.note}>{copyApproach.rationale}</p>}
                <p className={styles.note}>Es solo una guía de estructura: editas el texto como quieras y nada se publica sin tu aprobación.</p>
              </div>
            )}
            <ReviewActions status={status} onApprove={onApprove} onRequestChanges={onRequestChanges} onResubmit={onResubmit} isRegenerating={isRegenerating} />
            {status === "pending-review" || status === "changes-requested" ? (
              <div className={styles.reviewerField}>
                <label className={styles.label} htmlFor="reviewer-name">Reviewer</label>
                <input id="reviewer-name" className={styles.input} value={reviewerName} onChange={(event) => onReviewerChange(event.target.value)} placeholder="Identidad del reviewer" />
                {(status === "pending-review" || status === "changes-requested") && <>
                  <label className={styles.label} htmlFor="review-feedback">Feedback</label>
                  <textarea id="review-feedback" className={styles.caption} value={reviewFeedback} onChange={(event) => onReviewFeedbackChange(event.target.value)} placeholder="Motivo de los cambios solicitados" readOnly={status === "changes-requested"} />
                </>}
                {reviewMessage && <p className={styles.alert} role="alert">{reviewMessage}</p>}
              </div>
            ) : null}
            <p className={styles.banner}>
              Aprobar solo cambia el estado local del prototipo. No habilita copia, exportación ni publicación.
            </p>
            <section className={styles.savePlan} aria-labelledby="plan-save-title">
              <h3 id="plan-save-title" className={styles.savePlanTitle}>Plan editorial</h3>
              <p className={styles.note}>Guarda el contenido validado como un plan de un ítem para verlo en el calendario.</p>
              <button className={styles.savePlanButton} type="button" onClick={onSavePlan} disabled={!canSavePlan} aria-describedby="plan-save-hint">
                Guardar plan validado
              </button>
              <p id="plan-save-hint" className={styles.note}>
                {canSavePlan ? "Se guardará en el Calendario editorial." : "Se habilita cuando hay un borrador preparado."}
              </p>
              {planSaveMessage && <p className={styles.saveMessage} role="status">{planSaveMessage}</p>}
            </section>
          </section>

          <section className={styles.details} aria-label="Variantes">
            <p><strong>Variantes</strong></p>
            <p className={styles.note}>
              Regenera con el feedback registrado para crear una versión nueva pendiente de revisión. Nada se publica sin aprobación.
            </p>
          </section>

          <details className={styles.details}>
            <summary>Contexto de marca</summary>
            <p>{contextSummary}</p>
            <dl>
              {contextSector && (<><dt>Sector</dt><dd>{contextSector}</dd></>)}
              <dt>Restricciones indicadas</dt>
              <dd>{brief.restrictions || "Sin restricciones indicadas"}</dd>
            </dl>
            <p className={styles.note}>
              El contexto de marca se aplica en segundo plano; esta vista mantiene la atención en tu idea y la revisión.
            </p>
          </details>
        </aside>
      </div>
    </section>
  );
}
