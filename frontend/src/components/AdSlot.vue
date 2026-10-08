<template>
  <aside
    ref="slotElement"
    v-show="hasAd"
    class="ad-slot"
    :data-ad-placement="placement"
    aria-label="Advertisement"
  >
    <span>Advertisement</span>
    <div ref="adSurface" class="ad-slot-surface"></div>
  </aside>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";

defineProps({
  placement: {
    type: String,
    required: true
  }
});

const emit = defineEmits(["availability-change"]);
const slotElement = ref(null);
const adSurface = ref(null);
const hasAd = ref(false);
let observer = null;

function detectAdAvailability() {
  const root = slotElement.value;
  const surface = adSurface.value;

  if (!root || !surface) {
    return;
  }

  const explicitlyFilled =
    root.dataset.adStatus === "filled" ||
    Boolean(surface.querySelector('[data-ad-status="filled"]'));
  const renderedCreative = Boolean(
    surface.querySelector("iframe[src], img[src], video[src], object[data], embed[src]")
  );
  const nextAvailability = explicitlyFilled || renderedCreative;

  if (hasAd.value !== nextAvailability) {
    hasAd.value = nextAvailability;
    emit("availability-change", nextAvailability);
  }
}

onMounted(() => {
  observer = new MutationObserver(detectAdAvailability);
  observer.observe(slotElement.value, {
    attributes: true,
    childList: true,
    subtree: true,
    attributeFilter: ["data-ad-status", "src", "data"]
  });
  detectAdAvailability();
});

onBeforeUnmount(() => {
  observer?.disconnect();
});
</script>
