<template>
  <RouterLink :to="link" class="tool-card">
    <div class="tool-card-icon">
      {{ initials }}
    </div>

    <div>
      <h3>{{ title }}</h3>
      <p>{{ description }}</p>
      <span>Open tool →</span>
    </div>
  </RouterLink>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    required: true
  },
  link: {
    type: String,
    required: true
  }
});

const initials = computed(() => {
  return props.title
    .split(" ")
    .map((word) => word[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
});
</script>