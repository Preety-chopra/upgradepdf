<!-- <template>
  <div class="app-shell">
    <header class="topbar">
      <RouterLink to="/" class="brand">
        <span class="brand-icon">PDF</span>
        <span>
          <strong>PDF Utility Platform</strong>
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
  <RouterView />
</template>

<script setup>
import AppHeader from "./components/AppHeader.vue";
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
