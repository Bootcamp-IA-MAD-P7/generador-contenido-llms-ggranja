export type ViewId =
  | "dashboard"
  | "content-studio"
  | "drafts"
  | "history"
  | "calendar"
  | "library"
  | "analytics"
  | "brands"
  | "settings";

export type BrandId = "panaderia" | "coll-amunt";
export type CommerceId = "pelu-sonia" | "centre-d-estetica-alma";

/** Brand-specific colours. They colour brand artefacts only, never the platform UI. */
export type BrandTheme = {
  accent: string;
  ink: string;
  tint: string;
};

export type CommerceContext = {
  id: CommerceId;
  name: string;
  account: string;
  businessId: string;
  sector: string;
  summary: string;
  theme?: BrandTheme;
};

export type BrandContext = {
  id: BrandId;
  name: string;
  account: string;
  kind: string;
  summary: string;
  theme: BrandTheme;
  commerceOptions?: CommerceContext[];
};

export type Platform = "Instagram" | "Facebook";
export type ContentFormat = "Reel" | "Carrusel" | "Publicación";

export type BriefForm = {
  objective: string;
  audience: string;
  platform: Platform;
  format: ContentFormat;
  campaign: string;
  restrictions: string;
};

/** Local prototype states. They are narrower than the backend lifecycle on purpose. */
export type DraftPreparationStatus =
  | "not-prepared"
  | "draft"
  | "pending-review"
  | "brief-changed"
  | "changes-requested"
  | "approved";

export type EditorialStatus = "draft" | "review" | "approved";

export type DashboardItem = {
  id: string;
  title: string;
  date: string;
  platform: Platform;
  format: ContentFormat;
  campaign: string;
};

export type DashboardActivity = { id: string; text: string; time: string };

export type DashboardFixture = {
  drafts: number;
  review: number;
  approved: number;
  upcoming: DashboardItem[];
  activity: DashboardActivity[];
};

export type LocalDraft = {
  id: string;
  title: string;
  platform: Platform;
  format: ContentFormat;
  status: EditorialStatus;
  updatedAt: string;
  brief: BriefForm;
  copy: string;
  evidenceProvenance?: DraftEvidence[];
  supportedClaims?: string[];
  unsupportedClaims?: string[];
  copyApproach?: CopyApproachInfo | null;
  reviewer?: string;
  backendId?: string;
};

/** Suggested copy approach and optional formula, with the reason, shown to the human reviewer. */
export type CopyApproachInfo = { approach: string; formula: string; rationale: string };

export type DraftEvidence = {
  business_id: string;
  source_type?: string;
  source_id?: string;
  source_version?: string;
  source_file?: string | null;
  page_number?: number | null;
  source_uri?: string | null;
};

export type HistoryStatus = EditorialStatus | "changes-requested";

export type HistoryEntry = {
  id: string;
  text: string;
  time: string;
  status: HistoryStatus;
  draftId: string;
  source?: "session";
};
