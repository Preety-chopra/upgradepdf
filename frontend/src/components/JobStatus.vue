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
</script>