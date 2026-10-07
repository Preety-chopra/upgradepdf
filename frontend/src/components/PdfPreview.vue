<template>
  <div v-if="file" class="pdf-preview">
    <div class="preview-header">
      <div class="preview-file-details">
        <span class="preview-file-icon" aria-hidden="true">PDF</span>

        <div>
          <p class="preview-kicker">Document preview</p>
          <h3>{{ file.name }}</h3>
          <p class="muted-text">
            {{ pageCount ? `${pageCount} page${pageCount > 1 ? "s" : ""}` : "Preparing preview" }}
          </p>
        </div>
      </div>

      <span v-if="pageCount" class="preview-ready-badge">Ready to review</span>
    </div>

    <div v-if="loading" class="preview-loading">
      <span class="preview-spinner" aria-hidden="true"></span>
      <span>
        <strong>Preparing your preview</strong>
        <small>Rendering pages securely in your browser…</small>
      </span>
    </div>

    <p v-if="errorMessage" class="error-box">
      {{ errorMessage }}
    </p>

    <div v-if="pdfDocument" class="preview-layout">
      <aside class="thumbnail-panel">
        <button
          v-for="pageNumber in pageNumbers"
          :key="pageNumber"
          type="button"
          class="thumbnail-item"
          :class="{
            active: pageNumber === currentPage,
            selected: selectedPages.includes(pageNumber)
          }"
          @click="goToPage(pageNumber)"
        >
          <canvas :ref="(el) => setThumbnailRef(el, pageNumber)"></canvas>

          <div class="thumbnail-footer">
            <span>Page {{ pageNumber }}</span>

            <input
              v-if="selectable"
              type="checkbox"
              :checked="selectedPages.includes(pageNumber)"
              @click.stop
              @change="togglePage(pageNumber)"
            />
          </div>
        </button>
      </aside>

      <section class="main-preview-panel">
        <div class="preview-toolbar">
          <div class="page-controls">
            <button
              type="button"
              class="preview-tool-btn"
              :disabled="currentPage <= 1"
              aria-label="Previous page"
              title="Previous page"
              @click="previousPage"
            >
              <span aria-hidden="true">←</span>
            </button>

            <span class="page-indicator">
              <strong>{{ currentPage }}</strong>
              <span>of {{ pageCount }}</span>
            </span>

            <button
              type="button"
              class="preview-tool-btn"
              :disabled="currentPage >= pageCount"
              aria-label="Next page"
              title="Next page"
              @click="nextPage"
            >
              <span aria-hidden="true">→</span>
            </button>
          </div>

          <div class="preview-actions" aria-label="Zoom controls">
            <button
              type="button"
              class="preview-tool-btn"
              :disabled="scale <= 0.6"
              aria-label="Zoom out"
              title="Zoom out"
              @click="zoomOut"
            >
              <span aria-hidden="true">−</span>
            </button>
            <span class="zoom-label">{{ Math.round(scale * 100) }}%</span>
            <button
              type="button"
              class="preview-tool-btn"
              :disabled="scale >= 2.5"
              aria-label="Zoom in"
              title="Zoom in"
              @click="zoomIn"
            >
              <span aria-hidden="true">+</span>
            </button>
          </div>
        </div>

        <div class="canvas-wrap">
          <canvas ref="mainCanvas"></canvas>
        </div>

        <div v-if="selectable" class="selection-box">
          <div>
            <strong>Selected pages</strong>
            <p>
              {{ selectedPagesText || "No pages selected yet." }}
            </p>
          </div>

          <div class="selection-actions">
            <button type="button" class="secondary-btn" @click="selectAllPages">
              Select all
            </button>

            <button type="button" class="secondary-btn" @click="clearSelection">
              Clear
            </button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, markRaw, nextTick, ref, shallowRef, watch } from "vue";
import * as pdfjsLib from "pdfjs-dist/legacy/build/pdf.mjs";
import pdfWorkerUrl from "pdfjs-dist/build/pdf.worker.mjs?url";

// Bust responses cached before Nginx served .mjs files as JavaScript.
pdfjsLib.GlobalWorkerOptions.workerSrc = `${pdfWorkerUrl}?module=1`;

const props = defineProps({
  file: {
    type: File,
    default: null
  },
  selectable: {
    type: Boolean,
    default: false
  },
  modelValue: {
    type: String,
    default: ""
  }
});

const emit = defineEmits(["update:modelValue", "page-count"]);

const pdfDocument = shallowRef(null);
const loading = ref(false);
const errorMessage = ref("");
const pageCount = ref(0);
const currentPage = ref(1);
const scale = ref(1.2);
const selectedPages = ref([]);
const mainCanvas = ref(null);
const thumbnailRefs = ref({});

const pageNumbers = computed(() => {
  return Array.from({ length: pageCount.value }, (_, index) => index + 1);
});

const selectedPagesText = computed(() => {
  return selectedPages.value.join(",");
});

watch(
  () => props.file,
  async (newFile) => {
    resetPreview();

    if (newFile) {
      await loadPdf(newFile);
    }
  },
  { immediate: true }
);

watch(selectedPages, () => {
  emit("update:modelValue", selectedPagesText.value);
});

watch(scale, async () => {
  if (pdfDocument.value) {
    await renderMainPage();
  }
});

async function loadPdf(file) {
  loading.value = true;
  errorMessage.value = "";

  try {
    const arrayBuffer = await file.arrayBuffer();

    const loadingTask = pdfjsLib.getDocument({
      data: arrayBuffer
    });

    const loadedPdf = await loadingTask.promise;

    pdfDocument.value = markRaw(loadedPdf);
    pageCount.value = loadedPdf.numPages;
    currentPage.value = 1;

    emit("page-count", pageCount.value);

    await nextTick();

    await renderMainPage();
    await renderThumbnails();
  } catch (error) {
    console.error("PDF preview load failed:", error);

    errorMessage.value =
        error?.message ||
        "Could not load PDF preview. Please try another PDF file.";
  } finally {
    loading.value = false;
  }
}

async function renderMainPage() {
  if (!pdfDocument.value || !mainCanvas.value) {
    return;
  }

  const page = await pdfDocument.value.getPage(currentPage.value);
  const viewport = page.getViewport({ scale: scale.value });

  const canvas = mainCanvas.value;
  const context = canvas.getContext("2d");

  canvas.width = viewport.width;
  canvas.height = viewport.height;

  await page.render({
    canvasContext: context,
    viewport
  }).promise;
}

async function renderThumbnails() {
  if (!pdfDocument.value) {
    return;
  }

  for (const pageNumber of pageNumbers.value) {
    await renderThumbnail(pageNumber);
  }
}

async function renderThumbnail(pageNumber) {
  const canvas = thumbnailRefs.value[pageNumber];

  if (!canvas || !pdfDocument.value) {
    return;
  }

  const page = await pdfDocument.value.getPage(pageNumber);
  const viewport = page.getViewport({ scale: 0.18 });

  const context = canvas.getContext("2d");

  canvas.width = viewport.width;
  canvas.height = viewport.height;

  await page.render({
    canvasContext: context,
    viewport
  }).promise;
}

function setThumbnailRef(el, pageNumber) {
  if (el) {
    thumbnailRefs.value[pageNumber] = el;
  }
}

async function goToPage(pageNumber) {
  currentPage.value = pageNumber;
  await renderMainPage();
}

async function previousPage() {
  if (currentPage.value > 1) {
    currentPage.value -= 1;
    await renderMainPage();
  }
}

async function nextPage() {
  if (currentPage.value < pageCount.value) {
    currentPage.value += 1;
    await renderMainPage();
  }
}

function zoomIn() {
  if (scale.value < 2.5) {
    scale.value = Number((scale.value + 0.2).toFixed(1));
  }
}

function zoomOut() {
  if (scale.value > 0.6) {
    scale.value = Number((scale.value - 0.2).toFixed(1));
  }
}

function togglePage(pageNumber) {
  if (selectedPages.value.includes(pageNumber)) {
    selectedPages.value = selectedPages.value.filter((page) => page !== pageNumber);
  } else {
    selectedPages.value = [...selectedPages.value, pageNumber].sort((a, b) => a - b);
  }
}

function selectAllPages() {
  selectedPages.value = pageNumbers.value;
}

function clearSelection() {
  selectedPages.value = [];
}

function resetPreview() {
  pdfDocument.value = null;
  loading.value = false;
  errorMessage.value = "";
  pageCount.value = 0;
  currentPage.value = 1;
  selectedPages.value = [];
  thumbnailRefs.value = {};
  emit("page-count", 0);
}
</script>
