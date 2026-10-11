import { test } from "node:test";
import assert from "node:assert/strict";
import { createDraft, regenerateDraft, reviewDraft, updateDraft, ReviewApiError } from "../domain/review-api.ts";
import { savePlan, updatePlanItemDay } from "../domain/plans-api.ts";

const originalFetch = globalThis.fetch;

test.afterEach(() => { globalThis.fetch = originalFetch; });

test("createDraft sends brand, business and RAG parameters to the API", async () => {
  let request: Request | undefined;
  globalThis.fetch = async (input, init) => {
    request = new Request(input, init);
    return Response.json({ review_state: "pending_human_review", drafts: [], content_ids: [] });
  };
  await createDraft({ brief: { topic_or_offer: "Oferta", objective: "Objetivo", audience_context: "Barrio", business_context_refs: ["store"], platforms: ["instagram"], format: "single_image", brand_and_constraints: undefined, notes: "Generated from Content Studio.", facts: [] }, brandId: "coll-amunt", businessId: "business-a", ragEnabled: true });
  const body = await request!.json() as Record<string, unknown>;
  assert.equal(request!.url, "http://127.0.0.1:8000/drafts");
  assert.deepEqual(body, { brief: { topic_or_offer: "Oferta", objective: "Objetivo", audience_context: "Barrio", business_context_refs: ["store"], platforms: ["instagram"], format: "single_image", notes: "Generated from Content Studio.", facts: [] }, rag_enabled: true, brand_id: "coll-amunt", business_id: "business-a", top_k: 3 });
});

test("review and edit use the backend content id and preserve explicit decisions", async () => {
  const calls: Request[] = [];
  globalThis.fetch = async (input, init) => { calls.push(new Request(input, init)); return Response.json({ content_id: "content-1", state: "pending_human_review", draft: { caption: "Editado", evidence_provenance: [], supported_claims: [], unsupported_claims: [] } }); };
  await updateDraft("content-1", "Editado");
  await reviewDraft("content-1", "request_regeneration", "reviewer-1", "Aclarar el beneficio");
  assert.equal(calls[0].method, "PATCH");
  assert.equal(calls[0].url, "http://127.0.0.1:8000/drafts/content-1");
  assert.deepEqual(await calls[1].json(), { decision: "request_regeneration", reviewer_ref: "reviewer-1", feedback: "Aclarar el beneficio" });
});

test("regeneration sends the exact feedback, selected formula and current brief", async () => {
  let request: Request | undefined;
  globalThis.fetch = async (input, init) => {
    request = new Request(input, init);
    return Response.json({ content_id: "new-content", state: "pending_human_review" });
  };
  const feedback = "  Aclara el beneficio, por favor.  ";
  await regenerateDraft("content-1", {
    brief: { topic_or_offer: "Oferta", objective: "Informar", audience_context: "Barrio", business_context_refs: ["store"], platforms: ["instagram"], format: "single_image", brand_and_constraints: undefined, notes: "Generated from Content Studio.", facts: [] },
    feedback,
    formula: "4PS",
    businessId: "business-a",
    ragEnabled: true,
  });
  assert.equal(request!.method, "POST");
  assert.equal(request!.url, "http://127.0.0.1:8000/drafts/content-1/regenerate");
  assert.deepEqual(await request!.json(), {
    brief: { topic_or_offer: "Oferta", objective: "Informar", audience_context: "Barrio", business_context_refs: ["store"], platforms: ["instagram"], format: "single_image", notes: "Generated from Content Studio.", facts: [] },
    feedback,
    formula: "4PS",
    rag_enabled: true,
    top_k: 3,
  });
});

test("HTTP transition errors are actionable and retain their status", async () => {
  globalThis.fetch = async () => Response.json({ detail: "cannot approve" }, { status: 409 });
  await assert.rejects(reviewDraft("content-1", "approve", "reviewer-1"), (error: unknown) => error instanceof ReviewApiError && error.status === 409 && /Transición editorial inválida/.test(error.message));
});

test("savePlan sends a validated plan to the persistence API", async () => {
  let request: Request | undefined;
  globalThis.fetch = async (input, init) => {
    request = new Request(input, init);
    return Response.json({ plan_id: "plan-1", plan: await request!.clone().json() });
  };
  const plan = {
    strategy_id: "eighty_twenty",
    strategy_version: "1.0.0",
    total_slots: 1,
    starts_on: "2026-10-10",
    ends_on: "2026-10-10",
    targets: { VALUE: 1 },
    items: [{
      source_ref: "content-1",
      source_kind: "editorial_content" as const,
      strategy_version: "1.0.0",
      bucket_key: "VALUE",
      platform: "instagram" as const,
      format: "single_image" as const,
      review_state: "pending_human_review",
    }],
  };
  const saved = await savePlan(plan);
  assert.equal(request!.method, "POST");
  assert.equal(request!.url, "http://127.0.0.1:8000/plans");
  assert.deepEqual(await request!.json(), plan);
  assert.equal(saved.plan_id, "plan-1");
});

test("calendar movement persists the selected day through the plan API", async () => {
  let request: Request | undefined;
  globalThis.fetch = async (input, init) => {
    request = new Request(input, init);
    return Response.json({ plan_id: "plan-1", plan: { items: [{ scheduled_on: "2026-10-15" }] } });
  };
  const result = await updatePlanItemDay("plan-1", 0, "2026-10-15");
  assert.equal(request!.method, "PATCH");
  assert.equal(request!.url, "http://127.0.0.1:8000/plans/plan-1/items/0/day");
  assert.deepEqual(await request!.json(), { day: "2026-10-15" });
  assert.equal(result.plan.items[0].scheduled_on, "2026-10-15");
});
