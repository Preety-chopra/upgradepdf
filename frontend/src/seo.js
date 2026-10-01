const SITE_NAME = "UpgradePDF";
const SITE_URL = "https://upgradepdf.com";

const DEFAULT_METADATA = {
  title: "UpgradePDF – Free Online PDF Tools",
  description:
    "Merge, split, compress, convert, edit, and OCR PDF files online with UpgradePDF's secure and easy-to-use document tools."
};

const PAGE_METADATA = {
  "ocr-pdf": {
    title: "OCR PDF Online – Make Scanned PDFs Searchable",
    description:
      "Convert scanned PDFs into searchable documents with online OCR. Choose English, Hindi, or mixed-language recognition and export the extracted text."
  },
  convert: {
    title: "Convert PDF, Word, Excel, JPG & PNG Online",
    description:
      "Convert PDF, Word, Excel, JPG, and PNG files online. Create PDFs, export PDF pages as images, or extract tables into Excel and CSV files."
  }
};

const TOOL_METADATA = {
  merge: {
    title: "Merge PDF Online – Combine PDF Files",
    description:
      "Combine two or more PDF files into one document online. Upload your PDFs, merge them in order, and download the finished file."
  },
  split: {
    title: "Split PDF Online – Extract PDF Pages",
    description:
      "Split a PDF or extract selected pages into a new document online. Choose individual pages or page ranges and download the result."
  },
  compress: {
    title: "Compress PDF Online – Reduce PDF File Size",
    description:
      "Reduce PDF file size online while preserving readable text, links, forms, and page layout. Choose the compression level that fits your needs."
  },
  rotate: {
    title: "Rotate PDF Pages Online",
    description:
      "Rotate every page or selected pages in a PDF online. Choose the pages and angle, then download the corrected PDF document."
  },
  "delete-pages": {
    title: "Delete PDF Pages Online",
    description:
      "Remove unwanted pages from a PDF online. Select individual pages or page ranges and download a clean PDF with the remaining pages."
  },
  "pdf-to-jpg": {
    title: "PDF to JPG Converter Online",
    description:
      "Convert PDF pages to high-quality JPG images online. Upload a PDF and download all converted pages together in a ZIP file."
  },
  "jpg-to-pdf": {
    title: "JPG to PDF Converter Online",
    description:
      "Convert one or more JPG images into a single PDF document online. Upload your images and download a ready-to-share PDF file."
  },
  "png-to-pdf": {
    title: "PNG to PDF Converter Online",
    description:
      "Convert one or more PNG images into a single PDF document online. Upload your images and download a ready-to-share PDF file."
  },
  "images-to-pdf": {
    title: "JPG & PNG to PDF Converter Online",
    description:
      "Combine JPG and PNG images into a single PDF document online. Upload one or more images and download a ready-to-share PDF file."
  },
  "word-to-pdf": {
    title: "Word to PDF Converter Online",
    description:
      "Convert DOC and DOCX Word documents to PDF online. Upload your Word file and download a clean PDF that is easy to share."
  },
  "excel-to-pdf": {
    title: "Excel to PDF Converter Online",
    description:
      "Convert XLS and XLSX spreadsheets to PDF online. Upload an Excel workbook and download it as a convenient PDF document."
  },
  "pdf-to-word": {
    title: "PDF to Word Converter Online",
    description:
      "Convert PDF files to Word documents online. Create an editable DOCX or preserve the visual layout of scanned PDF pages."
  },
  "pdf-to-excel": {
    title: "PDF to Excel Converter Online",
    description:
      "Extract tables from a digital PDF into an Excel spreadsheet online. Upload your PDF and download the tabular data as an XLSX file."
  },
  "pdf-to-csv": {
    title: "PDF to CSV Converter Online",
    description:
      "Extract tabular data from a digital PDF into a CSV file online. Upload your PDF and download data ready for spreadsheets and analysis."
  }
};

const TOOL_SCHEMA = {
  merge: {
    name: "Merge PDF",
    features: ["Combine multiple PDF files into one document"]
  },
  split: {
    name: "Split PDF",
    features: ["Extract individual PDF pages or page ranges"]
  },
  compress: {
    name: "Compress PDF",
    features: ["Reduce PDF file size", "Choose from multiple compression levels"]
  },
  rotate: {
    name: "Rotate PDF",
    features: ["Rotate all or selected PDF pages", "Choose a page rotation angle"]
  },
  "delete-pages": {
    name: "Delete PDF Pages",
    features: ["Remove individual PDF pages or page ranges"]
  },
  "ocr-pdf": {
    name: "OCR PDF",
    features: [
      "Make scanned PDF documents searchable",
      "Recognize English, Hindi, or mixed-language text",
      "Export recognized text"
    ]
  },
  "pdf-to-jpg": {
    name: "PDF to JPG",
    features: ["Convert PDF pages to JPG images", "Download converted images in a ZIP file"]
  },
  "jpg-to-pdf": {
    name: "JPG to PDF",
    features: ["Combine one or more JPG images into a PDF document"]
  },
  "png-to-pdf": {
    name: "PNG to PDF",
    features: ["Combine one or more PNG images into a PDF document"]
  },
  "images-to-pdf": {
    name: "JPG and PNG to PDF",
    features: ["Combine JPG and PNG images into a PDF document"]
  },
  "word-to-pdf": {
    name: "Word to PDF",
    features: ["Convert DOC and DOCX documents to PDF"]
  },
  "excel-to-pdf": {
    name: "Excel to PDF",
    features: ["Convert XLS and XLSX workbooks to PDF"]
  },
  "pdf-to-word": {
    name: "PDF to Word",
    features: ["Convert PDF files to DOCX", "Support editable and visual conversion modes"]
  },
  "pdf-to-excel": {
    name: "PDF to Excel",
    features: ["Extract tables from PDF files into XLSX spreadsheets"]
  },
  "pdf-to-csv": {
    name: "PDF to CSV",
    features: ["Extract tabular data from PDF files into CSV files"]
  }
};

const ORGANIZATION_SCHEMA = {
  "@type": "Organization",
  "@id": `${SITE_URL}/#organization`,
  name: SITE_NAME,
  url: `${SITE_URL}/`
};

const WEBSITE_SCHEMA = {
  "@type": "WebSite",
  "@id": `${SITE_URL}/#website`,
  name: SITE_NAME,
  url: `${SITE_URL}/`,
  publisher: {
    "@id": `${SITE_URL}/#organization`
  }
};

function withSiteName(title) {
  return title.includes(SITE_NAME) ? title : `${title} | ${SITE_NAME}`;
}

function upsertMetaTag(attribute, value, content) {
  let tag = document.querySelector(`meta[${attribute}="${value}"]`);
  if (!tag) {
    tag = document.createElement("meta");
    tag.setAttribute(attribute, value);
    document.head.appendChild(tag);
  }

  tag.setAttribute("content", content);
}

function upsertStructuredData(data) {
  let script = document.querySelector("#upgradepdf-structured-data");
  if (!script) {
    script = document.createElement("script");
    script.id = "upgradepdf-structured-data";
    script.type = "application/ld+json";
    document.head.appendChild(script);
  }

  script.textContent = JSON.stringify(data);
}

function getToolKey(route) {
  if (route.name === "ocr-pdf") {
    return "ocr-pdf";
  }

  if (route.name === "conversion-tool" || route.name === "pdf-tool") {
    return route.params?.tool;
  }

  if (route.name === "convert") {
    return route.query?.type;
  }

  return null;
}

function getPageUrl(route, toolKey) {
  if (route.name === "ocr-pdf") {
    return `${SITE_URL}/tools/ocr-pdf`;
  }

  if (route.name === "conversion-tool" || route.name === "pdf-tool") {
    return `${SITE_URL}/tools/${encodeURIComponent(toolKey)}`;
  }

  if (route.name === "convert" && toolKey) {
    return `${SITE_URL}/convert?type=${encodeURIComponent(toolKey)}`;
  }

  if (route.name === "convert") {
    return `${SITE_URL}/convert`;
  }

  return `${SITE_URL}/`;
}

export function getSeoMetadata(route) {
  if (route.name === "home") {
    return DEFAULT_METADATA;
  }

  if (route.name === "ocr-pdf") {
    return PAGE_METADATA["ocr-pdf"];
  }

  if (route.name === "conversion-tool") {
    return TOOL_METADATA[route.params?.tool] || PAGE_METADATA.convert;
  }

  if (route.name === "convert") {
    return TOOL_METADATA[route.query?.type] || PAGE_METADATA.convert;
  }

  if (route.name === "pdf-tool") {
    return TOOL_METADATA[route.params?.tool] || DEFAULT_METADATA;
  }

  return DEFAULT_METADATA;
}

export function getStructuredData(route) {
  const toolKey = getToolKey(route);
  const toolSchema = TOOL_SCHEMA[toolKey];

  if (!toolSchema && route.name !== "convert") {
    return {
      "@context": "https://schema.org",
      "@graph": [
        ORGANIZATION_SCHEMA,
        WEBSITE_SCHEMA,
        {
          "@type": "WebApplication",
          "@id": `${SITE_URL}/#application`,
          name: SITE_NAME,
          url: `${SITE_URL}/`,
          description: DEFAULT_METADATA.description,
          applicationCategory: "UtilitiesApplication",
          operatingSystem: "Any",
          browserRequirements: "Requires a modern web browser with JavaScript enabled.",
          featureList: [
            "Merge, split, compress, and edit PDF files",
            "Convert PDF, Word, Excel, JPG, and PNG files",
            "Make scanned PDF documents searchable with OCR"
          ],
          offers: {
            "@type": "Offer",
            price: "0",
            priceCurrency: "USD"
          },
          provider: {
            "@id": `${SITE_URL}/#organization`
          }
        }
      ]
    };
  }

  const metadata = getSeoMetadata(route);
  const pageUrl = getPageUrl(route, toolKey);
  const name = toolSchema?.name || "PDF Conversion Tools";
  const features = toolSchema?.features || [
    "Convert PDF, Word, Excel, JPG, and PNG files online"
  ];

  return {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "WebPage",
        "@id": `${pageUrl}#webpage`,
        url: pageUrl,
        name: withSiteName(metadata.title),
        description: metadata.description,
        isPartOf: {
          "@id": `${SITE_URL}/#website`
        },
        mainEntity: {
          "@id": `${pageUrl}#application`
        }
      },
      {
        "@type": "WebApplication",
        "@id": `${pageUrl}#application`,
        name,
        url: pageUrl,
        description: metadata.description,
        applicationCategory: "UtilitiesApplication",
        operatingSystem: "Any",
        browserRequirements: "Requires a modern web browser with JavaScript enabled.",
        featureList: features,
        offers: {
          "@type": "Offer",
          price: "0",
          priceCurrency: "USD"
        },
        provider: {
          "@id": `${SITE_URL}/#organization`
        }
      },
      {
        "@type": "BreadcrumbList",
        "@id": `${pageUrl}#breadcrumb`,
        itemListElement: [
          {
            "@type": "ListItem",
            position: 1,
            name: "Home",
            item: `${SITE_URL}/`
          },
          {
            "@type": "ListItem",
            position: 2,
            name,
            item: pageUrl
          }
        ]
      }
    ]
  };
}

export function applySeoMetadata(route) {
  const metadata = getSeoMetadata(route);
  const title = withSiteName(metadata.title);

  document.title = title;
  upsertMetaTag("name", "description", metadata.description);
  upsertMetaTag("property", "og:title", title);
  upsertMetaTag("property", "og:description", metadata.description);
  upsertStructuredData(getStructuredData(route));
}
