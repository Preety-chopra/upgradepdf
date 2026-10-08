<template>
  <section v-if="file" class="page-organizer" aria-labelledby="page-organizer-title">
    <header class="page-organizer-header">
      <div>
        <p class="preview-kicker">Page organizer</p>
        <h3 id="page-organizer-title">Drag pages into the order you want</h3>
        <p class="muted-text">The number on each card is its original page number.</p>
      </div>
      <button
        v-if="pageOrder.length > 1"
        type="button"
        class="secondary-btn"
        :disabled="isOriginalOrder"
        @click="resetOrder"
      >
        Reset order
      </button>
    </header>

    <div v-if="loading" class="preview-loading">
      <span class="preview-spinner" aria-hidden="true"></span>
      <span>
        <strong>Preparing your pages</strong>
        <small>Rendering page thumbnails securely in your browser...</small>
      </span>
    </div>

    <p v-if="errorMessage" class="error-box" role="alert">{{ errorMessage }}</p>

    <ol v-if="pdfDocument" class="page-organizer-grid">
      <li
        v-for="(pageNumber, index) in pageOrder"
        :key="pageNumber"
        class="page-organizer-card"
        :class="{
          'page-organizer-card-dragging': draggedIndex === index,
          'page-organizer-card-drag-over': dragOverIndex === index && draggedIndex !== index
        }"
        draggable="true"
        @dragstart="handleDragStart($event, index)"
        @dragover.prevent="handleDragOver(index)"
        @drop.prevent="handleDrop(index)"
        @dragend="resetDragState"
      >
        <div class="page-organizer-position" aria-hidden="true">{{ index + 1 }}</div>
        <canvas :ref="(element) => setCanvasRef(element, pageNumber)"></canvas>
        <div class="page-organizer-card-footer">
          <span class="page-organizer-handle" aria-hidden="true">&#8942;&#8942;</span>
          <strong>Page {{ pageNumber }}</strong>
          <div class="page-organizer-actions">
            <button
              type="button"
              :disabled="index === 0"
              :aria-label="`Move page ${pageNumber} earlier`"
              @click="movePage(index, index - 1)"
            >&larr;</button>
            <button
              type="button"
              :disabled="index === pageOrder.length - 1"
              :aria-label="`Move page ${pageNumber} later`"
              @click="movePage(index, index + 1)"
            >&rarr;</button>
          </div>
        </div>
      </li>
    </ol>

    <p v-if="pdfDocument && !loading" class="page-organizer-summary" aria-live="polite">
      New page order: <strong>{{ pageOrder.join(", ") }}</strong>
    </p>
  </section>
</template>

<script setup>
import { computed, markRaw, nextTick, onBeforeUnmount, ref, shallowRef, watch } from "vue";
import * as pdfjsLib from "pdfjs-dist/legacy/build/pdf.mjs";
import pdfWorkerUrl from "pdfjs-dist/build/pdf.worker.mjs?url";

import { moveItem } from "../utils/fileOrder";

pdfjsLib.GlobalWorkerOptions.workerSrc = `${pdfWorkerUrl}?module=1`;

const props = defineProps({
  file: { type: File, default: null }
});
const emit = defineEmits(["order-change", "page-count", "preview-error"]);

const pdfDocument = shallowRef(null);
const loading = ref(false);
const errorMessage = ref("");
const pageOrder = ref([]);
const canvasRefs = ref({});
const draggedIndex = ref(null);
const dragOverIndex = ref(null);
let loadSequence = 0;

const isOriginalOrder = computed(() =>
  pageOrder.value.every((pageNumber, index) => pageNumber === index + 1)
);

watch(() => props.file, (file) => loadPdf(file), { immediate: true });

onBeforeUnmount(() => {
  loadSequence += 1;
  destroyPdfDocument();
});

async function loadPdf(file) {
  const currentSequence = ++loadSequence;
  destroyPdfDocument();
  loading.value = Boolean(file);
  errorMessage.value = "";
  pageOrder.value = [];
  canvasRefs.value = {};
  emit("order-change", []);
  emit("page-count", 0);
  emit("preview-error", "");

  if (!file) {
    loading.value = false;
    return;
  }

  try {
    const arrayBuffer = await file.arrayBuffer();
    const loadedPdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;

    if (currentSequence !== loadSequence) {
      await loadedPdf.destroy();
      return;
    }

    pdfDocument.value = markRaw(loadedPdf);
    pageOrder.value = Array.from({ length: loadedPdf.numPages }, (_, index) => index + 1);
    emit("page-count", loadedPdf.numPages);
    emitOrder();
    await nextTick();
    await renderThumbnails(currentSequence);
  } catch (error) {
    if (currentSequence !== loadSequence) return;
    console.error("PDF page organizer load failed:", error);
    errorMessage.value = error?.message || "Could not read this PDF. Please choose another file.";
    emit("preview-error", errorMessage.value);
  } finally {
    if (currentSequence === loadSequence) loading.value = false;
  }
}

async function renderThumbnails(sequence) {
  for (const pageNumber of pageOrder.value) {
    if (sequence !== loadSequence || !pdfDocument.value) return;
    const canvas = canvasRefs.value[pageNumber];
    if (!canvas) continue;

    const page = await pdfDocument.value.getPage(pageNumber);
    const baseViewport = page.getViewport({ scale: 1 });
    const viewport = page.getViewport({ scale: Math.min(0.32, 180 / baseViewport.width) });
    canvas.width = Math.ceil(viewport.width);
    canvas.height = Math.ceil(viewport.height);
    await page.render({ canvasContext: canvas.getContext("2d"), viewport }).promise;
  }
}

function setCanvasRef(element, pageNumber) {
  if (element) canvasRefs.value[pageNumber] = element;
}

function movePage(fromIndex, toIndex) {
  const reordered = moveItem(pageOrder.value, fromIndex, toIndex);
  if (reordered.every((pageNumber, index) => pageNumber === pageOrder.value[index])) return;
  pageOrder.value = reordered;
  emitOrder();
}

function resetOrder() {
  pageOrder.value = [...pageOrder.value].sort((a, b) => a - b);
  emitOrder();
}

function handleDragStart(event, index) {
  draggedIndex.value = index;
  event.dataTransfer.effectAllowed = "move";
  event.dataTransfer.setData("text/plain", String(index));
}

function handleDragOver(index) {
  if (draggedIndex.value !== null) dragOverIndex.value = index;
}

function handleDrop(toIndex) {
  if (draggedIndex.value !== null) movePage(draggedIndex.value, toIndex);
  resetDragState();
}

function resetDragState() {
  draggedIndex.value = null;
  dragOverIndex.value = null;
}

function emitOrder() {
  emit("order-change", [...pageOrder.value]);
}

function destroyPdfDocument() {
  if (pdfDocument.value) {
    pdfDocument.value.destroy();
    pdfDocument.value = null;
  }
}
</script>
