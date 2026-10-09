import { createRouter, createWebHistory } from "vue-router";

import { applySeoMetadata } from "../seo";

const HomeView = () => import("../views/HomeView.vue");
const PdfToolView = () => import("../views/PdfToolView.vue");
const ConversionTools = () => import("../pages/ConversionTools.vue");
const OcrTools = () => import("../pages/OcrTools.vue");

const routes = [
  {
    path: "/",
    name: "home",
    component: HomeView
  },

  {
    path: "/tools/ocr-pdf",
    alias: "/ocr",
    name: "ocr-pdf",
    component: OcrTools
  },

  {
    path: "/convert",
    name: "convert",
    component: ConversionTools
  },
  {
    path: "/tools/:tool(jpg-to-pdf|png-to-pdf|images-to-pdf|word-to-pdf|excel-to-pdf|pdf-to-jpg|pdf-to-word|pdf-to-excel|pdf-to-csv)",
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

router.afterEach((to) => {
  applySeoMetadata(to);
});

export default router;
