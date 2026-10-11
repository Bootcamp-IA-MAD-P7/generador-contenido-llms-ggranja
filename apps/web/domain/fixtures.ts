import type {
  BrandContext,
  BriefForm,
  DashboardFixture,
  HistoryEntry,
  LocalDraft,
} from "./types.ts";

/**
 * Deterministic UI fixtures. The Talent Hive sample brand remains synthetic; Coll
 * Amunt! commerce contexts carry only official names and real business IDs.
 * Factual content for those businesses is retrieved by the API RAG boundary.
 */

export const brandContexts: BrandContext[] = [
  {
    id: "panaderia",
    name: "Talent Hive",
    account: "talenthive",
    kind: "Soluciones gamificadas para empresas",
    summary: "Soluciones gamificadas para empresas. Ficha sintética de ejemplo.",
    theme: { accent: "#2453d4", ink: "#0f1f4d", tint: "#dfe7fb" },
  },
  {
    id: "coll-amunt",
    name: "Coll Amunt!",
    account: "collamunt",
    kind: "Asociación de comercio local · Barcelona",
    summary: "Asociación de comercios locales de Barcelona. El contexto factual se recupera del PDF oficial de Coll Amunt!.",
    theme: { accent: "#176b9a", ink: "#12354b", tint: "#dceef7" },
    commerceOptions: [
      {
        id: "pelu-sonia",
        name: "Pelu Sonia",
        account: "coll-amunt-pelu-sonia",
        businessId: "coll-amunt-pelu-sonia",
        sector: "Comercio asociado",
        summary: "Contexto oficial recuperable desde el PDF de Coll Amunt!.",
      },
      {
        id: "centre-d-estetica-alma",
        name: "Centre d\u2019Est\u00e8tica Alma",
        account: "coll-amunt-centre-d-estetica-alma",
        businessId: "coll-amunt-centre-d-estetica-alma",
        sector: "Comercio asociado",
        summary: "Contexto oficial recuperable desde el PDF de Coll Amunt!.",
      },
    ],
  },
];

export const dashboardFixtures: Record<string, DashboardFixture> = {
  talenthive: {
    drafts: 3,
    review: 2,
    approved: 5,
    upcoming: [
      { id: "hive-1", title: "Qué es la gamificación en la empresa", date: "12 jun", platform: "Instagram", format: "Carrusel", campaign: "Aprender jugando" },
      { id: "hive-2", title: "Retos que activan a los equipos", date: "14 jun", platform: "Facebook", format: "Publicación", campaign: "Equipos en juego" },
    ],
    activity: [
      { id: "hive-a1", text: "Borrador sintético actualizado: Qué es la gamificación", time: "Hoy, 09:40" },
      { id: "hive-a2", text: "Contenido sintético aprobado para revisión final", time: "Ayer, 16:20" },
      { id: "hive-a3", text: "Nuevo contenido añadido al calendario de ejemplo", time: "10 jun, 11:05" },
    ],
  },
  "coll-amunt-pelu-sonia": {
    drafts: 0,
    review: 0,
    approved: 0,
    upcoming: [],
    activity: [],
  },
  "coll-amunt-centre-d-estetica-alma": {
    drafts: 0,
    review: 0,
    approved: 0,
    upcoming: [],
    activity: [],
  },
};

export const briefDefaults: Record<string, BriefForm> = {
  talenthive: {
    objective: "Presentar una solución gamificada para equipos",
    audience: "Responsables de personas y equipos en empresas",
    platform: "Instagram",
    format: "Carrusel",
    campaign: "Aprender jugando",
    restrictions: "Mantener un tono cercano y profesional, sin prometer resultados ni cifras.",
  },
  "coll-amunt-pelu-sonia": {
    objective: "Dar a conocer el comercio seleccionado",
    audience: "Vecinas y vecinos del barrio",
    platform: "Instagram",
    format: "Carrusel",
    campaign: "Comercio de proximidad",
    restrictions: "Usar únicamente información respaldada por el PDF oficial y mantener el contenido pendiente de revisión humana.",
  },
  "coll-amunt-centre-d-estetica-alma": {
    objective: "Dar a conocer el comercio seleccionado",
    audience: "Vecinas y vecinos del barrio",
    platform: "Facebook",
    format: "Publicación",
    campaign: "Comercio de proximidad",
    restrictions: "Usar únicamente información respaldada por el PDF oficial y mantener el contenido pendiente de revisión humana.",
  },
};

export function getBriefDefaults(account: string): BriefForm {
  return briefDefaults[account] ?? briefDefaults.talenthive;
}

export const draftFixtures: Record<string, LocalDraft[]> = {
  talenthive: [
    {
      id: "hive-draft-aprender-jugando",
      title: "Aprender jugando: una idea para tu equipo",
      platform: "Instagram",
      format: "Carrusel",
      status: "draft",
      updatedAt: "Hoy · 09:40",
      brief: { ...briefDefaults.talenthive, objective: "Presentar una idea de aprendizaje gamificado" },
      copy: `Borrador sintético · Talent Hive\n\nUna idea para que el aprendizaje en la empresa se parezca más a un juego.\n\nContenido de ejemplo, pendiente de edición.`,
    },
    {
      id: "hive-review-retos",
      title: "Retos que motivan a un equipo",
      platform: "Facebook",
      format: "Publicación",
      status: "review",
      updatedAt: "Ayer · 16:20",
      brief: { ...briefDefaults.talenthive, platform: "Facebook", format: "Publicación", campaign: "Aprender jugando" },
      copy: `Borrador sintético · Talent Hive\n\nDescubre cómo un reto bien diseñado puede activar a un equipo.\n\nContenido de ejemplo, pendiente de revisión humana.`,
    },
    {
      id: "hive-approved-equipos",
      title: "Equipos en juego",
      platform: "Instagram",
      format: "Publicación",
      status: "approved",
      updatedAt: "8 oct · 12:15",
      brief: { ...briefDefaults.talenthive, format: "Publicación", campaign: "Equipos en juego" },
      copy: `Texto sintético aprobado en el prototipo para ilustrar el estado editorial.`,
    },
  ],
  "coll-amunt-pelu-sonia": [],
  "coll-amunt-centre-d-estetica-alma": [],
};

/** Synthetic editorial activity retained from the existing History screen. */
export const historyFixtures: Record<string, HistoryEntry[]> = {
  talenthive: [
    { id: "hive-history-1", text: "Se editó un borrador local.", time: "Hoy · 09:40", status: "draft", draftId: "hive-draft-aprender-jugando" },
    { id: "hive-history-2", text: "El contenido se envió a revisión humana.", time: "Ayer · 16:20", status: "review", draftId: "hive-review-retos" },
    { id: "hive-history-3", text: "Se marcó como aprobado en el prototipo.", time: "8 oct · 12:15", status: "approved", draftId: "hive-approved-equipos" },
  ],
  "coll-amunt-pelu-sonia": [],
  "coll-amunt-centre-d-estetica-alma": [],
};
