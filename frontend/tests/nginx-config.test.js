import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

test("serves ES modules with a JavaScript MIME type", async () => {
  const config = await readFile(new URL("../nginx.conf", import.meta.url), "utf8");

  assert.match(config, /location\s+~\*\s+\\\.mjs\$/);
  assert.match(config, /default_type\s+application\/javascript;/);
});

test("invalidates the worker response cached with the old MIME type", async () => {
  const component = await readFile(
    new URL("../src/components/PdfPreview.vue", import.meta.url),
    "utf8"
  );

  assert.match(component, /workerSrc\s*=\s*`\$\{pdfWorkerUrl\}\?module=1`/);
});

test("serves generated route HTML before the SPA fallback", async () => {
  const config = await readFile(new URL("../nginx.conf", import.meta.url), "utf8");

  assert.match(config, /try_files\s+\$uri\s+\$uri\.html\s+\$uri\/\s+\/index\.html;/);
});
