import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import {
  getPageUrl,
  getSeoMetadata,
  getStructuredData,
  SOCIAL_IMAGE_URL,
  withSiteName
} from "../src/seo.js";
import { countSeoWords, getSeoContent } from "../src/data/seoContent.js";

const frontendRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const distRoot = resolve(frontendRoot, "dist");
const baseHtml = await readFile(resolve(distRoot, "index.html"), "utf8");

const routes = [
  { name: "home", path: "/", params: {}, query: {} },
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
  {
    name: "pdf-tool",
    path: "/tools/reorder-pages",
    params: { tool: "reorder-pages" },
    query: {}
  },
  { name: "ocr-pdf", path: "/tools/ocr-pdf", params: {}, query: {} },
  { name: "ocr-pdf", path: "/ocr", params: {}, query: {} },
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

function getContentKey(route) {
  if (route.name === "home") return "home";
  if (route.name === "convert") return route.query.type || "convert";
  if (route.name === "ocr-pdf") return "ocr-pdf";
  return route.params.tool;
}

function renderList(tag, items) {
  return `<${tag}>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</${tag}>`;
}

function renderSeoContent(route) {
  const key = getContentKey(route);
  const content = getSeoContent(key);
  const wordCount = countSeoWords(content);

  if (wordCount < 250 || wordCount > 450) {
    throw new Error(`${key} SEO copy must contain 250-450 words; found ${wordCount}.`);
  }

  return `<section class="seo-content" aria-labelledby="${escapeHtml(key)}-seo-heading">
      <div class="seo-content__intro"><p class="seo-content__eyebrow">UpgradePDF guide</p><h2 id="${escapeHtml(key)}-seo-heading">${escapeHtml(content.heading)}</h2></div>
      <div class="seo-content__grid">
        <article class="seo-content__about"><h2>About the Tool</h2>${content.about.map((paragraph) => `<p>${escapeHtml(paragraph)}</p>`).join("")}</article>
        <article><h2>How to Use</h2>${renderList("ol", content.steps)}</article>
        <article><h2>Key Benefits</h2>${renderList("ul", content.benefits)}</article>
        <article><h2>Common Use Cases</h2>${renderList("ul", content.useCases)}</article>
      </div>
      <section class="seo-content__faqs" aria-label="Frequently asked questions"><h2>Frequently Asked Questions</h2><div class="seo-content__faq-grid">${content.faqs.map((faq) => `<article><h3>${escapeHtml(faq.question)}</h3><p>${escapeHtml(faq.answer)}</p></article>`).join("")}</div></section>
      <nav class="seo-content__related" aria-label="Related PDF tools"><h2>Related PDF Tools</h2><div>${content.related.map((link) => `<a href="${escapeHtml(link.path)}">${escapeHtml(link.label)}</a>`).join("")}</div></nav>
    </section>`;
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

  const prerenderedContent = `<main data-prerendered-page="${escapeHtml(getContentKey(route))}">
      <header><h1>${escapeHtml(metadata.title)}</h1><p>${escapeHtml(metadata.description)}</p></header>
      ${renderSeoContent(route)}
    </main>`;

  return html.replace('<div id="app"></div>', `<div id="app">${prerenderedContent}</div>`);
}

for (const route of routes) {
  const outputPath = route.path === "/"
    ? resolve(distRoot, "index.html")
    : resolve(distRoot, `${route.path.slice(1)}.html`);
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, renderRoute(route), "utf8");
}

await copyFile(resolve(frontendRoot, "src/assets/logo.jpg"), resolve(distRoot, "og-image.jpg"));

console.log(`Generated ${routes.length} crawlable route pages and the social preview image.`);
