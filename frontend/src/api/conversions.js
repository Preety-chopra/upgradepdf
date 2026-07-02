const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function filenameFromDisposition(disposition, fallback) {
  if (!disposition) return fallback;
  const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) return decodeURIComponent(utf8Match[1]);
  const normalMatch = disposition.match(/filename="?([^";]+)"?/i);
  return normalMatch?.[1] || fallback;
}

export async function runConversion({ endpoint, files, fields = {}, fallbackFilename }) {
  const formData = new FormData();

  if (Array.isArray(files)) {
    files.forEach((file) => formData.append('files', file));
  } else {
    formData.append('file', files);
  }

  Object.entries(fields).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      formData.append(key, value);
    }
  });

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let message = `Conversion failed with status ${response.status}`;
    try {
      const error = await response.json();
      message = error.detail || message;
    } catch (_) {
      // Keep fallback message.
    }
    throw new Error(message);
  }

  const blob = await response.blob();
  const disposition = response.headers.get('content-disposition');
  const filename = filenameFromDisposition(disposition, fallbackFilename || 'converted-file');

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
