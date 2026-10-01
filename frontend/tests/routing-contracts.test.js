import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const readSource = (relativePath) =>
  readFile(new URL(`../${relativePath}`, import.meta.url), 'utf8');


test('conversion dashboard route renders the conversion page', async () => {
  const router = await readSource('src/router/index.js');
  assert.match(router, /path:\s*["']\/convert["']/);
  assert.match(router, /name:\s*["']convert["'][\s\S]*component:\s*ConversionTools/);
});


test('dashboard conversion query values map to implemented tools', async () => {
  const [home, conversionPage] = await Promise.all([
    readSource('src/views/HomeView.vue'),
    readSource('src/pages/ConversionTools.vue')
  ]);

  const dashboardTypes = [...home.matchAll(/to="\/convert\?type=([^"]+)"/g)].map((match) => match[1]);
  const implementedTypes = new Set(
    [...conversionPage.matchAll(/key:\s*'([^']+)'/g)].map((match) => match[1])
  );

  assert.ok(dashboardTypes.length > 0);
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
  assert.match(seo, /upsertStructuredData\(getStructuredData\(route\)\)/);
  assert.match(seo, /"pdf-to-word"/);
  assert.match(seo, /"ocr-pdf"/);
  assert.match(index, /<meta\s+[\s\S]*?name="description"/);
  assert.match(index, /property="og:title"/);
  assert.match(index, /property="og:description"/);
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
    ['WebPage', 'WebApplication', 'BreadcrumbList']
  );
  assert.equal(mergeSchema['@graph'][1].offers.price, '0');
  assert.equal(mergeSchema['@graph'][2].itemListElement.length, 2);
});
