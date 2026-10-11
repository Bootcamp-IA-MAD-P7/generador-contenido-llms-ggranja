import { test } from "node:test";
import assert from "node:assert/strict";
import { canStartGeneration, dedupeEvidence, generationStateLabels, parseDraftResponse } from "../domain/draft-generation.ts";

function response(body: unknown, status = 200): Pick<Response, "ok" | "status" | "json"> {
  return { ok: status >= 200 && status < 300, status, json: async () => body };
}

test("a valid API response returns editable copy pending human review", async () => {
  const result = await parseDraftResponse(response({
    review_state: "pending_human_review",
    content_ids: ["content-1"],
    drafts: [{
      caption: " Texto real de la API ",
      evidence_provenance: [
        { business_id: "coll-amunt-pelu-sonia", source_id: "collamunt-llibre", source_file: "official.pdf", page_number: 3 },
        { business_id: "other-business", source_id: "other", page_number: 4 },
      ],
      supported_claims: ["Afirmación respaldada"],
      unsupported_claims: ["Afirmación dudosa"],
    }],
  }), "coll-amunt-pelu-sonia");
  assert.deepEqual(result, {
     copy: "Texto real de la API",
     contentIds: ["content-1"],
    reviewState: "pending_human_review",
    evidenceProvenance: [{ business_id: "coll-amunt-pelu-sonia", source_id: "collamunt-llibre", source_file: "official.pdf", page_number: 3 }],
    supportedClaims: ["Afirmación respaldada"],
    unsupportedClaims: ["Afirmación dudosa"],
    copyApproach: null,
  });
});

test("loading state prevents duplicate generations", () => {
  assert.equal(canStartGeneration("idle"), true);
  assert.equal(canStartGeneration("loading"), false);
  assert.equal(generationStateLabels.loading, "Generando…");
});

test("duplicate provenance entries collapse to one document page", () => {
  const evidence = { business_id: "business-a", source_id: "guide", source_file: "guide.pdf", page_number: 2 };
  assert.deepEqual(dedupeEvidence([evidence, { ...evidence }, { ...evidence, page_number: 3 }]), [evidence, { ...evidence, page_number: 3 }]);
});

test("partial provenance keeps only safe documented fields", async () => {
  const result = await parseDraftResponse(response({
    review_state: "pending_human_review",
    content_ids: ["content-1"],
    drafts: [{ caption: "Texto", evidence_provenance: [{ business_id: "business-a", source_file: 42, page_number: "3" }] }],
  }), "business-a");
  assert.deepEqual(result.evidenceProvenance, [{ business_id: "business-a" }]);
});

test("API errors remain visible to the caller", async () => {
  await assert.rejects(parseDraftResponse(response({ detail: "Servicio no disponible" }, 503)), /Servicio no disponible/);
});

test("an empty response is rejected", async () => {
  await assert.rejects(parseDraftResponse(response({ review_state: "pending_human_review", content_ids: [], drafts: [] })), /borrador editable/);
});

test("an invalid editorial state is rejected and cannot auto-approve", async () => {
  await assert.rejects(parseDraftResponse(response({ review_state: "approved", drafts: [{ caption: "Texto" }] })), /pendiente de revisión humana/);
});

test("malformed HTTP responses are rejected", async () => {
  await assert.rejects(parseDraftResponse({ ok: true, status: 200, json: async () => { throw new Error("invalid json"); } }), /respuesta no válida/);
});

test("parseCopyApproach reads suggested approach and ignores blanks", async () => {
  const { parseCopyApproach } = await import("../domain/draft-generation.ts");
  assert.deepEqual(parseCopyApproach({ copy_approach: "Educativo", copy_formula: "4 Cs", approach_rationale: "Explica." }), { approach: "Educativo", formula: "4 Cs", rationale: "Explica." });
  assert.equal(parseCopyApproach({ copy_approach: "  " }), null);
  assert.equal(parseCopyApproach({}), null);
});
