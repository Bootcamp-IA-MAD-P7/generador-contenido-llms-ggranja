import { test } from "node:test";
import assert from "node:assert/strict";
import { parseSession } from "../domain/auth.ts";

const valid = JSON.stringify({ token: "t", username: "gabriela", expiresAt: 2000 });

test("parseSession returns a live session", () => {
  assert.deepEqual(parseSession(valid, 1000), { token: "t", username: "gabriela", expiresAt: 2000 });
});

test("parseSession ignores expired, malformed and missing sessions", () => {
  assert.equal(parseSession(valid, 2000), null);
  assert.equal(parseSession("{not json", 1000), null);
  assert.equal(parseSession(JSON.stringify({ token: "t" }), 1000), null);
  assert.equal(parseSession(null, 1000), null);
});
