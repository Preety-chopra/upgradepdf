<template>
  <main class="ocr-page">
    <section class="ocr-hero">
      <div>
        <h1>OCR Module</h1>
        <p>
          Upload a scanned PDF, run OCR in a separate worker, and download a searchable PDF with optional text export.
        </p>
      </div>
      <div class="status-summary">
        <span>Job status</span>
        <strong>{{ statusLabel }}</strong>
      </div>
    </section>

    <section class="ocr-layout">
      <section class="ocr-card upload-card">
        <div class="card-title-row">
          <div>
            <p class="eyebrow">Input</p>
            <h2>Scanned document</h2>
          </div>
          <span class="limit-pill">PDF</span>
        </div>

        <div
          class="drop-zone"
          :class="{ dragging: isDragging, filled: !!file }"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="handleDrop"
        >
          <input
            ref="fileInput"
            class="hidden-input"
            type="file"
            accept="application/pdf,.pdf"
            @change="handleFileInput"
          />
          <div class="drop-icon">🔍</div>
          <h3>{{ file ? file.name : 'Drop scanned PDF here' }}</h3>
          <p>{{ file ? formatBytes(file.size) : 'OCR works best on scanned or image-based PDFs.' }}</p>
          <button type="button" class="secondary-btn" @click="openFilePicker">
            Browse PDF
          </button>
        </div>

        <div class="settings-grid">
          <label class="field-block">
            <span>OCR language</span>
            <select v-model="language">
              <option v-for="lang in languages" :key="lang.code" :value="lang.code">
                {{ lang.label }}
              </option>
            </select>
          </label>

          <label class="check-row">
            <input v-model="exportText" type="checkbox" />
            <span>Also generate text export</span>
          </label>
        </div>

        <div class="action-row">
          <button type="button" class="primary-btn" :disabled="!canStart" @click="startOcr">
            <span v-if="starting" class="spinner"></span>
            {{ starting ? 'Submitting...' : 'Start OCR' }}
          </button>
          <button type="button" class="ghost-btn" :disabled="starting || running" @click="resetJob">
            Reset
          </button>
        </div>
      </section>

      <aside class="ocr-card progress-card">
        <div class="card-title-row">
          <div>
            <p class="eyebrow">Progress</p>
            <h2>{{ statusLabel }}</h2>
          </div>
          <span class="percent-ring">{{ progress }}%</span>
        </div>

        <div class="progress-track">
          <div class="progress-bar" :style="{ width: progress + '%' }"></div>
        </div>

        <div class="step-list">
          <div v-for="step in steps" :key="step.key" class="step-row" :class="stepClass(step)">
            <span class="step-dot"></span>
            <div>
              <strong>{{ step.title }}</strong>
              <small>{{ step.description }}</small>
            </div>
          </div>
        </div>

        <div v-if="jobId" class="job-box">
          <small>Job ID</small>
          <code>{{ jobId }}</code>
        </div>

        <div v-if="error" class="alert error">
          {{ error }}
        </div>

        <div v-if="status === 'completed'" class="download-panel">
          <button type="button" class="download-btn" @click="downloadFile('pdf')">
            Download searchable PDF
          </button>
          <button v-if="exportText" type="button" class="download-btn muted" @click="downloadFile('text')">
            Download text file
          </button>
        </div>
      </aside>
    </section>

    <SeoContentSection page-key="ocr-pdf" />
  </main>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';

import SeoContentSection from "../components/SeoContentSection.vue";

const API_BASE = (
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  ''
).replace(/\/$/, '');

const fallbackLanguages = [
  { code: 'eng', label: 'English' },
  { code: 'hin', label: 'Hindi' },
  { code: 'eng+hin', label: 'English + Hindi' },
  { code: 'osd', label: 'Orientation detection' }
];

const steps = [
  { key: 'queued', title: 'Queued', description: 'OCR worker has received the job.' },
  { key: 'running', title: 'Processing', description: 'OCRmyPDF and Tesseract are processing pages.' },
  { key: 'completed', title: 'Completed', description: 'Searchable PDF is ready to download.' }
];

const file = ref(null);
const language = ref('eng');
const languages = ref(fallbackLanguages);
const exportText = ref(true);
const starting = ref(false);
const isDragging = ref(false);
const jobId = ref('');
const status = ref('idle');
const progress = ref(0);
const error = ref('');
const fileInput = ref(null);
let pollTimer = null;

const running = computed(() => ['queued', 'running'].includes(status.value));
const canStart = computed(() => !!file.value && !starting.value && !running.value);
const statusLabel = computed(() => {
  const labels = {
    idle: 'Ready',
    queued: 'Queued',
    running: 'Running',
    completed: 'Completed',
    failed: 'Failed',
    timeout: 'Timed out'
  };
  return labels[status.value] || status.value;
});

onMounted(fetchLanguages);
onBeforeUnmount(stopPolling);

async function fetchLanguages() {
  try {
    const response = await fetch(`${API_BASE}/api/ocr/languages`);
    if (!response.ok) return;

    const data = await response.json();
    if (Array.isArray(data.supported)) {
      languages.value = data.supported.map((item) => {
        if (typeof item === 'string') return { code: item, label: item };
        return {
          code: item.code || item.value || item.lang,
          label: item.label || item.name || item.code || item.value || item.lang
        };
      }).filter((item) => item.code);
    }
  } catch {
    languages.value = fallbackLanguages;
  }
}

function openFilePicker() {
  fileInput.value?.click();
}

function handleFileInput(event) {
  const selected = event.target.files?.[0];
  if (selected) setFile(selected);
}

function handleDrop(event) {
  isDragging.value = false;
  const selected = event.dataTransfer.files?.[0];
  if (selected) setFile(selected);
}

function setFile(selected) {
  error.value = '';
  if (selected.type && selected.type !== 'application/pdf' && !selected.name.toLowerCase().endsWith('.pdf')) {
    error.value = 'Please upload a PDF file.';
    return;
  }
  file.value = selected;
}

async function startOcr() {
  if (!file.value) return;

  starting.value = true;
  error.value = '';
  progress.value = 0;
  status.value = 'queued';

  try {
    const formData = new FormData();
    formData.append('file', file.value);
    formData.append('language', language.value);
    formData.append('export_text', String(exportText.value));

    const response = await fetch(`${API_BASE}/api/ocr/jobs`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const details = await safeReadError(response);
      throw new Error(details || 'Failed to start OCR job.');
    }

    const data = await response.json();
    jobId.value = data.job_id || data.id;

    if (!jobId.value) {
      throw new Error('OCR job was created but no job id was returned.');
    }

    await pollStatus();
    stopPolling();
    pollTimer = window.setInterval(pollStatus, 3000);
  } catch (err) {
    error.value = err.message || 'Could not start OCR.';
    status.value = 'failed';
  } finally {
    starting.value = false;
  }
}

async function pollStatus() {
  if (!jobId.value) return;

  try {
    const response = await fetch(`${API_BASE}/api/ocr/jobs/${jobId.value}`);

    if (!response.ok) {
      const details = await safeReadError(response);
      throw new Error(details || 'Failed to fetch OCR status.');
    }

    const data = await response.json();
    status.value = data.status || status.value;
    progress.value = normalizeProgress(data.percent);

    if (data.error) {
      error.value = data.error;
    }

    if (['completed', 'failed', 'timeout'].includes(status.value)) {
      stopPolling();
      if (status.value === 'failed' && !error.value) error.value = 'OCR failed.';
      if (status.value === 'timeout' && !error.value) error.value = 'OCR timed out for this file.';
    }
  } catch (err) {
    error.value = err.message || 'Status check failed.';
    stopPolling();
  }
}

function normalizeProgress(value) {
  const numeric = Number(value || 0);
  if (Number.isNaN(numeric)) return 0;
  return Math.max(0, Math.min(100, Math.round(numeric)));
}

function stepClass(step) {
  const order = ['queued', 'running', 'completed'];
  const currentIndex = order.indexOf(status.value);
  const stepIndex = order.indexOf(step.key);

  return {
    active: status.value === step.key,
    done: currentIndex > stepIndex || status.value === 'completed',
    error: ['failed', 'timeout'].includes(status.value)
  };
}

function downloadFile(type) {
  if (!jobId.value) return;
  window.open(`${API_BASE}/api/ocr/jobs/${jobId.value}/download?file_type=${type}`, '_blank');
}

function resetJob() {
  stopPolling();
  file.value = null;
  jobId.value = '';
  status.value = 'idle';
  progress.value = 0;
  error.value = '';
  starting.value = false;
  if (fileInput.value) fileInput.value.value = '';
}

function stopPolling() {
  if (pollTimer) {
    window.clearInterval(pollTimer);
    pollTimer = null;
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

function formatBytes(bytes) {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}
</script>

<style scoped>
.ocr-page {
  min-height: 100vh;
  padding: 36px 24px 60px;
  background:
    radial-gradient(circle at top right, rgba(14, 165, 233, 0.15), transparent 30%),
    linear-gradient(180deg, #f8fafc 0%, #edf4f8 100%);
  color: #0f172a;
}

.ocr-hero {
  max-width: 1180px;
  margin: 0 auto 26px;
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  gap: 18px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #0891b2;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.ocr-hero h1 {
  margin: 0;
  font-size: clamp(34px, 6vw, 58px);
  letter-spacing: -0.04em;
}

.ocr-hero p,
.drop-zone p,
.step-row small {
  color: #64748b;
  line-height: 1.6;
}

.status-summary {
  min-width: 220px;
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

.status-summary span {
  color: #64748b;
  font-size: 13px;
  font-weight: 800;
}

.status-summary strong {
  font-size: 24px;
}

.ocr-layout {
  max-width: 1180px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(330px, 0.7fr);
  gap: 24px;
}

.ocr-card {
  border-radius: 30px;
  padding: clamp(20px, 4vw, 34px);
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #e2e8f0;
  box-shadow: 0 22px 60px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(14px);
}

.card-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 22px;
}

.card-title-row h2 {
  margin: 0;
  font-size: 30px;
  letter-spacing: -0.03em;
}

.limit-pill,
.percent-ring {
  flex: 0 0 auto;
  border-radius: 999px;
  font-weight: 900;
}

.limit-pill {
  padding: 8px 12px;
  background: #cffafe;
  color: #0e7490;
}

.percent-ring {
  width: 68px;
  height: 68px;
  display: grid;
  place-items: center;
  background: #ecfeff;
  color: #0e7490;
  border: 1px solid #a5f3fc;
}

.drop-zone {
  border: 2px dashed #cbd5e1;
  border-radius: 26px;
  padding: 34px;
  text-align: center;
  background: #f8fafc;
  transition: 0.2s ease;
}

.drop-zone.dragging,
.drop-zone.filled {
  border-color: #0891b2;
  background: #ecfeff;
}

.hidden-input {
  display: none;
}

.drop-icon {
  width: 62px;
  height: 62px;
  margin: 0 auto 14px;
  border-radius: 20px;
  display: grid;
  place-items: center;
  background: #ffffff;
  font-size: 30px;
  box-shadow: 0 12px 26px rgba(14, 165, 233, 0.14);
}

.drop-zone h3 {
  margin: 0;
  word-break: break-word;
}

.settings-grid {
  margin-top: 18px;
  display: grid;
  gap: 14px;
}

.field-block {
  display: grid;
  gap: 8px;
}

.field-block span,
.check-row span {
  font-weight: 800;
}

select {
  width: 100%;
  padding: 11px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  background: #ffffff;
}

.check-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px;
  border-radius: 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.check-row input {
  width: 18px;
  height: 18px;
}

.action-row,
.download-panel {
  margin-top: 22px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.primary-btn,
.secondary-btn,
.ghost-btn,
.download-btn {
  border: none;
  cursor: pointer;
  font-weight: 900;
  transition: 0.2s ease;
  border-radius: 14px;
  padding: 12px 18px;
}

.primary-btn {
  background: #0891b2;
  color: #ffffff;
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.primary-btn:disabled,
.ghost-btn:disabled {
  background: #94a3b8;
  color: #ffffff;
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

.progress-track {
  height: 14px;
  border-radius: 999px;
  background: #e2e8f0;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #06b6d4, #0891b2);
  transition: width 0.25s ease;
}

.step-list {
  margin-top: 22px;
  display: grid;
  gap: 14px;
}

.step-row {
  display: grid;
  grid-template-columns: 18px 1fr;
  gap: 12px;
  align-items: start;
}

.step-dot {
  width: 14px;
  height: 14px;
  margin-top: 3px;
  border-radius: 999px;
  background: #cbd5e1;
}

.step-row.active .step-dot {
  background: #0891b2;
  box-shadow: 0 0 0 6px rgba(8, 145, 178, 0.12);
}

.step-row.done .step-dot {
  background: #059669;
}

.step-row.error .step-dot {
  background: #dc2626;
}

.step-row strong,
.step-row small {
  display: block;
}

.job-box {
  margin-top: 22px;
  padding: 14px;
  border-radius: 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  display: grid;
  gap: 6px;
}

.job-box small {
  color: #64748b;
  font-weight: 800;
}

.job-box code {
  white-space: normal;
  word-break: break-all;
}

.alert {
  margin-top: 18px;
  padding: 14px 16px;
  border-radius: 16px;
  font-weight: 800;
}

.alert.error {
  background: #fef2f2;
  color: #b91c1c;
}

.download-btn {
  background: #059669;
  color: #ffffff;
}

.download-btn.muted {
  background: #e2e8f0;
  color: #0f172a;
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
  .ocr-hero,
  .card-title-row {
    flex-direction: column;
  }

  .ocr-layout {
    grid-template-columns: 1fr;
  }
}
</style>
