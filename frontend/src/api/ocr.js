const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function filenameFromDisposition(disposition, fallback) {
  if (!disposition) return fallback;
  const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) return decodeURIComponent(utf8Match[1]);
  const normalMatch = disposition.match(/filename="?([^";]+)"?/i);
  return normalMatch?.[1] || fallback;
}

async function parseError(response, fallback) {
  try {
    const data = await response.json();
    return data.detail || fallback;
  } catch (_) {
    return fallback;
  }
}

export async function fetchOcrLanguages() {
  const response = await fetch(`${API_BASE_URL}/api/ocr/languages`);
  if (!response.ok) {
    throw new Error(await parseError(response, 'Unable to load OCR languages.'));
  }
  return response.json();
}

export async function createOcrJob({ file, language, exportText, deskew, rotatePages, forceOcr, timeoutSeconds }) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('language', language || 'eng');
  formData.append('export_text', exportText ? 'true' : 'false');
  formData.append('deskew', deskew ? 'true' : 'false');
  formData.append('rotate_pages', rotatePages ? 'true' : 'false');
  formData.append('force_ocr', forceOcr ? 'true' : 'false');
  formData.append('timeout_seconds', String(timeoutSeconds || 1200));

  const response = await fetch(`${API_BASE_URL}/api/ocr/jobs`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await parseError(response, 'Unable to create OCR job.'));
  }
  return response.json();
}

export async function fetchOcrStatus(jobId) {
  const response = await fetch(`${API_BASE_URL}/api/ocr/jobs/${jobId}`);
  if (!response.ok) {
    throw new Error(await parseError(response, 'Unable to get OCR status.'));
  }
  return response.json();
}

export async function downloadOcrOutput(jobId, fileType) {
  const response = await fetch(`${API_BASE_URL}/api/ocr/jobs/${jobId}/download?file_type=${fileType}`);
  if (!response.ok) {
    throw new Error(await parseError(response, 'Unable to download OCR output.'));
  }

  const blob = await response.blob();
  const disposition = response.headers.get('content-disposition');
  const filename = filenameFromDisposition(disposition, fileType === 'text' ? 'ocr.txt' : 'searchable.pdf');

  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(url);

  return filename;
}
