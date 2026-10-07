import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import {
  getPageUrl,
  getSeoMetadata,
  getStructuredData,
  SITE_NAME,
  SOCIAL_IMAGE_URL,
  withSiteName
} from "../src/seo.js";

const frontendRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const distRoot = resolve(frontendRoot, "dist");
const baseHtml = await readFile(resolve(distRoot, "index.html"), "utf8");

const routes = [
  { name: "convert", path: "/convert", params: {}, query: {} },
  { name: "pdf-tool", path: "/tools/merge", params: { tool: "merge" }, query: {} },
  { name: "pdf-tool", path: "/tools/split", params: { tool: "split" }, query: {} },
  { name: "pdf-tool", path: "/tools/compress", params: { tool: "compress" }, query: {} },
  { name: "pdf-tool", path: "/tools/rotate", params: { tool: "rotate" }, query: {} },
  {
    name: "pdf-tool",
    path: "/tools/delete-pages",
    params: { tool: "delete-pages" },
    query: {}
  },
  { name: "ocr-pdf", path: "/tools/ocr-pdf", params: {}, query: {} },
  ...[
    "pdf-to-jpg",
    "jpg-to-pdf",
    "png-to-pdf",
    "images-to-pdf",
    "word-to-pdf",
    "excel-to-pdf",
    "pdf-to-word",
    "pdf-to-excel",
    "pdf-to-csv"
  ].map((tool) => ({
    name: "conversion-tool",
    path: `/tools/${tool}`,
    params: { tool },
    query: {}
  }))
];

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function replaceMeta(html, attribute, key, content) {
  const escapedKey = key.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = new RegExp(
    `<meta\\s+([^>]*${attribute}=["']${escapedKey}["'][^>]*)>`,
    "i"
  );

  return html.replace(pattern, (tag) =>
    tag.replace(/content=(["'])(.*?)\1/i, `content="${escapeHtml(content)}"`)
  );
}

function renderRoute(route) {
  const metadata = getSeoMetadata(route);
  const title = withSiteName(metadata.title);
  const pageUrl = getPageUrl(route);
  const schema = JSON.stringify(getStructuredData(route), null, 2).replaceAll("<", "\\u003c");

  let html = baseHtml
    .replace(/<title>[\s\S]*?<\/title>/i, `<title>${escapeHtml(title)}</title>`)
    .replace(
      /<link\s+rel=["']canonical["']\s+href=["'][^"']*["']\s*\/?>/i,
      `<link rel="canonical" href="${escapeHtml(pageUrl)}" />`
    )
    .replace(
      /<script id="upgradepdf-structured-data" type="application\/ld\+json">[\s\S]*?<\/script>/i,
      `<script id="upgradepdf-structured-data" type="application/ld+json">\n${schema}\n    </script>`
    );

  for (const [attribute, key, content] of [
    ["name", "description", metadata.description],
    ["property", "og:title", title],
    ["property", "og:description", metadata.description],
    ["property", "og:url", pageUrl],
    ["property", "og:image", SOCIAL_IMAGE_URL],
    ["name", "twitter:title", title],
    ["name", "twitter:description", metadata.description],
    ["name", "twitter:image", SOCIAL_IMAGE_URL]
  ]) {
    html = replaceMeta(html, attribute, key, content);
  }

  const fallback = `<noscript><main><h1>${escapeHtml(title)}</h1><p>${escapeHtml(
    metadata.description
  )}</p><p><a href="${escapeHtml(pageUrl)}">Use ${escapeHtml(
    SITE_NAME
  )}</a></p></main></noscript>`;

  return html.replace('<div id="app"></div>', `<div id="app"></div>\n    ${fallback}`);
}

for (const route of routes) {
  const outputPath = resolve(distRoot, `${route.path.slice(1)}.html`);
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, renderRoute(route), "utf8");
}

await copyFile(resolve(frontendRoot, "src/assets/logo.jpg"), resolve(distRoot, "og-image.jpg"));

console.log(`Generated ${routes.length} crawlable route pages and the social preview image.`);
