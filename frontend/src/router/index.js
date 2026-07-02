import { createRouter, createWebHistory } from "vue-router";

import HomeView from "../views/HomeView.vue";
import PdfToolView from "../views/PdfToolView.vue";

import OcrTools from "../pages/OcrTools.vue";
import ConversionTools from "../pages/ConversionTools.vue";

const routes = [
  {
    path: "/",
    name: "home",
    component: HomeView
  },
  {
    path: "/tools/:tool",
    name: "pdf-tool",
    component: PdfToolView
  },
  {
    path: "/ocr",
    name: "ocr-tools",
    component: OcrTools
  },
  {
    path: "/convert",
    name: "conversion-tools",
    component: ConversionTools
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;