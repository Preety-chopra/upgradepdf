// frontend/src/data/pdfTools.js

export const pdfToolGroups = [
  {
    title: "ORGANIZE PDF",
    tools: [
      { name: "Merge PDF", slug: "merge", icon: "🔀" },
      { name: "Split PDF", slug: "split", icon: "✂️" }
    ]
  },
  {
    title: "OPTIMIZE PDF",
    tools: [
      { name: "Compress PDF", slug: "compress", icon: "🗜️" },
      { name: "OCR PDF", slug: "ocr-pdf", icon: "🔍" }
    ]
  },
  {
    title: "CONVERT TO PDF",
    tools: [
      { name: "JPG to PDF", slug: "jpg-to-pdf", icon: "🖼️" },
      { name: "PNG to PDF", slug: "png-to-pdf", icon: "🖼️" },
      { name: "WORD to PDF", slug: "word-to-pdf", icon: "📘" },
      { name: "EXCEL to PDF", slug: "excel-to-pdf", icon: "📗" }
    ]
  },
  {
    title: "CONVERT FROM PDF",
    tools: [
      { name: "PDF to JPG", slug: "pdf-to-jpg", icon: "🖼️" },
      { name: "PDF to WORD", slug: "pdf-to-word", icon: "📘" },
      { name: "PDF to EXCEL", slug: "pdf-to-excel", icon: "📗" },
      { name: "PDF to CSV", slug: "pdf-to-csv", icon: "📄" }
    ]
  }
];