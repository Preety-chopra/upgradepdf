import assert from "node:assert/strict";
import test from "node:test";
import { getCompressionResult } from "../src/utils/compression.js";

const job = (input, output) => ({
  operation: "compress",
  status: "completed",
  input_size_bytes: input,
  output_size_bytes: output
});

test("compression results calculate savings from actual file sizes", () => {
  const result = getCompressionResult({ ...job(1000, 750), savings_percent: 0 });
  assert.equal(result.reduced, true);
  assert.equal(result.savings, "25% space saved");
});

test("a real reduction never displays as zero percent", () => {
  const result = getCompressionResult(job(1000000, 999999));
  assert.equal(result.reduced, true);
  assert.equal(result.savings, "<0.1% space saved");
});

test("unchanged or larger output is never described as compressed successfully", () => {
  for (const output of [1000, 1100]) {
    const result = getCompressionResult(job(1000, output));
    assert.equal(result.reduced, false);
    assert.equal(result.savings, "No size reduction");
    assert.equal(result.title, "PDF could not be reduced");
    assert.match(result.message, /stronger compression/);
  }
});

test("other operations, pending jobs, and unavailable sizes have no compression result", () => {
  for (const input of [
    null,
    { ...job(1000, 750), operation: "merge" },
    { ...job(1000, 750), status: "processing" },
    job(null, 750), job(1000, null), job(0, 0), job(1000, -1)
  ]) {
    assert.equal(getCompressionResult(input), null);
  }
});
