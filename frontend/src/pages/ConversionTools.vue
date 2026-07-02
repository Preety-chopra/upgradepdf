<template>
  <main class="module-page">
    <section class="module-hero">
      <div>
        <p class="eyebrow">Module 6</p>
        <h1>Conversion Tools</h1>
        <p class="hero-copy">
          Convert PDFs, images, Word files, and Excel sheets from one clean workspace.
        </p>
      </div>

      <div class="hero-badge">
        <span>{{ selectedTool.badge }}</span>
        <strong>{{ selectedTool.title }}</strong>
      </div>
    </section>

    <section class="tool-layout">
      <aside class="tool-picker" aria-label="Conversion type">
        <button
          v-for="tool in tools"
          :key="tool.key"
          type="button"
          class="tool-option"
          :class="{ active: selectedKey === tool.key }"
          @click="selectTool(tool.key)"
        >
          <span class="tool-icon">{{ tool.icon }}</span>
          <span>
            <strong>{{ tool.title }}</strong>
            <small>{{ tool.description }}</small>
          </span>
        </button>
      </aside>

      <section class="workspace-card">
        <div class="workspace-header">
          <div>
            <p class="eyebrow">Selected conversion</p>
            <h2>{{ selectedTool.title }}</h2>
            <p>{{ selectedTool.longDescription }}</p>
          </div>
          <span class="format-chip">{{ selectedTool.output }}</span>
        </div>

        <div
          class="drop-zone"
          :class="{ dragging: isDragging, filled: files.length }"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="handleDrop"
        >
          <input
            ref="fileInput"
            class="hidden-input"
            type="file"
            :accept="selectedTool.accept"
            :multiple="selectedTool.multiple"
            @change="handleFileInput"
          />

          <div class="drop-icon">⬆</div>
          <h3>{{ files.length ? `${files.length} file(s) selected` : 'Drop file here' }}</h3>
          <p>
            {{ selectedTool.multiple ? 'You can select multiple JPG/PNG files.' : 'Select one file for this conversion.' }}
          </p>
          <button type="button" class="secondary-btn" @click="openFilePicker">
            Browse files
          </button>
        </div>

        <div v-if="files.length" class="file-list">
          <div v-for="file in files" :key="`${file.name}-${file.size}`" class="file-row">
            <div>
              <strong>{{ file.name }}</strong>
              <small>{{ formatBytes(file.size) }}</small>
            </div>
            <button type="button" class="text-btn" @click="removeFile(file)">Remove</button>
          </div>
        </div>

        <div v-if="selectedKey === 'pdf-to-word'" class="settings-panel">
          <label for="pdfWordMode">PDF to Word mode</label>
          <select id="pdfWordMode" v-model="pdfWordMode">
            <option value="auto">Auto recommended</option>
            <option value="layout">Layout mode for digital PDFs</option>
            <option value="image">Image mode for scanned PDFs</option>
            <option value="ocr">OCR editable text</option>
            <option value="text">Text only</option>
          </select>
          <p>
            Use <strong>Auto</strong> for mixed files. Use <strong>Image</strong> when the PDF is scanned and visual accuracy matters.
          </p>
        </div>

        <div class="action-row">
          <button type="button" class="primary-btn" :disabled="!canConvert" @click="convertFile">
            <span v-if="loading" class="spinner"></span>
            {{ loading ? 'Converting...' : 'Convert & Download' }}
          </button>
          <button type="button" class="ghost-btn" :disabled="loading && !files.length" @click="resetForm">
            Reset
          </button>
        </div>

        <div v-if="message" class="status-card success">
          {{ message }}
        </div>

        <div v-if="error" class="status-card error">
          {{ error }}
        </div>
      </section>
    </section>
  </main>
</template>

<script setup>
import { computed, ref } from 'vue';

const API_BASE = (
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  'http://localhost:8000'
).replace(/\/$/, '');

const tools = [
  {
    key: 'pdf-to-jpg',
    title: 'PDF to JPG',
    icon: '🖼️',
    badge: 'PDF pages',
    description: 'Export PDF pages as images',
    longDescription: 'Upload a PDF and download all pages as JPG images in a ZIP file.',
    accept: 'application/pdf,.pdf',
    output: 'ZIP / JPG',
    multiple: false,
    endpoint: '/api/conversions/pdf-to-jpg',
    defaultName: 'pdf-pages.zip'
  },
  {
    key: 'images-to-pdf',
    title: 'JPG / PNG to PDF',
    icon: '📄',
    badge: 'Image merge',
    description: 'Combine images into a PDF',
    longDescription: 'Upload one or more JPG/PNG images and generate a single PDF document.',
    accept: 'image/jpeg,image/png,.jpg,.jpeg,.png',
    output: 'PDF',
    multiple: true,
    endpoint: '/api/conversions/images-to-pdf',
    defaultName: 'images.pdf'
  },
  {
    key: 'word-to-pdf',
    title: 'Word to PDF',
    icon: '📝',
    badge: 'Office',
    description: 'Convert DOC/DOCX to PDF',
    longDescription: 'Upload a Word document and convert it to PDF using the backend LibreOffice converter.',
    accept: '.doc,.docx,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    output: 'PDF',
    multiple: false,
    endpoint: '/api/conversions/word-to-pdf',
    defaultName: 'word.pdf'
  },
  {
    key: 'excel-to-pdf',
    title: 'Excel to PDF',
    icon: '📊',
    badge: 'Spreadsheet',
    description: 'Convert XLS/XLSX to PDF',
    longDescription: 'Upload an Excel workbook and convert it into a PDF document.',
    accept: '.xls,.xlsx,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    output: 'PDF',
    multiple: false,
    endpoint: '/api/conversions/excel-to-pdf',
    defaultName: 'excel.pdf'
  },
  {
    key: 'pdf-to-word',
    title: 'PDF to Word',
    icon: '🔤',
    badge: 'DOCX',
    description: 'Create editable or visual DOCX',
    longDescription: 'Convert digital PDFs to editable Word files, or preserve scanned PDF pages visually using image mode.',
    accept: 'application/pdf,.pdf',
    output: 'DOCX',
    multiple: false,
    endpoint: '/api/conversions/pdf-to-word',
    defaultName: 'converted.docx'
  },
  {
    key: 'pdf-to-excel',
    title: 'PDF to Excel',
    icon: '📈',
    badge: 'Tables',
    description: 'Extract tables to XLSX',
    longDescription: 'Extract tables from a digital PDF and download the result as an Excel file.',
    accept: 'application/pdf,.pdf',
    output: 'XLSX',
    multiple: false,
    endpoint: '/api/conversions/pdf-to-data?format=xlsx',
    defaultName: 'tables.xlsx'
  },
  {
    key: 'pdf-to-csv',
    title: 'PDF to CSV',
    icon: '🧾',
    badge: 'Data',
    description: 'Extract tables to CSV',
    longDescription: 'Extract tabular data from a digital PDF and download it as a CSV file.',
    accept: 'application/pdf,.pdf',
    output: 'CSV',
    multiple: false,
    endpoint: '/api/conversions/pdf-to-data?format=csv',
    defaultName: 'tables.csv'
  }
];

const selectedKey = ref('pdf-to-jpg');
const files = ref([]);
const loading = ref(false);
const error = ref('');
const message = ref('');
const isDragging = ref(false);
const pdfWordMode = ref('auto');
const fileInput = ref(null);

const selectedTool = computed(() => tools.find((tool) => tool.key === selectedKey.value) || tools[0]);
const canConvert = computed(() => files.value.length > 0 && !loading.value);

function selectTool(key) {
  selectedKey.value = key;
  resetForm();
}

function openFilePicker() {
  fileInput.value?.click();
}

function handleFileInput(event) {
  setFiles(Array.from(event.target.files || []));
}

function handleDrop(event) {
  isDragging.value = false;
  setFiles(Array.from(event.dataTransfer.files || []));
}

function setFiles(incomingFiles) {
  error.value = '';
  message.value = '';

  if (!incomingFiles.length) {
    files.value = [];
    return;
  }

  files.value = selectedTool.value.multiple ? incomingFiles : [incomingFiles[0]];
}

function removeFile(targetFile) {
  files.value = files.value.filter((file) => file !== targetFile);
}

function resetForm() {
  files.value = [];
  error.value = '';
  message.value = '';
  loading.value = false;
  if (fileInput.value) fileInput.value.value = '';
}

function buildEndpoint() {
  let endpoint = selectedTool.value.endpoint;

  if (selectedKey.value === 'pdf-to-word') {
    const separator = endpoint.includes('?') ? '&' : '?';
    endpoint = `${endpoint}${separator}mode=${encodeURIComponent(pdfWordMode.value)}`;
  }

  return `${API_BASE}${endpoint}`;
}

async function convertFile() {
  if (!files.value.length) return;

  loading.value = true;
  error.value = '';
  message.value = '';

  try {
    const formData = new FormData();

    if (selectedTool.value.multiple) {
      files.value.forEach((file) => formData.append('files', file));
    } else {
      formData.append('file', files.value[0]);
    }

    const response = await fetch(buildEndpoint(), {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const details = await safeReadError(response);
      throw new Error(details || 'Conversion failed. Please try another file.');
    }

    const blob = await response.blob();
    const filename = getFilenameFromResponse(response) || selectedTool.value.defaultName;
    downloadBlob(blob, filename);
    message.value = `Done. Download started: ${filename}`;
  } catch (err) {
    error.value = err.message || 'Something went wrong during conversion.';
  } finally {
    loading.value = false;
  }
}

async function safeReadError(response) {
  try {
    const data = await response.json();
    return data.detail || data.message || '';
  } catch {
    return '';
  }
}

function getFilenameFromResponse(response) {
  const disposition = response.headers.get('content-disposition');
  if (!disposition) return '';

  const utfMatch = disposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utfMatch?.[1]) return decodeURIComponent(utfMatch[1]);

  const normalMatch = disposition.match(/filename="?([^";]+)"?/i);
  return normalMatch?.[1] || '';
}

function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

function formatBytes(bytes) {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}
</script>

<style scoped>
.module-page {
  min-height: 100vh;
  padding: 36px 24px 60px;
  background:
    radial-gradient(circle at top left, rgba(37, 99, 235, 0.13), transparent 32%),
    linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
  color: #0f172a;
}

.module-hero {
  max-width: 1180px;
  margin: 0 auto 26px;
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  gap: 18px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #2563eb;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.module-hero h1,
.workspace-header h2 {
  margin: 0;
  letter-spacing: -0.04em;
}

.module-hero h1 {
  font-size: clamp(34px, 6vw, 58px);
}

.hero-copy,
.workspace-header p,
.drop-zone p,
.settings-panel p {
  color: #64748b;
  line-height: 1.6;
}

.hero-badge {
  min-width: 230px;
  padding: 22px;
  border-radius: 24px;
  background: #ffffffcc;
  border: 1px solid #e2e8f0;
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
}

.hero-badge span {
  color: #64748b;
  font-size: 13px;
  font-weight: 700;
}

.hero-badge strong {
  font-size: 22px;
}

.tool-layout {
  max-width: 1180px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 330px minmax(0, 1fr);
  gap: 24px;
}

.tool-picker,
.workspace-card {
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid #e2e8f0;
  box-shadow: 0 22px 60px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(14px);
}

.tool-picker {
  border-radius: 26px;
  padding: 14px;
  display: grid;
  gap: 10px;
  align-self: start;
}

.tool-option {
  width: 100%;
  padding: 14px;
  border: 1px solid transparent;
  border-radius: 18px;
  background: transparent;
  display: grid;
  grid-template-columns: 44px 1fr;
  align-items: center;
  gap: 12px;
  text-align: left;
  color: #0f172a;
  cursor: pointer;
  transition: 0.2s ease;
}

.tool-option:hover,
.tool-option.active {
  background: #eff6ff;
  border-color: #bfdbfe;
}

.tool-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: #ffffff;
  display: grid;
  place-items: center;
  box-shadow: inset 0 0 0 1px #e2e8f0;
}

.tool-option strong,
.file-row strong {
  display: block;
}

.tool-option small,
.file-row small {
  color: #64748b;
  display: block;
  margin-top: 4px;
}

.workspace-card {
  border-radius: 30px;
  padding: clamp(20px, 4vw, 34px);
}

.workspace-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 22px;
}

.workspace-header h2 {
  font-size: 32px;
}

.format-chip {
  flex: 0 0 auto;
  padding: 8px 12px;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 13px;
  font-weight: 800;
}

.drop-zone {
  position: relative;
  border: 2px dashed #cbd5e1;
  border-radius: 26px;
  padding: 34px;
  text-align: center;
  background: #f8fafc;
  transition: 0.2s ease;
}

.drop-zone.dragging,
.drop-zone.filled {
  border-color: #2563eb;
  background: #eff6ff;
}

.hidden-input {
  display: none;
}

.drop-icon {
  width: 58px;
  height: 58px;
  margin: 0 auto 14px;
  border-radius: 18px;
  display: grid;
  place-items: center;
  background: #ffffff;
  color: #2563eb;
  font-size: 28px;
  box-shadow: 0 12px 26px rgba(37, 99, 235, 0.14);
}

.drop-zone h3 {
  margin: 0;
  font-size: 22px;
}

.file-list {
  margin-top: 18px;
  display: grid;
  gap: 10px;
}

.file-row {
  padding: 14px 16px;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: #ffffff;
}

.settings-panel {
  margin-top: 18px;
  padding: 16px;
  border-radius: 18px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  display: grid;
  gap: 8px;
}

.settings-panel label {
  font-weight: 800;
}

.settings-panel select {
  max-width: 360px;
}

.action-row {
  margin-top: 22px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.primary-btn,
.secondary-btn,
.ghost-btn,
.text-btn {
  border: none;
  cursor: pointer;
  font-weight: 800;
  transition: 0.2s ease;
}

.primary-btn,
.secondary-btn,
.ghost-btn {
  border-radius: 14px;
  padding: 12px 18px;
}

.primary-btn {
  background: #2563eb;
  color: #ffffff;
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.primary-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.secondary-btn {
  background: #0f172a;
  color: #ffffff;
}

.ghost-btn {
  background: #e2e8f0;
  color: #0f172a;
}

.text-btn {
  background: transparent;
  color: #2563eb;
}

.status-card {
  margin-top: 18px;
  padding: 14px 16px;
  border-radius: 16px;
  font-weight: 700;
}

.status-card.success {
  background: #ecfdf5;
  color: #047857;
}

.status-card.error {
  background: #fef2f2;
  color: #b91c1c;
}

select {
  width: 100%;
  padding: 11px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  background: #ffffff;
}

.spinner {
  width: 16px;
  height: 16px;
  border-radius: 999px;
  border: 2px solid rgba(255, 255, 255, 0.45);
  border-top-color: #ffffff;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 900px) {
  .module-hero,
  .workspace-header {
    flex-direction: column;
  }

  .tool-layout {
    grid-template-columns: 1fr;
  }

  .tool-picker {
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }
}
</style>
