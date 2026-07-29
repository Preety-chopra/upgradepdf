import { createRouter, createWebHistory } from "vue-router";

import HomeView from "../views/HomeView.vue";
import PdfToolView from "../views/PdfToolView.vue";

import ConversionTools from "../pages/ConversionTools.vue";
import OcrTools from "../pages/OcrTools.vue";

const routes = [
  {
    path: "/",
    name: "home",
    component: HomeView
  },

  {
    path: "/tools/ocr-pdf",
    name: "ocr-pdf",
    component: OcrTools
  },

  {
    path: "/tools/:tool(jpg-to-pdf|png-to-pdf|word-to-pdf|excel-to-pdf|pdf-to-jpg|pdf-to-word|pdf-to-excel|pdf-to-csv)",
    name: "conversion-tool",
    component: ConversionTools,
    props: true
  },

  {
    path: "/tools/:tool",
    name: "pdf-tool",
    component: PdfToolView,
    props: true
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;