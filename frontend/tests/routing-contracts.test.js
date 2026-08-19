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
