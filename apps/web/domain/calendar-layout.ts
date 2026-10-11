/** Pure, timezone-safe helpers for the editorial calendar month view. */

export type CalendarItem = {
  id: string;
  title: string;
  bucket: string;
  platform: string;
  format: string;
  date: string;
  synthetic?: boolean;
  planId?: string;
  itemIndex?: number;
  startsOn?: string;
  endsOn?: string;
};

export type UndatedItem = Omit<CalendarItem, "date">;

export type DayCell = { date: string; day: number; inMonth: boolean };

const DAY_MS = 86_400_000;

export function parseISO(value: string): Date {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(Date.UTC(year, month - 1, day));
}

export function toISO(date: Date): string {
  return date.toISOString().slice(0, 10);
}

export function addDays(value: string, days: number): string {
  return toISO(new Date(parseISO(value).getTime() + days * DAY_MS));
}

/** Six Monday-first weeks covering the month, so the grid height never jumps. */
export function monthGrid(year: number, month: number): DayCell[] {
  const first = new Date(Date.UTC(year, month, 1));
  const offset = (first.getUTCDay() + 6) % 7;
  const start = first.getTime() - offset * DAY_MS;
  return Array.from({ length: 42 }, (_, index) => {
    const date = new Date(start + index * DAY_MS);
    return { date: toISO(date), day: date.getUTCDate(), inMonth: date.getUTCMonth() === month };
  });
}

export function shiftMonth(year: number, month: number, delta: number): { year: number; month: number } {
  const total = year * 12 + month + delta;
  return { year: Math.floor(total / 12), month: ((total % 12) + 12) % 12 };
}

/** Monday, Wednesday and Friday by default (getUTCDay: 1, 3, 5). */
export const DEFAULT_WEEKDAYS = [1, 3, 5];

/** Places items one per publishing slot, in order, starting on or after `startsOn`. */
export function distribute(
  items: UndatedItem[],
  startsOn: string,
  weekdays: number[] = DEFAULT_WEEKDAYS,
): CalendarItem[] {
  const result: CalendarItem[] = [];
  let cursor = startsOn;
  for (const item of items) {
    while (!weekdays.includes(parseISO(cursor).getUTCDay())) cursor = addDays(cursor, 1);
    result.push({ ...item, date: cursor });
    cursor = addDays(cursor, 1);
  }
  return result;
}

export function applyMoves(items: CalendarItem[], moves: Record<string, string>): CalendarItem[] {
  return items.map((item) => (moves[item.id] ? { ...item, date: moves[item.id] } : item));
}

export function itemsByDate(items: CalendarItem[]): Map<string, CalendarItem[]> {
  const map = new Map<string, CalendarItem[]>();
  for (const item of items) map.set(item.date, [...(map.get(item.date) ?? []), item]);
  return map;
}

export const bucketLabels: Record<string, string> = {
  EDUCATIONAL: "Educativo",
  COMMUNITY: "Comunidad",
  PROMOTIONAL: "Promoción y marca",
  VALUE: "Valor y comunidad",
};

export const platformLabels: Record<string, string> = { instagram: "Instagram", facebook: "Facebook" };
export const formatLabels: Record<string, string> = { single_image: "Publicación", carousel: "Carrusel", reel: "Reel" };

/** Synthetic sample used to preview a full month; clearly labelled in the UI. */
export const SAMPLE_START = "2026-11-02";
export const sampleItems: UndatedItem[] = [
  ["Qué es la gamificación en la empresa", "EDUCATIONAL", "instagram", "carousel"],
  ["¿Qué juego te engancha y por qué?", "COMMUNITY", "facebook", "single_image"],
  ["Quiénes somos: soluciones gamificadas", "PROMOTIONAL", "instagram", "reel"],
  ["Retos frente a obligaciones", "EDUCATIONAL", "instagram", "carousel"],
  ["¿Cómo aprende mejor tu equipo?", "COMMUNITY", "instagram", "reel"],
  ["Cómo trabajamos: del reto al juego", "PROMOTIONAL", "facebook", "single_image"],
  ["Elementos de un juego aplicables al trabajo", "EDUCATIONAL", "instagram", "carousel"],
  ["Mito o realidad: ¿jugar es perder el tiempo?", "COMMUNITY", "instagram", "reel"],
  ["Un ejemplo de solución gamificada", "PROMOTIONAL", "facebook", "single_image"],
  ["Errores habituales al gamificar", "EDUCATIONAL", "instagram", "carousel"],
  ["Reto de cierre de mes para tu equipo", "COMMUNITY", "instagram", "reel"],
  ["Hablemos: cómo empezar con tu equipo", "PROMOTIONAL", "facebook", "single_image"],
].map(([title, bucket, platform, format], index) => ({
  id: `sample-${index + 1}`,
  title,
  bucket,
  platform,
  format,
  synthetic: true,
}));

export type MixRow = { bucket: string; label: string; count: number; percent: number };

/** Counts and shares per content bucket for the given items, largest first by bucket order of appearance. */
export function summarizeMix(items: CalendarItem[]): { total: number; rows: MixRow[]; platforms: Record<string, number>; formats: Record<string, number> } {
  const counts = new Map<string, number>();
  const platforms: Record<string, number> = {};
  const formats: Record<string, number> = {};
  for (const item of items) {
    counts.set(item.bucket, (counts.get(item.bucket) ?? 0) + 1);
    platforms[item.platform] = (platforms[item.platform] ?? 0) + 1;
    formats[item.format] = (formats[item.format] ?? 0) + 1;
  }
  const total = items.length;
  const rows = [...counts.entries()].map(([bucket, count]) => ({
    bucket,
    label: bucketLabels[bucket] ?? bucket,
    count,
    percent: total ? Math.round((count / total) * 100) : 0,
  }));
  return { total, rows, platforms, formats };
}

/**
 * Qualitative expectations only. There is no historical data behind them, so no
 * figures are produced: they describe which signal each kind of content tends to
 * move and must be replaced by measured results once available.
 */
export const engagementHints: Record<string, { signal: string; expectation: string }> = {
  EDUCATIONAL: { signal: "Guardados y compartidos", expectation: "Suele generar menos comentarios y más guardados; construye autoridad a medio plazo." },
  COMMUNITY: { signal: "Comentarios y respuestas", expectation: "Es lo que más conversación abre; funciona mejor con una pregunta clara." },
  PROMOTIONAL: { signal: "Clics y mensajes", expectation: "Alcance más contenido y menos interacción espontánea; conviene no pasar de un tercio." },
  VALUE: { signal: "Interacción general", expectation: "Mezcla de aprendizaje y conversación; base de la relación con la audiencia." },
};

export const formatHints: Record<string, string> = {
  reel: "Reels: mayor alcance potencial entre personas que aún no te siguen.",
  carousel: "Carruseles: favorecen guardados y tiempo de lectura.",
  single_image: "Publicaciones: útiles para avisos y mensajes directos en Facebook.",
};

export type BalanceRow = { bucket: string; label: string; actual: number; target: number; diff: number; percent: number };

const THIRDS: [string, number][] = [["EDUCATIONAL", 34], ["COMMUNITY", 33], ["PROMOTIONAL", 33]];

/** Same largest-remainder split as the API's THREE_THIRDS preset (34/33/33). */
export function thirdsTargets(total: number): Record<string, number> {
  const quotas = THIRDS.map(([, pct]) => total * pct);
  const counts = quotas.map((quota) => Math.floor(quota / 100));
  const order = quotas.map((_, index) => index).sort((a, b) => (quotas[b] % 100) - (quotas[a] % 100) || a - b);
  for (const index of order.slice(0, total - counts.reduce((sum, count) => sum + count, 0))) counts[index] += 1;
  return Object.fromEntries(THIRDS.map(([key], index) => [key, counts[index]]));
}

export function mergeTargets(list: Record<string, number>[]): Record<string, number> {
  const merged: Record<string, number> = {};
  for (const targets of list) for (const [key, count] of Object.entries(targets)) merged[key] = (merged[key] ?? 0) + count;
  return merged;
}

/** Compares what is planned with the strategy targets. Pure arithmetic, no judgement or forecast. */
export function balance(items: CalendarItem[], targets: Record<string, number>): { total: number; rows: BalanceRow[]; balanced: boolean; message: string } {
  const actual: Record<string, number> = {};
  for (const item of items) actual[item.bucket] = (actual[item.bucket] ?? 0) + 1;
  const keys = [...new Set([...Object.keys(targets), ...Object.keys(actual)])];
  const total = items.length;
  const rows = keys.map((bucket) => ({
    bucket,
    label: bucketLabels[bucket] ?? bucket,
    actual: actual[bucket] ?? 0,
    target: targets[bucket] ?? 0,
    diff: (actual[bucket] ?? 0) - (targets[bucket] ?? 0),
    percent: total ? Math.round(((actual[bucket] ?? 0) / total) * 100) : 0,
  }));
  const excess = rows.filter((row) => row.diff > 0);
  const lacking = rows.filter((row) => row.diff < 0);
  const balanced = excess.length === 0 && lacking.length === 0;
  const plural = (n: number) => `${n} ${n === 1 ? "publicación" : "publicaciones"}`;
  const message = balanced
    ? "El mes está equilibrado respecto al objetivo."
    : `Para equilibrar: ${excess.length ? `cambia ${plural(excess.reduce((sum, row) => sum + row.diff, 0))} de ${excess.map((row) => row.label.toLowerCase()).join(" y ")}` : "añade publicaciones"}${lacking.length ? ` ${excess.length ? "por" : "de"} ${lacking.map((row) => `${-row.diff} ${row.label.toLowerCase()}`).join(" y ")}` : ""}.`;
  return { total, rows, balanced, message };
}
