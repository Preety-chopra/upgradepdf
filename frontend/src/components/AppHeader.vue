<!-- frontend/src/components/AppHeader.vue -->

<template>
  <header class="app-header">
    <RouterLink to="/" class="logo">
      <img src="../assets/logo1.png" alt="UpgradePDF.com" />
    </RouterLink>

    <nav class="main-nav">
       <RouterLink
        to="/tools/merge"
        class="nav-link"
        :class="{ active: currentTool === 'merge' }"
      >
        MERGE PDF
      </RouterLink>

      <RouterLink
        to="/tools/split"
        class="nav-link"
        :class="{ active: currentTool === 'split' }"
      >
        SPLIT PDF
      </RouterLink>

      <RouterLink
        to="/tools/compress"
        class="nav-link"
        :class="{ active: currentTool === 'compress' }"
      >
        COMPRESS PDF
      </RouterLink>

      <div class="nav-dropdown">
        <button
          class="nav-link dropdown-button"
          :class="{ active: isConvertTool }"
        >
          CONVERT PDF
          <svg
            class="chevron"
            viewBox="0 0 12 8"
            aria-hidden="true"
          >
            <path d="M1 1.5 6 6.5l5-5" />
          </svg>
        </button>

        <div class="convert-menu dropdown-panel">
          <div class="menu-column">
            <h4>CONVERT TO PDF</h4>

            <RouterLink
              v-for="tool in convertToPdf"
              :key="tool.slug"
              :to="`/tools/${tool.slug}`"
              class="tool-link"
            >
              <span class="tool-icon">{{ tool.icon }}</span>
              <span>{{ tool.name }}</span>
            </RouterLink>
          </div>

          <div class="menu-column">
            <h4>CONVERT FROM PDF</h4>

            <RouterLink
              v-for="tool in convertFromPdf"
              :key="tool.slug"
              :to="`/tools/${tool.slug}`"
              class="tool-link"
            >
              <span class="tool-icon">{{ tool.icon }}</span>
              <span>{{ tool.name }}</span>
            </RouterLink>
          </div>
        </div>
      </div>

      <div class="nav-dropdown all-tools-wrapper">
        <button class="nav-link dropdown-button" :class="{ active: isAnyPdfTool }">
          ALL PDF TOOLS
          <svg
            class="chevron"
            viewBox="0 0 12 8"
            aria-hidden="true"
          >
            <path d="M1 1.5 6 6.5l5-5" />
          </svg>
        </button>

        <div class="all-tools-menu dropdown-panel">
          <div
            v-for="group in pdfToolGroups"
            :key="group.title"
            class="menu-column"
          >
            <h4>{{ group.title }}</h4>

            <RouterLink
              v-for="tool in group.tools"
              :key="tool.slug"
              :to="`/tools/${tool.slug}`"
              class="tool-link"
            >
              <span class="tool-icon">{{ tool.icon }}</span>
              <span>{{ tool.name }}</span>
            </RouterLink>
          </div>
        </div>
      </div>
    </nav>

    <!-- <div class="header-actions">
      <button class="login-btn">Login</button>
      <button class="signup-btn">Sign up</button>
    </div> -->
  </header>
</template>

<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import { pdfToolGroups } from "../data/pdfTools";

const route = useRoute();

const currentTool = computed(() => route.params.tool);

const convertToPdf = computed(() => {
  return pdfToolGroups.find((group) => group.title === "CONVERT TO PDF")?.tools || [];
});

const convertFromPdf = computed(() => {
  return pdfToolGroups.find((group) => group.title === "CONVERT FROM PDF")?.tools || [];
});

const convertSlugs = computed(() => [
  ...convertToPdf.value.map((tool) => tool.slug),
  ...convertFromPdf.value.map((tool) => tool.slug)
]);

const isConvertTool = computed(() => {
  return convertSlugs.value.includes(currentTool.value);
});

const isAnyPdfTool = computed(() => {
  return route.path.startsWith("/tools/");
});
</script>

<style scoped>
.app-header {
  width: 100%;
  height: 68px;
  background: #ffffff;
  border-bottom: 1px solid #dedede;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 36px;
  position: sticky;
  top: 0;
  z-index: 1000;
}

.logo {
  text-decoration: none;
  display: flex;
  align-items: center;
}

.logo img {
  display: block;
  width: auto;
  height: 52px;
  max-width: 240px;
  object-fit: contain;
}

.main-nav {
  display: flex;
  align-items: center;
  gap: 26px;
  height: 100%;
  flex: 1;
}

.nav-link {
  color: #111;
  text-decoration: none;
  font-size: 15px;
  font-weight: 700;
  border: none;
  background: transparent;
  cursor: pointer;
  height: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0;
}

.nav-link:hover,
.nav-link.active {
  color: #e5322d;
}

.dropdown-button {
  font-family: inherit;
}

.chevron {
  width: 11px;
  height: 7px;
  flex: 0 0 auto;
  display: block;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.75;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.nav-dropdown {
  height: 100%;
  display: flex;
  align-items: center;
  position: relative;
}

.dropdown-panel {
  display: none;
  position: absolute;
  top: 68px;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 22px 60px rgba(0, 0, 0, 0.16);
  padding: 36px 40px;
  z-index: 2000;
}

.nav-dropdown:hover .dropdown-panel {
  display: flex;
}

.convert-menu {
  left: 50%;
  transform: translateX(-50%);
  min-width: 620px;
  gap: 70px;
}

.all-tools-menu {
  left: 50%;
  transform: translateX(-50%);
  width: min(1280px, calc(100vw - 80px));
  gap: 44px;
  align-items: flex-start;
}

.menu-column {
  min-width: 150px;
}

.menu-column h4 {
  margin: 0 0 22px;
  font-size: 15px;
  font-weight: 800;
  color: #70737b;
  white-space: nowrap;
}

.tool-link {
  display: flex;
  align-items: center;
  gap: 14px;
  text-decoration: none;
  color: #222;
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 20px;
  white-space: nowrap;
}

.tool-link:hover {
  color: #e5322d;
}

.tool-icon {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  background: #f3f3f3;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 14px;
}

.login-btn,
.signup-btn {
  border: none;
  background: transparent;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
}

.signup-btn {
  background: #e5322d;
  color: #fff;
  border-radius: 9px;
  padding: 12px 18px;
}

@media (max-width: 1000px) {
  .main-nav {
    gap: 16px;
  }

  .nav-link {
    font-size: 13px;
  }

  .header-actions {
    display: none;
  }

  .all-tools-menu {
    left: auto;
    right: 0;
    transform: none;
    overflow-x: auto;
  }
}

@media (max-width: 760px) {
  .app-header {
    gap: 16px;
    overflow-x: auto;
  }

  .logo img {
    height: 44px;
    max-width: 200px;
  }

  .main-nav {
    min-width: max-content;
  }

  .dropdown-panel {
    position: fixed;
    left: 16px;
    right: 16px;
    top: 68px;
    transform: none;
    width: auto;
    min-width: auto;
    overflow-x: auto;
  }
}
</style>
