<template>
  <main class="home-page">
    <section class="hero-section">
      <h1>PDF Utility Platform</h1>
    </section>

    <section class="tools-grid">
      <RouterLink class="tool-card" to="/tools/merge">
        <span class="tool-icon">🔗</span>
        <h3>Merge PDF</h3>
        <p>Combine multiple PDFs into one file.</p>
      </RouterLink>

      <RouterLink class="tool-card" to="/tools/split">
        <span class="tool-icon">✂️</span>
        <h3>Split PDF</h3>
        <p>Split PDF pages or extract selected ranges.</p>
      </RouterLink>

      <RouterLink class="tool-card" to="/tools/compress">
        <span class="tool-icon">🗜️</span>
        <h3>Compress PDF</h3>
        <p>Reduce file size while keeping readable quality.</p>
      </RouterLink>

      <RouterLink class="tool-card" to="/tools/delete-pages">
        <span class="tool-icon">🗑️</span>
        <h3>Delete Pages</h3>
        <p>Remove unwanted pages from a PDF.</p>
      </RouterLink>

      <RouterLink class="tool-card" to="/tools/reorder-pages">
        <span class="tool-icon">↕️</span>
        <h3>Reorder Pages</h3>
        <p>Rearrange pages visually and export a new PDF.</p>
      </RouterLink>

      <RouterLink class="tool-card" to="/convert?type=pdf-to-jpg">
        <div class="tool-icon">🖼️</div>
        <h3>PDF to JPG</h3>
        <p>Convert PDF pages into JPG images.</p>
      </RouterLink>

      <RouterLink class="tool-card" to="/convert?type=images-to-pdf">
        <div class="tool-icon">📄</div>
        <h3>JPG / PNG to PDF</h3>
        <p>Create a PDF from image files.</p>
      </RouterLink>

      <RouterLink class="tool-card" to="/convert?type=word-to-pdf">
        <div class="tool-icon">📝</div>
        <h3>Word to PDF</h3>
        <p>Convert DOC/DOCX files into PDF.</p>
      </RouterLink>

      <RouterLink class="tool-card" to="/convert?type=excel-to-pdf">
        <div class="tool-icon">📊</div>
        <h3>Excel to PDF</h3>
        <p>Convert XLS/XLSX spreadsheets into PDF.</p>
      </RouterLink>

      <RouterLink class="tool-card" to="/convert?type=pdf-to-word">
        <div class="tool-icon">🔁</div>
        <h3>PDF to Word</h3>
        <p>Convert PDF into editable Word format.</p>
      </RouterLink>

      <RouterLink class="tool-card" to="/convert?type=pdf-to-excel">
        <div class="tool-icon">📑</div>
        <h3>PDF to Excel / CSV</h3>
        <p>Extract tables from PDF into Excel or CSV.</p>
      </RouterLink>

      <RouterLink class="tool-card ocr-card" to="/tools/ocr-pdf">
        <div class="tool-icon">🔍</div>
        <h3>Scanned PDF OCR</h3>
        <p>Upload scanned PDFs and generate searchable PDFs.</p>
      </RouterLink>

      <RouterLink class="tool-card ocr-card" to="/tools/ocr-pdf">
        <div class="tool-icon">🌐</div>
        <h3>OCR Language Selection</h3>
        <p>Select English, Hindi, or mixed language OCR.</p>
      </RouterLink>

      <RouterLink class="tool-card ocr-card" to="/tools/ocr-pdf">
        <div class="tool-icon">📥</div>
        <h3>Searchable PDF Output</h3>
        <p>Download OCR-processed searchable PDF files.</p>
      </RouterLink>

      <RouterLink class="tool-card ocr-card" to="/tools/ocr-pdf">
        <div class="tool-icon">📃</div>
        <h3>Text Export</h3>
        <p>Export OCR text separately as a text file.</p>
      </RouterLink>
    </section>
  </main>
</template>

<style scoped>
.home-page {
  min-height: 100vh;
  padding: 42px 24px 70px;
  background:
    radial-gradient(circle at top left, rgba(37, 99, 235, 0.12), transparent 30%),
    linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
  color: #0f172a;
}

.hero-section {
  max-width: 1120px;
  margin: 0 auto 34px;
  text-align: center;
}

.eyebrow {
  margin: 0 0 8px;
  color: #2563eb;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.hero-section h1 {
  margin: 0;
  font-size: clamp(36px, 6vw, 62px);
  letter-spacing: -0.05em;
}

.hero-section p {
  color: #64748b;
  font-size: 18px;
}

.tools-grid {
  max-width: 1120px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(245px, 1fr));
  gap: 20px;
}

.tool-card {
  min-height: 190px;
  padding: 24px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #e2e8f0;
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08);
  color: inherit;
  text-decoration: none;
  transition: 0.2s ease;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.tool-card:hover {
  transform: translateY(-5px);
  border-color: #93c5fd;
  box-shadow: 0 24px 58px rgba(15, 23, 42, 0.14);
}

.tool-icon {
  width: 48px;
  height: 48px;
  margin-bottom: 16px;
  border-radius: 16px;
  background: #eff6ff;
  display: grid;
  place-items: center;
  font-size: 24px;
}

.tool-card h3 {
  margin: 0 0 10px;
  font-size: 21px;
}

.tool-card p {
  margin: 0;
  color: #64748b;
  line-height: 1.55;
}

.tool-card small {
  margin-bottom: 8px;
  color: #2563eb;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.module-card {
  border-color: #bfdbfe;
  background: linear-gradient(180deg, #ffffff 0%, #eff6ff 100%);
}

.module-card.cyan {
  border-color: #a5f3fc;
  background: linear-gradient(180deg, #ffffff 0%, #ecfeff 100%);
}
</style>
