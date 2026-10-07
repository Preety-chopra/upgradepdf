import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const readSource = (relativePath) =>
  readFile(new URL(`../${relativePath}`, import.meta.url), 'utf8');


test('conversion dashboard route renders the conversion page', async () => {
  const router = await readSource('src/router/index.js');
  assert.match(router, /path:\s*["']\/convert["']/);
  assert.match(router, /name:\s*["']convert["'][\s\S]*component:\s*ConversionTools/);
  assert.match(router, /images-to-pdf/);
});


test('dashboard conversion links use canonical tool URLs that map to implemented tools', async () => {
  const [home, conversionPage] = await Promise.all([
    readSource('src/views/HomeView.vue'),
    readSource('src/pages/ConversionTools.vue')
  ]);

  const dashboardTypes = [...home.matchAll(/to="\/tools\/([^"]+)"/g)]
    .map((match) => match[1])
    .filter((type) => conversionPage.includes(`key: '${type}'`));
  const implementedTypes = new Set(
    [...conversionPage.matchAll(/key:\s*'([^']+)'/g)].map((match) => match[1])
  );

  assert.ok(dashboardTypes.length > 0);
  assert.doesNotMatch(home, /\/convert\?type=/);
  for (const type of dashboardTypes) {
    assert.ok(implementedTypes.has(type), `Dashboard conversion type is not implemented: ${type}`);
  }
});


test('conversion page initializes selection from the route query', async () => {
  const source = await readSource('src/pages/ConversionTools.vue');
  assert.match(source, /const route = useRoute\(\)/);
  assert.match(source, /selectedKey\.value = typeFromDashboard/);
  assert.doesNotMatch(source, /conversionType\.value/);
});


test('images-to-pdf accepts multiple images and uses the matching API endpoint', async () => {
  const source = await readSource('src/pages/ConversionTools.vue');
  const toolBlock = source.match(/key:\s*'images-to-pdf'[\s\S]*?\n\s*\}/)?.[0] || '';
  assert.match(toolBlock, /multiple:\s*true/);
  assert.match(toolBlock, /endpoint:\s*'\/api\/conversions\/images-to-pdf'/);
});


test('merge preview can switch between every selected PDF', async () => {
  const source = await readSource('src/views/PdfToolView.vue');

  assert.match(source, /v-model\.number="activePreviewIndex"/);
  assert.match(source, /v-for="\(file, index\) in files"/);
  assert.match(source, /files\.value\[activePreviewIndex\.value\]\s*\|\|\s*files\.value\[0\]/);
});


test('OCR UI consumes the backend language and progress field names', async () => {
  const source = await readSource('src/pages/OcrTools.vue');
  assert.match(source, /data\.supported/);
  assert.match(source, /data\.percent/);
  assert.doesNotMatch(source, /data\.progress/);
});


test('public routes update the meta title and description', async () => {
  const [router, seo, index, seoModule] = await Promise.all([
    readSource('src/router/index.js'),
    readSource('src/seo.js'),
    readSource('index.html'),
    import('../src/seo.js')
  ]);

  assert.match(router, /router\.afterEach/);
  assert.match(router, /applySeoMetadata\(to\)/);
  assert.match(seo, /document\.title\s*=/);
  assert.match(seo, /upsertMetaTag\("name", "description", metadata\.description\)/);
  assert.match(seo, /upsertMetaTag\("property", "og:title", title\)/);
  assert.match(seo, /upsertMetaTag\("property", "og:description", metadata\.description\)/);
  assert.match(seo, /upsertLinkTag\("canonical", pageUrl\)/);
  assert.match(seo, /upsertMetaTag\("property", "og:url", pageUrl\)/);
  assert.match(seo, /upsertMetaTag\("property", "og:image", SOCIAL_IMAGE_URL\)/);
  assert.match(seo, /upsertMetaTag\("name", "twitter:card", "summary_large_image"\)/);
  assert.match(seo, /upsertStructuredData\(getStructuredData\(route\)\)/);
  assert.match(seo, /"pdf-to-word"/);
  assert.match(seo, /"ocr-pdf"/);
  assert.match(index, /<meta\s+[\s\S]*?name="description"/);
  assert.match(index, /property="og:title"/);
  assert.match(index, /property="og:description"/);
  assert.match(index, /rel="canonical" href="https:\/\/upgradepdf\.com\/"/);
  assert.match(index, /property="og:image"/);
  assert.match(index, /property="og:image:width" content="4096"/);
  assert.match(index, /name="twitter:card"/);
  assert.match(index, /type="application\/ld\+json"/);
  assert.match(index, /<title>UpgradePDF – Free Online PDF Tools<\/title>/);

  const staticSchemaMatch = index.match(
    /<script id="upgradepdf-structured-data" type="application\/ld\+json">([\s\S]*?)<\/script>/
  );
  assert.ok(staticSchemaMatch, 'Homepage JSON-LD script is missing');
  const staticSchema = JSON.parse(staticSchemaMatch[1]);
  assert.deepEqual(
    staticSchema['@graph'].map((item) => item['@type']),
    ['Organization', 'WebSite', 'WebApplication']
  );

  const mergeMetadata = seoModule.getSeoMetadata({
    name: 'pdf-tool',
    params: { tool: 'merge' },
    query: {}
  });
  const conversionMetadata = seoModule.getSeoMetadata({
    name: 'convert',
    params: {},
    query: { type: 'pdf-to-word' }
  });

  assert.equal(mergeMetadata.title, 'Merge PDF Online – Combine PDF Files');
  assert.match(mergeMetadata.description, /Combine two or more PDF files/);
  assert.equal(conversionMetadata.title, 'PDF to Word Converter Online');

  const homeSchema = seoModule.getStructuredData({ name: 'home', params: {}, query: {} });
  const mergeSchema = seoModule.getStructuredData({
    name: 'pdf-tool',
    params: { tool: 'merge' },
    query: {}
  });

  assert.deepEqual(
    homeSchema['@graph'].map((item) => item['@type']),
    ['Organization', 'WebSite', 'WebApplication']
  );
  assert.deepEqual(
    mergeSchema['@graph'].map((item) => item['@type']),
    ['Organization', 'WebSite', 'WebPage', 'WebApplication', 'BreadcrumbList']
  );
  assert.equal(mergeSchema['@graph'][3].offers.price, '0');
  assert.equal(mergeSchema['@graph'][3].isAccessibleForFree, true);
  assert.equal(mergeSchema['@graph'][4].itemListElement.length, 2);
});

test('robots and sitemap expose every indexable public route', async () => {
  const [robots, sitemap] = await Promise.all([
    readSource('public/robots.txt'),
    readSource('public/sitemap.xml')
  ]);

  assert.match(robots, /User-agent:\s*\*/);
  assert.match(robots, /Allow:\s*\//);
  assert.match(robots, /Sitemap:\s*https:\/\/upgradepdf\.com\/sitemap\.xml/);

  for (const path of [
    '/',
    '/convert',
    '/tools/merge',
    '/tools/compress',
    '/tools/ocr-pdf',
    '/tools/pdf-to-jpg',
    '/tools/pdf-to-word'
  ]) {
    assert.match(sitemap, new RegExp(`<loc>https://upgradepdf\\.com${path}</loc>`));
  }
});
