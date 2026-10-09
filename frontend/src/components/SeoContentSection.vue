<template>
  <section class="seo-content" :aria-labelledby="`${resolvedKey}-seo-heading`">
    <div class="seo-content__intro">
      <p class="seo-content__eyebrow">UpgradePDF guide</p>
      <h2 :id="`${resolvedKey}-seo-heading`">{{ content.heading }}</h2>
    </div>

    <div class="seo-content__grid">
      <article class="seo-content__about">
        <h2>About the Tool</h2>
        <p v-for="paragraph in content.about" :key="paragraph">{{ paragraph }}</p>
      </article>

      <article>
        <h2>How to Use</h2>
        <ol>
          <li v-for="step in content.steps" :key="step">{{ step }}</li>
        </ol>
      </article>

      <article>
        <h2>Key Benefits</h2>
        <ul>
          <li v-for="benefit in content.benefits" :key="benefit">{{ benefit }}</li>
        </ul>
      </article>

      <article>
        <h2>Common Use Cases</h2>
        <ul>
          <li v-for="useCase in content.useCases" :key="useCase">{{ useCase }}</li>
        </ul>
      </article>
    </div>

    <section class="seo-content__faqs" aria-label="Frequently asked questions">
      <h2>Frequently Asked Questions</h2>
      <div class="seo-content__faq-grid">
        <article v-for="faq in content.faqs" :key="faq.question">
          <h3>{{ faq.question }}</h3>
          <p>{{ faq.answer }}</p>
        </article>
      </div>
    </section>

    <nav class="seo-content__related" aria-label="Related PDF tools">
      <h2>Related PDF Tools</h2>
      <div>
        <RouterLink v-for="link in content.related" :key="link.path" :to="link.path">
          {{ link.label }}
        </RouterLink>
      </div>
    </nav>
  </section>
</template>

<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";

import { getSeoContent } from "../data/seoContent";

const props = defineProps({
  pageKey: {
    type: String,
    default: ""
  }
});

const route = useRoute();
const resolvedKey = computed(() => {
  if (props.pageKey) return props.pageKey;
  if (route.name === "ocr-pdf") return "ocr-pdf";
  if (route.name === "convert") return route.query.type || "convert";
  return route.params.tool || "home";
});
const content = computed(() => getSeoContent(resolvedKey.value));
</script>
