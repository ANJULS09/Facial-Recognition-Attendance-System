import assert from "node:assert/strict";
import test from "node:test";

import { bestMatch, euclidean, normalizeName } from "../public/js/matching.js";

const sample = (name, ...descriptor) => ({ name, descriptor });

test("euclidean distance", () => {
  assert.equal(euclidean([0, 0], [3, 4]), 5);
  assert.equal(euclidean([1, 2, 3], [1, 2, 3]), 0);
});

test("picks the closest enrolled face", () => {
  const samples = [sample("A", 0, 0), sample("B", 1, 0), sample("C", 5, 5)];
  const { name, distance } = bestMatch(samples, [0.9, 0]);
  assert.equal(name, "B");
  assert.ok(Math.abs(distance - 0.1) < 1e-9);
});

test("several photos of one person: the nearest photo wins", () => {
  const samples = [sample("A", 0, 0), sample("A", 10, 0), sample("B", 5, 0)];
  assert.equal(bestMatch(samples, [9.8, 0]).name, "A");
});

test("returns null name outside tolerance but still reports the distance", () => {
  const result = bestMatch([sample("A", 0, 0)], [3, 4], 0.6);
  assert.equal(result.name, null);
  assert.equal(result.distance, 5);
});

test("tolerance is inclusive", () => {
  assert.equal(bestMatch([sample("A", 0, 0)], [0.6, 0], 0.6).name, "A");
});

test("nobody enrolled", () => {
  assert.deepEqual(bestMatch([], [1, 1]), { name: null, distance: null });
});

test("normalizeName trims, collapses spaces and uppercases", () => {
  assert.equal(normalizeName("  jane   doe "), "JANE DOE");
  assert.equal(normalizeName("   "), "");
});
