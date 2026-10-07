<template>
  <div
    class="dropzone"
    :class="{ 'dropzone-active': isDragging }"
    @dragover.prevent="isDragging = true"
    @dragleave.prevent="isDragging = false"
    @drop.prevent="handleDrop"
  >
    <input
      ref="fileInput"
      class="file-input"
      type="file"
      accept="application/pdf"
      :multiple="multiple"
      @change="handleFileChange"
    />

    <div class="dropzone-content">
      <div class="upload-icon">↑</div>
      <h3>{{ multiple ? "Upload PDF files" : "Upload PDF file" }}</h3>
      <p>
        Drag and drop PDF {{ multiple ? "files" : "file" }} here, or click to
        browse.
      </p>

      <button type="button" class="secondary-btn" @click="openFilePicker">
        Choose {{ multiple ? "files" : "file" }}
      </button>
    </div>
  </div>

  <div v-if="files.length" class="selected-files">
    <h4>Selected file{{ files.length > 1 ? "s" : "" }}</h4>

    <p v-if="multiple && files.length > 1" class="file-order-help">
      Drag files or use the arrow buttons to set the merge order.
    </p>

    <ul class="selected-file-list">
      <li
        v-for="(file, index) in files"
        :key="`${file.name}-${file.size}-${file.lastModified}-${index}`"
        class="selected-file-item"
        :class="{
          'selected-file-item-draggable': multiple && files.length > 1,
          'selected-file-item-dragging': draggedIndex === index,
          'selected-file-item-drag-over': dragOverIndex === index && draggedIndex !== index
        }"
        :draggable="multiple && files.length > 1"
        @dragstart="handleReorderDragStart($event, index)"
        @dragover.prevent="handleReorderDragOver(index)"
        @drop.prevent="handleReorderDrop(index)"
        @dragend="resetReorderDrag"
      >
        <span v-if="multiple && files.length > 1" class="file-drag-handle" aria-hidden="true">⠿</span>
        <span class="file-order-number">{{ index + 1 }}</span>
        <span class="selected-file-name">{{ file.name }}</span>
        <small>{{ formatSize(file.size) }}</small>
        <span v-if="multiple && files.length > 1" class="file-order-actions">
          <button
            type="button"
            class="file-order-btn"
            :disabled="index === 0"
            :aria-label="`Move ${file.name} up`"
            @click="moveFile(index, index - 1)"
          >↑</button>
          <button
            type="button"
            class="file-order-btn"
            :disabled="index === files.length - 1"
            :aria-label="`Move ${file.name} down`"
            @click="moveFile(index, index + 1)"
          >↓</button>
        </span>
      </li>
    </ul>

    <button type="button" class="text-btn" @click="clearFiles">
      Clear selected files
    </button>
  </div>
</template>

<script setup>
import { ref } from "vue";

import { moveItem } from "../utils/fileOrder";

const props = defineProps({
  multiple: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(["files-selected", "files-reordered"]);

const fileInput = ref(null);
const files = ref([]);
const isDragging = ref(false);
const draggedIndex = ref(null);
const dragOverIndex = ref(null);

function openFilePicker() {
  fileInput.value?.click();
}

function handleFileChange(event) {
  const selected = Array.from(event.target.files || []);
  setFiles(selected);
}

function handleDrop(event) {
  isDragging.value = false;

  const droppedFiles = Array.from(event.dataTransfer.files || []);
  setFiles(droppedFiles);
}

function setFiles(selectedFiles) {
  const pdfFiles = selectedFiles.filter(
    (file) => file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")
  );

  if (!props.multiple && pdfFiles.length > 1) {
    files.value = [pdfFiles[0]];
  } else {
    files.value = pdfFiles;
  }

  emit("files-selected", files.value);
}

function clearFiles() {
  files.value = [];

  if (fileInput.value) {
    fileInput.value.value = "";
  }

  emit("files-selected", []);
}

function moveFile(fromIndex, toIndex) {
  const reorderedFiles = moveItem(files.value, fromIndex, toIndex);

  if (reorderedFiles.every((file, index) => file === files.value[index])) {
    return;
  }

  files.value = reorderedFiles;
  emit("files-reordered", files.value);
}

function handleReorderDragStart(event, index) {
  if (!props.multiple || files.value.length < 2) {
    event.preventDefault();
    return;
  }

  draggedIndex.value = index;
  event.dataTransfer.effectAllowed = "move";
  event.dataTransfer.setData("text/plain", String(index));
}

function handleReorderDragOver(index) {
  if (draggedIndex.value !== null) {
    dragOverIndex.value = index;
  }
}

function handleReorderDrop(toIndex) {
  if (draggedIndex.value !== null) {
    moveFile(draggedIndex.value, toIndex);
  }

  resetReorderDrag();
}

function resetReorderDrag() {
  draggedIndex.value = null;
  dragOverIndex.value = null;
}

function formatSize(bytes) {
  if (!bytes) {
    return "0 B";
  }

  const mb = bytes / (1024 * 1024);
  return `${mb.toFixed(2)} MB`;
}
</script>
