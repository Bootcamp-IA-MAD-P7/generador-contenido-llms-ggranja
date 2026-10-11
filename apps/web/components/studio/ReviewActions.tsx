import type { DraftPreparationStatus } from "../../domain/types.ts";
import styles from "./studio.module.css";

/** Explicit human decisions. Rendered only for the states that allow them. */
export function ReviewActions({
  status,
  onApprove,
  onRequestChanges,
  onResubmit,
  isRegenerating,
}: {
  status: DraftPreparationStatus;
  onApprove: () => void;
  onRequestChanges: () => void;
  onResubmit: () => void;
  isRegenerating: boolean;
}) {
  if (status === "pending-review") {
    return (
      <div className={styles.actions} role="group" aria-label="Decisión de revisión">
        <button type="button" className={styles.action} onClick={onRequestChanges}>Solicitar cambios</button>
        <button type="button" className={`${styles.action} ${styles.approve}`} onClick={onApprove}>Aprobar en prototipo</button>
      </div>
    );
  }
  if (status === "changes-requested") {
    return (
      <div className={styles.actions}>
        <button type="button" className={styles.action} onClick={onResubmit} disabled={isRegenerating}>
          {isRegenerating ? "Regenerando…" : "Regenerar"}
        </button>
      </div>
    );
  }
  return null;
}
