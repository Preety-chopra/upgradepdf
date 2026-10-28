<template>
  <section class="tool-page compare-page">
    <RouterLink to="/" class="back-link">← Back to tools</RouterLink>

    <div class="tool-layout">
      <div class="tool-panel">
        <p class="eyebrow">PDF tool</p>
        <h1>Compare PDF</h1>
        <p class="tool-description">
          Upload an original PDF and its newer version. We will create a side-by-side
          report and highlight every visible change in red.
        </p>

        <div class="privacy-note">
          Your files are processed in a secure, isolated environment and deleted
          automatically.
        </div>

        <div class="compare-upload-grid">
          <article class="compare-upload-card">
            <span class="compare-step">1</span>
            <div>
              <h2>Original PDF</h2>
              <p>The reference document before edits.</p>
            </div>
            <FileDropzone
              ref="referenceDropzone"
              title="Select original PDF"
              description="Drop the earlier or approved version here."
              button-text="Choose original PDF"
              @files-selected="referenceFiles = $event"
            />
          </article>

          <article class="compare-upload-card">
            <span class="compare-step">2</span>
            <div>
              <h2>New PDF</h2>
              <p>The revised document you want to check.</p>
            </div>
            <FileDropzone
              ref="revisedDropzone"
              title="Select new PDF"
              description="Drop the revised version here."
              button-text="Choose new PDF"
              @files-selected="revisedFiles = $event"
            />
          </article>
        </div>

        <div class="compare-actions">
          <button
            type="button"
            class="primary-btn"
            :disabled="isSubmitting || !referenceFile || !revisedFile"
            @click="submit"
          >
            {{ isSubmitting ? "Uploading..." : "Compare PDFs" }}
          </button>
          <button
            v-if="referenceFile || revisedFile"
            type="button"
            class="danger-btn"
            :disabled="isSubmitting"
            @click="clearFiles"
          >
            Clear files
          </button>
        </div>

        <div v-if="uploadProgress > 0 && uploadProgress < 100" class="progress-wrap">
          <div class="progress-label">
            <span>Uploading both PDFs</span>
            <span>{{ uploadProgress }}%</span>
          </div>
          <div class="progress-track">
            <div class="progress-bar" :style="{ width: `${uploadProgress}%` }"></div>
          </div>
        </div>

        <div
          v-if="job && ['pending', 'processing'].includes(job.status)"
          class="compact-job-status"
          role="status"
          aria-live="polite"
        >
          <span class="preview-spinner" aria-hidden="true"></span>
          <span>
            <strong>{{ job.status === "pending" ? "Waiting to start" : "Comparing your PDFs" }}</strong>
            <small>Pages are being aligned and checked for visible differences.</small>
          </span>
        </div>

        <section v-if="job?.status === 'completed'" class="comparison-result" aria-live="polite">
          <div class="comparison-result-heading">
            <div>
              <p class="eyebrow">Comparison complete</p>
              <h2>{{ resultHeading }}</h2>
              <p>{{ resultDescription }}</p>
            </div>
            <a class="primary-btn" :href="downloadUrl" download>
              Download comparison report
            </a>
          </div>

          <dl v-if="job.comparison" class="comparison-stats">
            <div>
              <dt>Pages checked</dt>
              <dd>{{ job.comparison.pages_compared }}</dd>
            </div>
            <div>
              <dt>Changed</dt>
              <dd>{{ job.comparison.changed_pages }}</dd>
            </div>
            <div>
              <dt>Added</dt>
              <dd>{{ job.comparison.added_pages }}</dd>
            </div>
            <div>
              <dt>Removed</dt>
              <dd>{{ job.comparison.removed_pages }}</dd>
            </div>
            <div>
              <dt>Unchanged</dt>
              <dd>{{ job.comparison.unchanged_pages }}</dd>
            </div>
          </dl>

          <p class="comparison-legend">
            <span aria-hidden="true"></span>
            Red areas in the downloaded report mark visible differences in the new PDF.
          </p>
        </section>

        <p v-if="job?.status === 'failed'" class="error-box">
          {{ job.error_message || "Comparison failed. Please try again." }}
        </p>
        <p v-if="errorMessage" class="error-box">{{ errorMessage }}</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from "vue";

import FileDropzone from "../components/FileDropzone.vue";
import { buildAbsoluteUrl, getJob, submitCompare } from "../services/api";

const referenceFiles = ref([]);
const revisedFiles = ref([]);
const referenceDropzone = ref(null);
const revisedDropzone = ref(null);
const isSubmitting = ref(false);
const uploadProgress = ref(0);
const errorMessage = ref("");
const job = ref(null);
const pollingTimer = ref(null);

const referenceFile = computed(() => referenceFiles.value[0] || null);
const revisedFile = computed(() => revisedFiles.value[0] || null);
const downloadUrl = computed(() => buildAbsoluteUrl(job.value?.download_url));
const totalDifferences = computed(() => {
  const summary = job.value?.comparison;
  return summary
    ? summary.changed_pages + summary.added_pages + summary.removed_pages
    : null;
});
const resultHeading = computed(() => {
  if (totalDifferences.value === 0) {
    return "No visible differences found";
  }
  if (totalDifferences.value === null) {
    return "Your comparison report is ready";
  }
  return `${totalDifferences.value} changed page${totalDifferences.value === 1 ? "" : "s"} found`;
});
const resultDescription = computed(() => {
  return totalDifferences.value === 0
    ? "The rendered pages match at the comparison resolution."
    : "Review the highlighted changes in the downloadable side-by-side report.";
});

onBeforeUnmount(stopPolling);

function handleUploadProgress(progressEvent) {
  if (progressEvent.total) {
    uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total);
  }
}

async function submit() {
  if (!referenceFile.value || !revisedFile.value) {
    return;
  }

  errorMessage.value = "";
  job.value = null;
  isSubmitting.value = true;
  uploadProgress.value = 0;

  try {
    const response = await submitCompare(
      referenceFile.value,
      revisedFile.value,
      handleUploadProgress
    );
    uploadProgress.value = 100;
    if (!response?.job_id) {
      throw new Error("Job ID not received from server.");
    }
    await loadJob(response.job_id);
    startPolling(response.job_id);
  } catch (error) {
    errorMessage.value =
      error?.response?.data?.detail || error?.message || "Could not compare these PDFs.";
  } finally {
    isSubmitting.value = false;
  }
}

async function loadJob(jobId) {
  job.value = await getJob(jobId);
}

function startPolling(jobId) {
  stopPolling();
  pollingTimer.value = window.setInterval(async () => {
    try {
      await loadJob(jobId);
      if (["completed", "failed", "purged"].includes(job.value?.status)) {
        stopPolling();
      }
    } catch {
      stopPolling();
      errorMessage.value = "Could not refresh comparison status.";
    }
  }, 2000);
}

function stopPolling() {
  if (pollingTimer.value) {
    window.clearInterval(pollingTimer.value);
    pollingTimer.value = null;
  }
}

function clearFiles() {
  referenceDropzone.value?.clearFiles();
  revisedDropzone.value?.clearFiles();
  job.value = null;
  errorMessage.value = "";
  uploadProgress.value = 0;
  stopPolling();
}
</script>

<style scoped>
.compare-upload-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
  margin-top: 22px;
}

.compare-upload-card {
  position: relative;
  min-width: 0;
  padding: 22px;
  border: 1px solid var(--border);
  border-radius: 24px;
  background: #ffffff;
}

.compare-upload-card > div:first-of-type {
  padding-left: 46px;
}

.compare-upload-card h2,
.comparison-result h2 {
  margin: 0 0 6px;
}

.compare-upload-card p,
.comparison-result p {
  margin: 0;
  color: var(--muted);
  line-height: 1.5;
}

.compare-step {
  position: absolute;
  top: 20px;
  left: 20px;
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #eff6ff;
  color: #2563eb;
  font-weight: 900;
}

.compare-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin: 20px 0;
}

.compare-actions .primary-btn {
  min-width: 220px;
}

.comparison-result {
  margin-top: 22px;
  padding: 24px;
  border: 1px solid #bbf7d0;
  border-radius: 24px;
  background: linear-gradient(135deg, #f0fdf4, #ffffff);
}

.comparison-result-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.comparison-result-heading .primary-btn {
  flex: 0 0 auto;
  text-decoration: none;
}

.comparison-stats {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  margin: 22px 0;
}

.comparison-stats div {
  padding: 14px;
  border: 1px solid #dcfce7;
  border-radius: 16px;
  background: #ffffff;
}

.comparison-stats dt {
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
}

.comparison-stats dd {
  margin: 5px 0 0;
  font-size: 25px;
  font-weight: 900;
}

.comparison-legend {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 14px;
}

.comparison-legend span {
  width: 16px;
  height: 16px;
  border-radius: 5px;
  background: rgba(239, 68, 68, 0.55);
}

@media (max-width: 760px) {
  .compare-upload-grid,
  .comparison-stats {
    grid-template-columns: 1fr;
  }

  .compare-actions,
  .comparison-result-heading {
    align-items: stretch;
    flex-direction: column;
  }

  .compare-actions .primary-btn,
  .comparison-result-heading .primary-btn {
    width: 100%;
  }
}
</style>
