<!-- <template>
  <div class="app-shell">
    <header class="topbar">
      <RouterLink to="/" class="brand">
        <span class="brand-icon">PDF</span>
        <span>
          <strong>UpgradePDF</strong>
          <small>Secure document tools</small>
        </span>
      </RouterLink>

      <nav class="topnav">
        <RouterLink to="/">Home</RouterLink>
        <a href="/docs" target="_blank" rel="noreferrer">
          API Docs
        </a>
      </nav>
    </header>

    <main>
      <RouterView />
    </main>
  </div>
</template> -->

<!-- frontend/src/App.vue -->

<template>
  <AppHeader />
  <div class="page-ad-layout" :class="{ 'has-right-ad': rightAdAvailable }">
    <AdSlot placement="page-left" />
    <div class="page-route-content">
      <RouterView />
    </div>
    <AdSlot placement="page-right" @availability-change="rightAdAvailable = $event" />
  </div>
</template>

<script setup>
import { ref } from "vue";

import AdSlot from "./components/AdSlot.vue";
import AppHeader from "./components/AppHeader.vue";

const rightAdAvailable = ref(false);
</script>

<style>
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: Arial, Helvetica, sans-serif;
  background: #f5f5fa;
}
</style>
