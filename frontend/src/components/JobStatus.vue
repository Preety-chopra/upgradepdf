<template>
  <div v-if="job" class="job-card">
    <div class="job-header">
      <div>
        <p class="eyebrow">Job status</p>
        <h3>{{ readableStatus }}</h3>
      </div>

      <span class="status-pill" :class="`status-${job.status}`">
        {{ job.status }}
      </span>
    </div>

    <div class="job-details">
      <div>
        <small>Job ID</small>
        <p>{{ job.id }}</p>
      </div>

      <div>
        <small>Operation</small>
        <p>{{ job.operation }}</p>
      </div>

      <div>
        <small>Created</small>
        <p>{{ formatDate(job.created_at) }}</p>
      </div>

      <div v-if="job.output_filename">
        <small>Output</small>
        <p>{{ job.output_filename }}</p>
      </div>

      <div v-if="job.operation === 'compress' && job.input_size_bytes != null">
        <small>Original size</small>
        <p>{{ formatSize(job.input_size_bytes) }}</p>
      </div>

      <div v-if="job.operation === 'compress' && job.output_size_bytes != null">
        <small>Compressed size</small>
        <p>{{ formatSize(job.output_size_bytes) }}</p>
      </div>

      <div
        v-if="
          job.operation === 'compress' &&
          job.savings_percent !== null &&
          job.savings_percent !== undefined
        "
      >
        <small>Space saved</small>
        <p>{{ job.savings_percent }}%</p>
      </div>
    </div>

    <p v-if="job.error_message" class="error-box">
      {{ job.error_message }}
    </p>

    <a
      v-if="downloadUrl"
      class="primary-btn full-width"
      :href="downloadUrl"
      target="_blank"
      rel="noreferrer"
    >
      Download processed PDF
    </a>

    <p v-if="job.status === 'purged'" class="warning-box">
      This file has been deleted as per the 60-minute retention policy.
    </p>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { buildAbsoluteUrl } from "../services/api";

const props = defineProps({
  job: {
    type: Object,
    default: null
  }
});

const readableStatus = computed(() => {
  if (!props.job) {
    return "";
  }

  const map = {
    pending: "Waiting to start",
    processing: "Processing your PDF",
    completed: "Your PDF is ready",
    failed: "Processing failed",
    purged: "File deleted"
  };

  return map[props.job.status] || props.job.status;
});

const downloadUrl = computed(() => {
  if (!props.job?.download_url) {
    return null;
  }

  return buildAbsoluteUrl(props.job.download_url);
});

function formatDate(value) {
  if (!value) {
    return "-";
  }

  return new Date(value).toLocaleString();
}

function formatSize(bytes) {
  if (bytes === null || bytes === undefined) {
    return "-";
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}
</script>