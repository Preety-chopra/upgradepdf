import axios from "axios";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000
});

export function buildAbsoluteUrl(relativeUrl) {
  if (!relativeUrl) {
    return null;
  }

  if (relativeUrl.startsWith("http://") || relativeUrl.startsWith("https://")) {
    return relativeUrl;
  }

  return `${API_BASE_URL}${relativeUrl}`;
}

export async function getJob(jobId) {
  const response = await apiClient.get(`/api/jobs/${jobId}`);
  return response.data;
}

export async function submitMerge(files, onUploadProgress) {
  const formData = new FormData();

  files.forEach((file) => {
    formData.append("files", file);
  });

  const response = await apiClient.post("/api/pdf/merge", formData, {
    headers: {
      "Content-Type": "multipart/form-data"
    },
    onUploadProgress
  });

  return response.data;
}

export async function submitCompress(file, quality, onUploadProgress) {
  const formData = new FormData();

  formData.append("file", file);
  formData.append("quality", quality);

  const response = await apiClient.post("/api/pdf/compress", formData, {
    headers: {
      "Content-Type": "multipart/form-data"
    },
    onUploadProgress
  });

  return response.data;
}

export async function submitSplit(file, pages, onUploadProgress) {
  const formData = new FormData();

  formData.append("file", file);
  formData.append("pages", pages);

  const response = await apiClient.post("/api/pdf/split", formData, {
    headers: {
      "Content-Type": "multipart/form-data"
    },
    onUploadProgress
  });

  return response.data;
}

export async function submitRotate(file, pages, angle, onUploadProgress) {
  const formData = new FormData();

  formData.append("file", file);
  formData.append("pages", pages);
  formData.append("angle", angle);

  const response = await apiClient.post("/api/pdf/rotate", formData, {
    headers: {
      "Content-Type": "multipart/form-data"
    },
    onUploadProgress
  });

  return response.data;
}

export async function submitDeletePages(file, pages, onUploadProgress) {
  const formData = new FormData();

  formData.append("file", file);
  formData.append("pages", pages);

  const response = await apiClient.post("/api/pdf/delete-pages", formData, {
    headers: {
      "Content-Type": "multipart/form-data"
    },
    onUploadProgress
  });

  return response.data;
}
