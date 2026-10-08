<template>
  <section class="tool-page">
    <RouterLink to="/" class="back-link">← Back to tools</RouterLink>

    <div class="tool-layout">
      <div class="tool-panel">
        <p class="eyebrow">PDF tool</p>
        <h1>{{ config.title }}</h1>
        <p class="tool-description">
          {{ config.description }}
        </p>

        <div class="privacy-note">
          Your files are processed in a secure, isolated environment and deleted
          automatically.
        </div>

        <FileDropzone
          :multiple="config.multiple"
          @files-selected="handleFilesSelected"
          @files-reordered="handleFilesReordered"
        />

        <div v-if="showPreview && tool !== 'reorder-pages'" class="preview-area">
          <div v-if="files.length > 1" class="preview-file-selector">
            <label for="preview-file">Preview file</label>
            <select id="preview-file" v-model.number="activePreviewIndex">
              <option
                v-for="(file, index) in files"
                :key="`${file.name}-${file.size}-${index}`"
                :value="index"
              >
                {{ index + 1 }}. {{ file.name }}
              </option>
            </select>
            <small>
              Previewing file {{ activePreviewIndex + 1 }} of {{ files.length }}.
              All selected files will still be merged in the listed order.
            </small>
          </div>

          <PdfPreview
            :file="previewFile"
            :selectable="isPageSelectionTool"
            v-model="selectedPagesFromPreview"
            @page-count="handlePageCount"
          />
        </div>

        <PdfPageOrganizer
          v-if="previewFile && tool === 'reorder-pages'"
          :file="previewFile"
          @order-change="handlePageOrderChange"
          @page-count="handlePageCount"
          @preview-error="handleOrganizerError"
        />

        <div v-if="tool === 'split' || tool === 'delete-pages'" class="form-group">
          <label for="pages">Pages</label>
          <input
            id="pages"
            v-model="pages"
            type="text"
            placeholder="Example: 1-3 or 1,4,6"
          />
          <small>
            You can type pages manually or select pages from the preview.
          </small>
        </div>

        <div v-if="tool === 'rotate'" class="form-group">
          <label for="rotate-pages">Pages</label>
          <input
            id="rotate-pages"
            v-model="pages"
            type="text"
            placeholder="all or 1,3,5"
          />
          <small>
            Use "all", type selected pages manually, or select pages from the preview.
          </small>
        </div>

        <div v-if="tool === 'rotate'" class="form-group">
          <label for="angle">Rotation angle</label>
          <select id="angle" v-model="angle">
            <option value="90">90 degrees</option>
            <option value="180">180 degrees</option>
            <option value="270">270 degrees</option>
            <option value="-90">-90 degrees</option>
          </select>
        </div>

        <fieldset v-if="tool === 'compress'" class="compression-options">
          <legend>Compression level</legend>

          <label
            v-for="option in compressionOptions"
            :key="option.value"
            class="compression-option"
            :class="{ selected: quality === option.value }"
          >
            <input v-model="quality" type="radio" :value="option.value" />
            <span>
              <strong>{{ option.label }}</strong>
              <small>{{ option.description }}</small>
            </span>
          </label>
        </fieldset>

        <div v-if="pageCount" class="page-count-note">
          Detected {{ pageCount }} page{{ pageCount > 1 ? "s" : "" }} in this PDF.
        </div>

        <div v-if="uploadProgress > 0 && uploadProgress < 100" class="progress-wrap">
          <div class="progress-label">
            <span>Uploading</span>
            <span>{{ uploadProgress }}%</span>
          </div>
          <div class="progress-track">
            <div class="progress-bar" :style="{ width: `${uploadProgress}%` }"></div>
          </div>
        </div>

        <button
          type="button"
          class="primary-btn full-width"
          :disabled="isSubmitDisabled"
          @click="submitTool"
        >
          {{ isSubmitting ? "Uploading..." : config.buttonText }}
        </button>

        <p v-if="errorMessage" class="error-box">
          {{ errorMessage }}
        </p>
      </div>

      <div class="result-panel">
        <JobStatus :job="job" />

        <div v-if="!job" class="empty-result">
          <h3>No job started yet</h3>
          <p>
            Upload your PDF file, preview pages, start processing, and the result
            will appear here.
          </p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import FileDropzone from "../components/FileDropzone.vue";
import JobStatus from "../components/JobStatus.vue";
import PdfPageOrganizer from "../components/PdfPageOrganizer.vue";
import PdfPreview from "../components/PdfPreview.vue";
import {
  getJob,
  submitCompress,
  submitDeletePages,
  submitMerge,
  submitReorderPages,
  submitRotate,
  submitSplit
} from "../services/api";

const route = useRoute();
const router = useRouter();

const files = ref([]);
const pages = ref("");
const selectedPagesFromPreview = ref("");
const angle = ref("90");
const quality = ref("balanced");
const isSubmitting = ref(false);
const uploadProgress = ref(0);
const errorMessage = ref("");
const job = ref(null);
const pollingTimer = ref(null);
const pageCount = ref(0);
const activePreviewIndex = ref(0);
const pageOrder = ref([]);
const organizerError = ref("");

const tool = computed(() => route.params.tool);

const toolConfigs = {
  compress: {
    title: "Compress PDF",
    description:
      "Reduce PDF file size while preserving text, links, forms, and page layout.",
    multiple: false,
    buttonText: "Compress PDF"
  },
  merge: {
    title: "Merge PDF",
    description: "Combine two or more PDF files into a single PDF document.",
    multiple: true,
    buttonText: "Merge PDF"
  },
  split: {
    title: "Split PDF",
    description: "Extract selected pages and save them as a new PDF.",
    multiple: false,
    buttonText: "Split PDF"
  },
  rotate: {
    title: "Rotate PDF",
    description: "Rotate all pages or selected pages by a chosen angle.",
    multiple: false,
    buttonText: "Rotate PDF"
  },
  "delete-pages": {
    title: "Delete Pages",
    description: "Remove selected pages and download the remaining PDF.",
    multiple: false,
    buttonText: "Delete Pages"
  },
  "reorder-pages": {
    title: "Reorder PDF Pages",
    description: "Arrange PDF pages visually, then export a new document in your chosen order.",
    multiple: false,
    buttonText: "Export Reordered PDF"
  }
};

const compressionOptions = [
  {
    value: "light",
    label: "Light",
    description: "Best visual quality with a smaller size reduction."
  },
  {
    value: "balanced",
    label: "Balanced",
    description: "Recommended for sharing, email, and everyday use."
  },
  {
    value: "strong",
    label: "Strong",
    description: "Smallest files with more image quality reduction."
  }
];

const config = computed(() => {
  return toolConfigs[tool.value] || toolConfigs.merge;
});

const previewFile = computed(() => {
  if (!files.value.length) {
    return null;
  }

  return files.value[activePreviewIndex.value] || files.value[0];
});

const showPreview = computed(() => {
  return Boolean(previewFile.value);
});

const isPageSelectionTool = computed(() => {
  return ["split", "rotate", "delete-pages"].includes(tool.value);
});

const isSubmitDisabled = computed(() => {
  if (isSubmitting.value) {
    return true;
  }

  if (tool.value === "merge") {
    return files.value.length < 2;
  }

  if (["split", "delete-pages"].includes(tool.value)) {
    return files.value.length < 1 || !pages.value.trim();
  }

  if (tool.value === "rotate") {
    return files.value.length < 1 || !pages.value.trim() || !angle.value;
  }

  if (tool.value === "compress") {
    return files.value.length < 1 || !quality.value;
  }

  if (tool.value === "reorder-pages") {
    return files.value.length < 1 || pageOrder.value.length < 1 || Boolean(organizerError.value);
  }

  return true;
});

watch(
  () => route.params.tool,
  (newTool) => {
    if (!toolConfigs[newTool]) {
      router.replace("/");
      return;
    }

    resetStateForTool(newTool);
  },
  { immediate: true }
);

watch(selectedPagesFromPreview, (value) => {
  if (!value) {
    return;
  }

  pages.value = value;
});

onBeforeUnmount(() => {
  stopPolling();
});

function resetStateForTool(newTool) {
  files.value = [];
  job.value = null;
  errorMessage.value = "";
  uploadProgress.value = 0;
  angle.value = "90";
  quality.value = "balanced";
  selectedPagesFromPreview.value = "";
  pageCount.value = 0;
  activePreviewIndex.value = 0;
  pageOrder.value = [];
  organizerError.value = "";
  pages.value = newTool === "rotate" ? "all" : "";
  stopPolling();
}

function handleFilesSelected(selectedFiles) {
  files.value = selectedFiles;
  errorMessage.value = "";
  job.value = null;
  selectedPagesFromPreview.value = "";
  pageCount.value = 0;
  activePreviewIndex.value = 0;
  pageOrder.value = [];
  organizerError.value = "";

  if (tool.value === "rotate") {
    pages.value = "all";
  } else {
    pages.value = "";
  }
}

function handleFilesReordered(reorderedFiles) {
  const activeFile = previewFile.value;
  files.value = reorderedFiles;

  const reorderedPreviewIndex = reorderedFiles.indexOf(activeFile);
  activePreviewIndex.value = reorderedPreviewIndex >= 0 ? reorderedPreviewIndex : 0;
}

function handlePageCount(count) {
  pageCount.value = count;
}

function handlePageOrderChange(order) {
  pageOrder.value = order;
}

function handleOrganizerError(message) {
  organizerError.value = message;
}

function handleUploadProgress(progressEvent) {
  if (!progressEvent.total) {
    return;
  }

  uploadProgress.value = Math.round(
    (progressEvent.loaded * 100) / progressEvent.total
  );
}

async function submitTool() {
  errorMessage.value = "";
  isSubmitting.value = true;
  uploadProgress.value = 0;
  job.value = null;

  try {
    let response;

    if (tool.value === "merge") {
      response = await submitMerge(files.value, handleUploadProgress);
    }

    if (tool.value === "compress") {
      response = await submitCompress(
        files.value[0],
        quality.value,
        handleUploadProgress
      );
    }

    if (tool.value === "split") {
      response = await submitSplit(files.value[0], pages.value, handleUploadProgress);
    }

    if (tool.value === "rotate") {
      response = await submitRotate(
        files.value[0],
        pages.value || "all",
        Number(angle.value),
        handleUploadProgress
      );
    }

    if (tool.value === "delete-pages") {
      response = await submitDeletePages(
        files.value[0],
        pages.value,
        handleUploadProgress
      );
    }

    if (tool.value === "reorder-pages") {
      response = await submitReorderPages(
        files.value[0],
        pageOrder.value,
        handleUploadProgress
      );
    }

    uploadProgress.value = 100;

    if (!response?.job_id) {
      throw new Error("Job ID not received from server.");
    }

    await loadJob(response.job_id);
    startPolling(response.job_id);
  } catch (error) {
    errorMessage.value =
      error?.response?.data?.detail ||
      error?.message ||
      "Something went wrong while processing your PDF.";
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
    } catch (error) {
      stopPolling();
      errorMessage.value = "Could not refresh job status.";
    }
  }, 2000);
}

function stopPolling() {
  if (pollingTimer.value) {
    window.clearInterval(pollingTimer.value);
    pollingTimer.value = null;
  }
}
</script>
