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

    <ul>
      <li v-for="file in files" :key="file.name + file.size">
        <span>{{ file.name }}</span>
        <small>{{ formatSize(file.size) }}</small>
      </li>
    </ul>

    <button type="button" class="text-btn" @click="clearFiles">
      Clear selected files
    </button>
  </div>
</template>

<script setup>
import { ref } from "vue";

const props = defineProps({
  multiple: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(["files-selected"]);

const fileInput = ref(null);
const files = ref([]);
const isDragging = ref(false);

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

function formatSize(bytes) {
  if (!bytes) {
    return "0 B";
  }

  const mb = bytes / (1024 * 1024);
  return `${mb.toFixed(2)} MB`;
}
</script>