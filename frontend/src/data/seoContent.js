const toolLink = (slug, label) => ({ path: `/tools/${slug}`, label });

function defineTool({
  heading,
  name,
  input,
  output,
  about,
  steps,
  benefits,
  useCases,
  bestResult,
  extraFaq,
  related
}) {
  return {
    heading,
    about: [
      about,
      `${name} runs in your browser as a straightforward online workflow: choose the source ${input}, confirm the available settings, and download ${output}. It is useful when you need a focused result without installing desktop PDF software or learning a complex editor.`
    ],
    steps,
    benefits,
    useCases,
    faqs: [
      {
        question: `What files can I use with ${name}?`,
        answer: `This tool is designed for ${input}. Choose a file that matches the upload field shown above; the page will reject unsupported formats.`
      },
      {
        question: `What do I receive after using ${name}?`,
        answer: `When processing finishes, you can download ${output}. Keep the original file until you have opened and checked the result.`
      },
      {
        question: `Do I need to install software to use ${name}?`,
        answer: `No. The workflow is available through a modern web browser, so there is no desktop application to install for this task.`
      },
      {
        question: `How can I get the best result?`,
        answer: bestResult
      },
      extraFaq
    ],
    related
  };
}

export const SEO_CONTENT = {
  home: {
    heading: "Free Online PDF Tools for Everyday Document Tasks",
    about: [
      "UpgradePDF brings common PDF jobs into one browser-based workspace. You can combine documents, extract selected pages, reduce file size, correct page order, convert between popular formats, and run optical character recognition on scanned pages. Each utility is separated into a focused workflow so you can move from upload to download without navigating a full document editor.",
      "The collection is built for practical questions such as “How do I merge PDF files online?” and “Can I turn a scanned PDF into searchable text?” Choose the tool that matches your intended output, review its options, and keep your original document until you have verified the downloaded result."
    ],
    steps: [
      "Choose a PDF tool from the cards above based on the result you need.",
      "Upload the supported PDF, image, Word, or Excel file and select any page or output options.",
      "Start processing, then download and review the new document on your device."
    ],
    benefits: [
      "Focused tools make routine document changes easier to understand.",
      "Browser access means you do not need to install a desktop PDF suite.",
      "Related workflows are linked so multi-step jobs are easier to complete."
    ],
    useCases: [
      "Prepare reports by merging attachments and removing unnecessary pages.",
      "Create shareable PDFs from photos, Word documents, or spreadsheets.",
      "Extract images, tables, editable text, or searchable text from PDFs."
    ],
    faqs: [
      { question: "What can I do with UpgradePDF?", answer: "You can organize, optimize, convert, and OCR documents with dedicated online tools for each task." },
      { question: "Are the PDF tools free to use?", answer: "The tools shown on this site are available without a purchase step. Individual pages explain their supported inputs and outputs." },
      { question: "Do I need an account?", answer: "The current workflows do not present an account or sign-in requirement before you upload a file." },
      { question: "Which tool should I choose?", answer: "Start with your desired output: use Merge or Split for page organization, Compress for a smaller PDF, Convert for another format, or OCR for scanned text." },
      { question: "Can I use UpgradePDF on a phone?", answer: "The responsive interface works in modern mobile browsers, although large documents are usually easier to review on a larger screen." }
    ],
    related: [toolLink("merge", "Merge PDF"), toolLink("compress", "Compress PDF"), toolLink("pdf-to-word", "PDF to Word"), toolLink("ocr-pdf", "OCR PDF")]
  },

  convert: {
    heading: "Online PDF and Document Conversion Tools",
    about: [
      "The UpgradePDF conversion workspace changes documents between PDF, JPG, PNG, Word, Excel, and CSV formats. Select a conversion based on what you want to download: a PDF for sharing, images for individual pages, an editable Word file, or structured spreadsheet data. Separate routes provide a clear, indexable explanation for every supported conversion.",
      "Format conversion is not the same as visual editing. Results depend on the source document: clean digital text and well-defined tables usually convert more predictably than scans, photographs, or highly designed layouts. Review the output before relying on it for publication, calculations, or archival use."
    ],
    steps: ["Choose a conversion type from the list above.", "Upload a supported source file and select a mode when one is available.", "Convert the file, download the result, and check formatting or extracted data."],
    benefits: ["One workspace covers popular document and image formats.", "Purpose-built modes help match the output to the source document.", "Direct downloads keep the workflow simple for one-off conversions."],
    useCases: ["Turn office documents into PDFs for consistent sharing.", "Export PDF pages as images for presentations or previews.", "Move PDF text or tables into editable Word, Excel, or CSV files."],
    faqs: [
      { question: "Which formats can I convert?", answer: "The current tools cover PDF, JPG, PNG, DOC, DOCX, XLS, XLSX, and CSV-related workflows." },
      { question: "Will a converted file look exactly like the original?", answer: "Not always. Fonts, complex layouts, scans, and irregular tables can change during conversion, so review the download." },
      { question: "Can scanned PDFs become editable Word files?", answer: "The PDF to Word tool includes modes for scanned pages, including OCR text and image-based output." },
      { question: "Can I combine several images into one PDF?", answer: "Yes. Use the Images to PDF tool to upload multiple JPG or PNG files and create one PDF." },
      { question: "Do I need conversion software?", answer: "No desktop converter is required; these workflows run through a modern browser." }
    ],
    related: [toolLink("images-to-pdf", "Images to PDF"), toolLink("word-to-pdf", "Word to PDF"), toolLink("pdf-to-jpg", "PDF to JPG"), toolLink("pdf-to-excel", "PDF to Excel")]
  },

  merge: defineTool({
    heading: "Merge PDF Files Online",
    name: "Merge PDF",
    input: "two or more PDF files",
    output: "one combined PDF in the selected file order",
    about: "Merge PDF combines several PDF documents into a single file. It is designed for assembling related pages—such as a cover sheet, report, appendix, and signed form—while keeping each source PDF intact inside the new document.",
    steps: ["Upload at least two PDFs and add more files if needed.", "Reorder the selected files so they appear in the intended sequence.", "Select Merge PDF, wait for processing, and download the combined document."],
    benefits: ["Create one attachment instead of sending a group of separate files.", "Control document order before processing.", "Preserve the pages of each source PDF in a single output."],
    useCases: ["Combine invoices or monthly statements into one record.", "Join a proposal with supporting schedules and appendices.", "Assemble scanned pages that were saved as separate PDFs."],
    bestResult: "Open each source PDF first, remove password restrictions if necessary, and arrange files in the exact reading order before merging.",
    extraFaq: { question: "Can I change the order of PDFs before merging?", answer: "Yes. Reorder the uploaded files in the list before starting the merge; the output follows that sequence." },
    related: [toolLink("reorder-pages", "Reorder PDF Pages"), toolLink("delete-pages", "Delete PDF Pages"), toolLink("compress", "Compress PDF")]
  }),

  split: defineTool({
    heading: "Split PDF and Extract Selected Pages Online",
    name: "Split PDF",
    input: "one PDF file and a page selection such as 1-3 or 1,4,6",
    output: "a new PDF containing only the pages you selected",
    about: "Split PDF extracts specific pages from a larger document. Instead of altering the source file, it creates a new PDF from the page numbers or ranges you choose, which is helpful when only part of a report or packet needs to be shared.",
    steps: ["Upload the PDF you want to divide.", "Enter page numbers or ranges, or choose pages from the preview.", "Select Split PDF and download the extracted-page document."],
    benefits: ["Share only the relevant pages of a long PDF.", "Combine separate page ranges in one new file.", "Keep the original PDF unchanged on your device."],
    useCases: ["Extract one chapter from a manual.", "Send selected pages from a contract for review.", "Create a smaller handout from a presentation PDF."],
    bestResult: "Check the detected page count and preview the selection. Page numbers begin at 1, and ranges should follow the examples shown in the field.",
    extraFaq: { question: "Can I extract non-consecutive PDF pages?", answer: "Yes. Enter comma-separated pages, such as 1,4,6, or combine them with a range such as 1-3,7." },
    related: [toolLink("delete-pages", "Delete PDF Pages"), toolLink("reorder-pages", "Reorder PDF Pages"), toolLink("merge", "Merge PDF")]
  }),

  compress: defineTool({
    heading: "Compress PDF Online and Reduce File Size",
    name: "Compress PDF",
    input: "one PDF file",
    output: "a smaller PDF using the chosen compression level",
    about: "Compress PDF reduces document size for easier email, upload, and storage. Light, balanced, and strong settings let you choose between visual fidelity and a more aggressive reduction, while the output remains a PDF.",
    steps: ["Upload the PDF whose file size you want to reduce.", "Choose light, balanced, or strong compression based on your quality needs.", "Compress the document, then compare the downloaded result with the original."],
    benefits: ["Make large PDFs easier to attach or upload.", "Choose a compression level instead of accepting one fixed setting.", "Keep text, forms, links, and page layout where the source allows."],
    useCases: ["Reduce a report before sending it by email.", "Prepare a PDF for a portal with a file-size limit.", "Save storage space for image-heavy scanned documents."],
    bestResult: "Use balanced compression first. Choose strong compression for image-heavy files only when a smaller download matters more than maximum image quality.",
    extraFaq: { question: "Why is my compressed PDF not much smaller?", answer: "A PDF that already uses efficient images and fonts may have little redundant data. Compression gains vary by document." },
    related: [toolLink("merge", "Merge PDF"), toolLink("split", "Split PDF"), toolLink("ocr-pdf", "OCR PDF")]
  }),

  rotate: defineTool({
    heading: "Rotate PDF Pages Online",
    name: "Rotate PDF",
    input: "one PDF plus all pages or selected page numbers",
    output: "a corrected PDF with the requested pages rotated",
    about: "Rotate PDF fixes pages that display sideways or upside down. You can rotate the entire document or target selected pages, then choose a 90-, 180-, or 270-degree angle before exporting a corrected copy.",
    steps: ["Upload the PDF and open the preview if you need to inspect orientation.", "Choose all pages or enter selected page numbers, then set the rotation angle.", "Apply the rotation and download the corrected PDF."],
    benefits: ["Correct mixed page orientations without rebuilding the document.", "Rotate only the pages that need attention.", "Create a new file while retaining your original copy."],
    useCases: ["Fix landscape pages scanned as portrait.", "Correct upside-down pages in a signed packet.", "Standardize orientation before merging or sharing PDFs."],
    bestResult: "Preview the document and test one affected page if orientation varies. A 90-degree clockwise rotation may need 270 degrees to reverse it.",
    extraFaq: { question: "Can I rotate only one page in a PDF?", answer: "Yes. Enter that page number in the Pages field and select the angle before processing." },
    related: [toolLink("reorder-pages", "Reorder PDF Pages"), toolLink("delete-pages", "Delete PDF Pages"), toolLink("merge", "Merge PDF")]
  }),

  "delete-pages": defineTool({
    heading: "Delete Pages from a PDF Online",
    name: "Delete PDF Pages",
    input: "one PDF and the page numbers or ranges to remove",
    output: "a new PDF containing every page except those selected for deletion",
    about: "Delete PDF Pages removes unwanted material while keeping the remaining pages in their original order. Use it to clean blank scans, outdated sections, duplicate pages, or confidential pages from a shareable copy.",
    steps: ["Upload the PDF and review its page count or preview.", "Enter the individual pages or ranges you want to remove.", "Select Delete Pages and download the PDF containing the remaining pages."],
    benefits: ["Remove several page ranges in one operation.", "Preview before processing to reduce page-number mistakes.", "Protect the source by creating a separate output file."],
    useCases: ["Remove blank pages introduced by a scanner.", "Delete an outdated appendix before distribution.", "Create a client copy without internal-only pages."],
    bestResult: "Confirm page numbers in the preview before deleting. At least one page must remain, so the tool will not create an empty PDF.",
    extraFaq: { question: "Can I undo deleted PDF pages?", answer: "The downloaded output does not include those pages. Keep the original PDF so you can return to it if needed." },
    related: [toolLink("split", "Split PDF"), toolLink("reorder-pages", "Reorder PDF Pages"), toolLink("merge", "Merge PDF")]
  }),

  "reorder-pages": defineTool({
    heading: "Reorder PDF Pages Online",
    name: "Reorder PDF Pages",
    input: "one PDF with two or more pages",
    output: "a new PDF whose pages follow your chosen order",
    about: "Reorder PDF Pages lets you rearrange a document visually. Page thumbnails make it easier to move misplaced sheets, reverse accidental scan order, or assemble a cleaner reading sequence before exporting a new PDF.",
    steps: ["Upload a PDF and open the visual page organizer.", "Drag thumbnails or use the move controls to set the correct sequence.", "Export and download the reordered PDF after checking every page."],
    benefits: ["See page thumbnails instead of working from numbers alone.", "Use keyboard-accessible move controls as an alternative to dragging.", "Rebuild page order without recreating the source document."],
    useCases: ["Correct pages scanned in the wrong sequence.", "Move a contents page or cover to the beginning.", "Arrange presentation handouts into the intended reading order."],
    bestResult: "Use the thumbnail preview to verify distinctive headings, page numbers, and orientation before exporting the final order.",
    extraFaq: { question: "Does reordering remove any PDF pages?", answer: "No. The organizer changes sequence; use Delete PDF Pages separately if you also need to remove content." },
    related: [toolLink("delete-pages", "Delete PDF Pages"), toolLink("rotate", "Rotate PDF"), toolLink("merge", "Merge PDF")]
  }),

  "ocr-pdf": defineTool({
    heading: "OCR PDF Online for Searchable Scanned Documents",
    name: "OCR PDF",
    input: "a scanned PDF document",
    output: "a searchable PDF and, when selected, a separate text file",
    about: "OCR PDF applies optical character recognition to pages that contain photographed or scanned text. It can recognize English, Hindi, or mixed English and Hindi content, adding a searchable text layer while retaining a PDF output.",
    steps: ["Upload a scanned PDF and select the document language.", "Choose whether you also want a separate text export, then start OCR.", "Wait for the progress steps to complete and download the searchable PDF or text file."],
    benefits: ["Search and select text that was previously stored only as an image.", "Choose English, Hindi, mixed-language, or orientation detection options.", "Create a sidecar text file for copying or downstream review."],
    useCases: ["Make archived letters searchable.", "Extract draft text from scanned forms or receipts.", "Improve discovery inside scanned reports and research material."],
    bestResult: "Use a clear, upright scan with good contrast and choose the correct language. Always proofread names, numbers, and tables after OCR.",
    extraFaq: { question: "Is OCR text always accurate?", answer: "No. Accuracy depends on scan quality, language, fonts, handwriting, and page layout, so important output needs human review." },
    related: [toolLink("pdf-to-word", "PDF to Word"), toolLink("compress", "Compress PDF"), toolLink("rotate", "Rotate PDF")]
  }),

  "pdf-to-jpg": defineTool({
    heading: "Convert PDF to JPG Images Online",
    name: "PDF to JPG",
    input: "one PDF file",
    output: "a ZIP archive containing a JPG image for each PDF page",
    about: "PDF to JPG renders every page of a PDF as a separate image. The images are bundled into one ZIP download, making multi-page documents easier to use in slide decks, image viewers, content previews, or systems that do not accept PDF files.",
    steps: ["Upload the PDF whose pages you want to convert.", "Start the conversion and allow every page to render as a JPG.", "Download the ZIP file and extract it to access the page images."],
    benefits: ["Convert all pages in one operation.", "Receive familiar JPG files for broad compatibility.", "Keep page order through consistently named images inside the ZIP."],
    useCases: ["Add a PDF page to a presentation as an image.", "Create image previews for a document library.", "Share individual pages with someone who cannot open PDFs."],
    bestResult: "Start with a clear PDF and remember that selectable text becomes pixels in the JPG. Use OCR or PDF to Word when editable text is the goal.",
    extraFaq: { question: "Why does PDF to JPG download a ZIP file?", answer: "A PDF can contain many pages, so the tool packages all page images together for one convenient download." },
    related: [toolLink("images-to-pdf", "Images to PDF"), toolLink("pdf-to-word", "PDF to Word"), toolLink("split", "Split PDF")]
  }),

  "images-to-pdf": defineTool({
    heading: "Convert JPG and PNG Images to PDF Online",
    name: "Images to PDF",
    input: "one or more JPG or PNG images",
    output: "one PDF containing the uploaded images",
    about: "Images to PDF combines photographs, scans, screenshots, and other JPG or PNG files into a single PDF. It is the flexible choice when the image set contains both formats or when several pages need to become one shareable document.",
    steps: ["Select one or more JPG or PNG files from your device.", "Review the selected images and remove any files you do not want included.", "Convert the set and download the combined PDF."],
    benefits: ["Mix JPG and PNG source files in one conversion.", "Combine multiple image pages into one document.", "Create a PDF that is easier to send, print, or archive than loose images."],
    useCases: ["Turn photographed receipts into one expense document.", "Combine scanned forms into a PDF packet.", "Package screenshots or portfolio images for sharing."],
    bestResult: "Use upright, high-resolution images and select them in the intended document sequence. Very large photos can create a large PDF.",
    extraFaq: { question: "Can I mix JPG and PNG images in the same PDF?", answer: "Yes. The combined image converter accepts both formats in one upload selection." },
    related: [toolLink("jpg-to-pdf", "JPG to PDF"), toolLink("png-to-pdf", "PNG to PDF"), toolLink("pdf-to-jpg", "PDF to JPG")]
  }),

  "jpg-to-pdf": defineTool({
    heading: "Convert JPG Images to PDF Online",
    name: "JPG to PDF",
    input: "one or more JPG or JPEG images",
    output: "a single PDF made from the selected images",
    about: "JPG to PDF turns common JPEG photographs and scans into a document that is easier to print and share. Multiple images can be combined into one PDF, making this useful for camera-captured paperwork or page-by-page JPG exports.",
    steps: ["Choose the JPG or JPEG images you want in the document.", "Review the selected files and remove any accidental choices.", "Convert the images and download the resulting PDF."],
    benefits: ["Package several JPEG files into one attachment.", "Create a standard document from phone photos or scans.", "Preserve the source images while producing a separate PDF."],
    useCases: ["Combine photographed notes into a printable PDF.", "Submit identity or application pages as one document.", "Archive a sequence of JPEG scans together."],
    bestResult: "Crop and rotate photos before upload, use readable resolution, and select images in the order you want them to appear.",
    extraFaq: { question: "Is JPG the same as JPEG for this converter?", answer: "Yes. JPG and JPEG are filename extensions for the same image format and are accepted by the combined image workflow." },
    related: [toolLink("png-to-pdf", "PNG to PDF"), toolLink("images-to-pdf", "Images to PDF"), toolLink("pdf-to-jpg", "PDF to JPG")]
  }),

  "png-to-pdf": defineTool({
    heading: "Convert PNG Images to PDF Online",
    name: "PNG to PDF",
    input: "one or more PNG images",
    output: "a single PDF made from the selected PNG files",
    about: "PNG to PDF converts screenshots, diagrams, interface captures, and lossless scans into a convenient document. It is especially useful when sharp text or graphics are already stored as PNG files and need to be grouped for sharing or printing.",
    steps: ["Choose one or more PNG files from your device.", "Review the selected image list and remove files that do not belong.", "Convert the images and download the finished PDF."],
    benefits: ["Combine multiple lossless images into one file.", "Turn screenshots into a document that follows page order.", "Use a widely supported PDF for distribution or printing."],
    useCases: ["Bundle product screenshots into a review document.", "Convert diagrams or charts into a printable packet.", "Combine scanned PNG pages for a single submission."],
    bestResult: "Use PNGs with clear dimensions and readable text. Arrange the source filenames or selection order carefully before conversion.",
    extraFaq: { question: "Will PNG transparency remain transparent in the PDF?", answer: "PDF page rendering may place transparent areas on a page background, so inspect the downloaded result if transparency is important." },
    related: [toolLink("jpg-to-pdf", "JPG to PDF"), toolLink("images-to-pdf", "Images to PDF"), toolLink("pdf-to-jpg", "PDF to JPG")]
  }),

  "word-to-pdf": defineTool({
    heading: "Convert Word Documents to PDF Online",
    name: "Word to PDF",
    input: "one DOC or DOCX document",
    output: "a PDF version of the Word document",
    about: "Word to PDF converts a Microsoft Word document into a fixed-layout PDF for distribution, printing, or submission. A PDF is useful when recipients should see a consistent document rather than edit the original DOC or DOCX file.",
    steps: ["Upload a DOC or DOCX file.", "Start the conversion and wait while the document is rendered to PDF.", "Download the PDF and check fonts, spacing, page breaks, and images."],
    benefits: ["Create a shareable format from an editable document.", "Reduce accidental changes by distributing a PDF copy.", "Prepare Word files for systems that request PDF uploads."],
    useCases: ["Export a résumé or cover letter for an application.", "Share a report while preserving its page layout.", "Create a printable PDF from a Word template."],
    bestResult: "Use standard fonts, resolve tracked changes, and confirm page breaks in Word before uploading. Review the converted PDF for font substitutions.",
    extraFaq: { question: "Will Word formatting be preserved exactly?", answer: "Most conventional layouts convert well, but unavailable fonts, floating objects, and complex fields can render differently, so review the PDF." },
    related: [toolLink("pdf-to-word", "PDF to Word"), toolLink("excel-to-pdf", "Excel to PDF"), toolLink("compress", "Compress PDF")]
  }),

  "excel-to-pdf": defineTool({
    heading: "Convert Excel Spreadsheets to PDF Online",
    name: "Excel to PDF",
    input: "one XLS or XLSX workbook",
    output: "a PDF rendered from the spreadsheet",
    about: "Excel to PDF creates a fixed document from an XLS or XLSX workbook. It is useful for sharing tables, schedules, and reports when recipients need a printable view instead of formulas or editable spreadsheet cells.",
    steps: ["Upload an XLS or XLSX workbook.", "Convert the spreadsheet with the current print and page settings.", "Download the PDF and inspect every sheet, column, and page break."],
    benefits: ["Share spreadsheet information in a non-editable format.", "Create a printable version for records or approval.", "Use PDF where a portal does not accept Excel workbooks."],
    useCases: ["Publish a budget summary without exposing formulas.", "Send a schedule or inventory report for review.", "Archive a dated snapshot of spreadsheet results."],
    bestResult: "Set print areas, orientation, scaling, and page breaks in Excel first. Wide sheets may otherwise span several PDF pages.",
    extraFaq: { question: "Does Excel to PDF recalculate formulas?", answer: "The converter renders the workbook it receives. Save the spreadsheet with current calculated values before uploading." },
    related: [toolLink("pdf-to-excel", "PDF to Excel"), toolLink("word-to-pdf", "Word to PDF"), toolLink("compress", "Compress PDF")]
  }),

  "pdf-to-word": defineTool({
    heading: "Convert PDF to Word Online",
    name: "PDF to Word",
    input: "one digital or scanned PDF",
    output: "a DOCX using automatic, layout, image, OCR, or text mode",
    about: "PDF to Word creates a DOCX for editing or reuse. Choose layout mode for digital PDFs, image mode when visual fidelity matters, OCR mode for editable text from scans, text mode for a simpler extraction, or automatic mode for a practical default.",
    steps: ["Upload the PDF and identify whether it contains digital text or scanned pages.", "Select the Word conversion mode that matches your editing and layout needs.", "Convert, download the DOCX, and proofread the content and formatting."],
    benefits: ["Choose between editable text and visual page preservation.", "Handle digital PDFs and scanned material with different modes.", "Move document content into a familiar Word workflow."],
    useCases: ["Revise text from an old PDF report.", "Create a Word draft from a scanned document using OCR.", "Preserve scanned page appearance inside a DOCX."],
    bestResult: "Use layout mode for born-digital PDFs and OCR for clear scans. Complex columns, tables, handwriting, and decorative fonts require manual checking.",
    extraFaq: { question: "Which PDF to Word mode should I choose?", answer: "Start with Auto. Choose Layout for digital text, Image for visual fidelity, OCR for editable scanned text, or Text for plain extraction." },
    related: [toolLink("word-to-pdf", "Word to PDF"), toolLink("ocr-pdf", "OCR PDF"), toolLink("pdf-to-jpg", "PDF to JPG")]
  }),

  "pdf-to-excel": defineTool({
    heading: "Convert PDF Tables to Excel Online",
    name: "PDF to Excel",
    input: "one digital PDF containing recognizable tables",
    output: "an XLSX workbook containing extracted table data",
    about: "PDF to Excel extracts tabular content from a digital PDF into an XLSX spreadsheet. It is intended for structured rows and columns that need sorting, checking, or further calculation—not for reproducing every visual element of the original page.",
    steps: ["Upload a digital PDF that contains clearly defined tables.", "Start extraction and let the tool identify tabular regions.", "Download the XLSX workbook and verify headings, rows, numeric values, and sheet structure."],
    benefits: ["Avoid retyping well-structured tables by hand.", "Move extracted data into spreadsheet filters and formulas.", "Create an editable starting point from a PDF report."],
    useCases: ["Extract financial statement tables for analysis.", "Move inventory or schedule data into Excel.", "Reuse research tables in a working spreadsheet."],
    bestResult: "Use a born-digital PDF with visible grid structure. Scans, merged cells, footnotes, and multi-column layouts can reduce extraction accuracy.",
    extraFaq: { question: "Can PDF to Excel convert scanned tables?", answer: "This workflow is best for digital PDFs. Run OCR first for a scan, then expect to clean and validate the extracted spreadsheet." },
    related: [toolLink("pdf-to-csv", "PDF to CSV"), toolLink("excel-to-pdf", "Excel to PDF"), toolLink("ocr-pdf", "OCR PDF")]
  }),

  "pdf-to-csv": defineTool({
    heading: "Convert PDF Tables to CSV Online",
    name: "PDF to CSV",
    input: "one digital PDF containing tabular data",
    output: "a CSV file, or a ZIP when the PDF produces multiple CSV tables",
    about: "PDF to CSV extracts rows and columns into a lightweight, plain-text data format. CSV is useful for importing data into spreadsheets, databases, analytics tools, and scripts when visual PDF formatting is less important than reusable values.",
    steps: ["Upload a digital PDF with a clear table structure.", "Run the table extraction and wait for the data files to be prepared.", "Download the CSV or ZIP and validate delimiters, headings, rows, and numeric values."],
    benefits: ["Create portable data for many spreadsheet and database tools.", "Avoid manual copying from straightforward PDF tables.", "Receive multiple extracted tables together when needed."],
    useCases: ["Import statement rows into an analysis workflow.", "Move catalog or reference tables into a database.", "Create a lightweight data file from a PDF report."],
    bestResult: "Choose a digital PDF with consistent rows and columns. Review dates, decimal separators, wrapped cells, and headers before using the data.",
    extraFaq: { question: "Why did I receive a ZIP instead of one CSV?", answer: "When several separate tables are detected, the converter can package multiple CSV files together in one ZIP download." },
    related: [toolLink("pdf-to-excel", "PDF to Excel"), toolLink("excel-to-pdf", "Excel to PDF"), toolLink("ocr-pdf", "OCR PDF")]
  })
};

export function getSeoContent(pageKey) {
  return SEO_CONTENT[pageKey] || SEO_CONTENT.home;
}

export function countSeoWords(content) {
  const text = [
    ...content.about,
    ...content.steps,
    ...content.benefits,
    ...content.useCases,
    ...content.faqs.flatMap((item) => [item.question, item.answer]),
    ...content.related.map((item) => item.label)
  ].join(" ");

  return text.trim().split(/\s+/).filter(Boolean).length;
}
