"use client";

import { useEffect, useMemo, useState } from "react";
import { getPlans, updatePlanItemDay, type StoredPlan } from "../../domain/plans-api.ts";
import {
  applyMoves,
  bucketLabels,
  distribute,
  formatLabels,
  itemsByDate,
  mergeTargets,
  monthGrid,
  parseISO,
  platformLabels,
  sampleItems,
  SAMPLE_START,
  shiftMonth,
  thirdsTargets,
  type CalendarItem,
} from "../../domain/calendar-layout.ts";
import { Kicker } from "../ui/Kicker";
import { MixSummary } from "./MixSummary";
import styles from "./calendar.module.css";

const weekdays = ["L", "M", "X", "J", "V", "S", "D"];
const bucketClass: Record<string, string> = {
  EDUCATIONAL: styles.bEdu,
  COMMUNITY: styles.bCom,
  PROMOTIONAL: styles.bPro,
  VALUE: styles.bCom,
};

function planItems(plans: StoredPlan[]): CalendarItem[] {
  return plans.flatMap(({ plan_id, plan }) => {
    const base = distribute(
      plan.items.map((item, index) => ({
        id: `${plan_id}-${index}`,
        title: `${bucketLabels[item.bucket_key] ?? item.bucket_key} · ${platformLabels[item.platform] ?? item.platform}`,
        bucket: item.bucket_key,
        platform: item.platform,
        format: item.format,
      })),
      plan.starts_on,
    );
    return plan.items.map((item, index) => ({
      ...base[index],
      date: item.scheduled_on ?? (base[index].date <= plan.ends_on ? base[index].date : plan.ends_on),
      planId: plan_id,
      itemIndex: index,
      startsOn: plan.starts_on,
      endsOn: plan.ends_on,
    }));
  });
}

export function CalendarView({ welcomeName }: { welcomeName: string }) {
  const [plans, setPlans] = useState<StoredPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showSample, setShowSample] = useState(false);
  const [cursor, setCursor] = useState(() => {
    const now = new Date();
    return { year: now.getFullYear(), month: now.getMonth() };
  });
  const [moves, setMoves] = useState<Record<string, string>>({});
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [dragId, setDragId] = useState<string | null>(null);
  const [savingId, setSavingId] = useState<string | null>(null);

  useEffect(() => {
    getPlans()
      .then(setPlans)
      .catch((cause: Error) => setError(cause.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape") setSelectedId(null); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selectedId]);

  const items = useMemo(() => {
    const base = [...planItems(plans), ...(showSample ? distribute(sampleItems, SAMPLE_START) : [])];
    return applyMoves(base, moves);
  }, [plans, showSample, moves]);
  const byDate = useMemo(() => itemsByDate(items), [items]);
  const grid = useMemo(() => monthGrid(cursor.year, cursor.month), [cursor]);
  const selected = items.find((item) => item.id === selectedId);
  const rawLabel = new Date(Date.UTC(cursor.year, cursor.month, 1)).toLocaleDateString("es-ES", { month: "long", year: "numeric", timeZone: "UTC" });
  const monthLabel = rawLabel.charAt(0).toUpperCase() + rawLabel.slice(1).replace(" de ", " ");
  const monthPrefix = `${cursor.year}-${String(cursor.month + 1).padStart(2, "0")}`;
  const monthItems = items.filter((item) => item.date.startsWith(monthPrefix));
  const monthCount = monthItems.length;
  const monthTargets = useMemo(() => {
    const inMonth = (date: string) => date.startsWith(monthPrefix);
    const planTargets = plans.filter(({ plan_id }) => monthItems.some((item) => item.id.startsWith(`${plan_id}-`))).map(({ plan }) => plan.targets);
    const sampleCount = showSample ? monthItems.filter((item) => item.synthetic && inMonth(item.date)).length : 0;
    return mergeTargets([...planTargets, ...(sampleCount ? [thirdsTargets(sampleCount)] : [])]);
  }, [plans, showSample, monthItems, monthPrefix]);

  async function moveTo(date: string, id: string | null) {
    if (!id) return;
    const item = items.find((candidate) => candidate.id === id);
    if (!item) return;
    if (item.startsOn && item.endsOn && (date < item.startsOn || date > item.endsOn)) {
      setError("El día elegido debe estar dentro del rango del plan.");
      return;
    }
    if (item.planId && item.itemIndex !== undefined) {
      setSavingId(id);
      setError("");
      try {
        const updated = await updatePlanItemDay(item.planId, item.itemIndex, date);
        setPlans((current) => current.map((stored) => stored.plan_id === updated.plan_id ? updated : stored));
        setSelectedId(null);
      } catch (cause) {
        setError(cause instanceof Error ? `No se pudo guardar el cambio de día: ${cause.message}` : "No se pudo guardar el cambio de día.");
      } finally {
        setSavingId(null);
        setDragId(null);
      }
      return;
    }
    setMoves((current) => ({ ...current, [id]: date }));
    setSelectedId(null);
    setDragId(null);
  }

  function toggleSample() {
    if (showSample) {
      setShowSample(false);
      setMoves({});
      setSelectedId(null);
      return;
    }
    setShowSample(true);
    const start = parseISO(SAMPLE_START);
    setCursor({ year: start.getUTCFullYear(), month: start.getUTCMonth() });
  }

  return (
    <section className={styles.view} aria-labelledby="calendar-title">
      <header className={styles.head}>
        <div>
          <Kicker>Calendario editorial</Kicker>
          <p className={styles.greeting}>Hola, {welcomeName}</p>
          <h1 id="calendar-title" className={styles.title}>¿Qué planificamos este mes?</h1>
          <p className={styles.lede}>Las publicaciones se reparten en lunes, miércoles y viernes. Muévelas al día que prefieras.</p>
        </div>
        <button type="button" className={styles.sampleButton} onClick={toggleSample} aria-pressed={showSample}>
          {showSample ? "Quitar ejemplo de noviembre" : "Cargar ejemplo de noviembre"}
        </button>
      </header>

      {error && <p className={styles.alert} role="alert">Calendario: {error}</p>}
      {loading && <p className={styles.state} role="status">Cargando planes…</p>}

      <div className={styles.toolbar}>
        <div className={styles.nav}>
          <button type="button" className={styles.navButton} onClick={() => setCursor((c) => shiftMonth(c.year, c.month, -1))} aria-label="Mes anterior">‹</button>
          <h2 className={styles.month} aria-live="polite">{monthLabel}</h2>
          <button type="button" className={styles.navButton} onClick={() => setCursor((c) => shiftMonth(c.year, c.month, 1))} aria-label="Mes siguiente">›</button>
        </div>
        <ul className={styles.legend} aria-label="Leyenda de bloques">
          <li><span className={`${styles.swatch} ${styles.bEdu}`} />Educativo</li>
          <li><span className={`${styles.swatch} ${styles.bCom}`} />Comunidad</li>
          <li><span className={`${styles.swatch} ${styles.bPro}`} />Promoción y marca</li>
        </ul>
      </div>

      {selected && (
        <p className={styles.moving} role="status">
          Moviendo «{selected.title}». Elige un día con «Mover aquí» o pulsa Esc para cancelar.
        </p>
      )}

      <div className={styles.grid} role="group" aria-label={`Calendario de ${monthLabel}`}>
        {weekdays.map((day) => <div key={day} className={styles.dow} aria-hidden="true">{day}</div>)}
        {grid.map((cell) => {
          const dayItems = byDate.get(cell.date) ?? [];
          return (
            <div
              key={cell.date}
              className={`${styles.cell} ${cell.inMonth ? "" : styles.outside} ${dragId ? styles.droppable : ""}`}
              onDragOver={(event) => { if (dragId) event.preventDefault(); }}
              onDrop={(event) => { event.preventDefault(); moveTo(cell.date, dragId); }}
            >
              <span className={styles.dayNum}>{cell.day}</span>
              {dayItems.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  draggable
                  className={`${styles.post} ${bucketClass[item.bucket] ?? styles.bCom} ${item.id === selectedId ? styles.postSelected : ""}`}
                  aria-pressed={item.id === selectedId}
                  onClick={() => setSelectedId(item.id === selectedId ? null : item.id)}
                  onDragStart={() => setDragId(item.id)}
                  onDragEnd={() => setDragId(null)}
                >
                  <span className={styles.postTitle}>{item.title}</span>
                  <span className={styles.postMeta}>{platformLabels[item.platform] ?? item.platform} · {formatLabels[item.format] ?? item.format}</span>
                </button>
              ))}
              {selected && selected.date !== cell.date && cell.inMonth &&
                (!selected.startsOn || !selected.endsOn || (cell.date >= selected.startsOn && cell.date <= selected.endsOn)) && (
                <button type="button" className={styles.dropHere} onClick={() => moveTo(cell.date, selectedId)}>
                  {savingId === selected.id ? "Guardando…" : "Mover aquí"}<span className="sr-only"> el {cell.day} de {monthLabel}</span>
                </button>
              )}
            </div>
          );
        })}
      </div>

      <MixSummary items={monthItems} monthLabel={monthLabel} targets={monthTargets} />

      {!loading && items.length === 0 && (
        <p className={styles.state}>
          Aún no hay publicaciones planificadas. Guarda un plan validado desde Content Studio o carga el ejemplo para ver cómo se vería un mes completo.
        </p>
      )}
      <p className={styles.note}>
        {showSample ? "Ejemplo sintético de 12 publicaciones. " : ""}
        {monthCount} en {monthLabel}. Los cambios de día de los planes guardados se persisten; los movimientos del ejemplo sintético duran esta sesión.
      </p>
    </section>
  );
}
