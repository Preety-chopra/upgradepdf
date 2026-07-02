<template>
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
        <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
          API Docs
        </a>
      </nav>
    </header>

    <main>
      <RouterView />
    </main>
  </div>
</template>
