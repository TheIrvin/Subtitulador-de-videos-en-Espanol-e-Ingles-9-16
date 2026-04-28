export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export function resolveMediaUrl(path) {
  if (!path) return "";
  return path.startsWith("http") ? path : `${API_BASE_URL}${path}`;
}

export async function uploadVideo(file) {
  const formData = new FormData();
  formData.append("video", file);

  const response = await fetch(`${API_BASE_URL}/api/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("No se pudo subir el video.");
  }

  return response.json();
}

export async function getProject(projectId) {
  const response = await fetch(`${API_BASE_URL}/api/project/${projectId}`);

  if (!response.ok) {
    throw new Error("No se pudo cargar el proyecto.");
  }

  return response.json();
}

export async function getProjectHistory() {
  const response = await fetch(`${API_BASE_URL}/api/history`);

  if (!response.ok) {
    throw new Error("No se pudo cargar el historial.");
  }

  return response.json();
}

export async function deleteProjectHistory(projectId) {
  const response = await fetch(`${API_BASE_URL}/api/history/${projectId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "No se pudo eliminar del historial.");
  }

  return response.json();
}

export async function saveBlocks(projectId, blocks) {
  const response = await fetch(`${API_BASE_URL}/api/project/${projectId}/blocks`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ blocks }),
  });

  if (!response.ok) {
    throw new Error("No se pudieron guardar los cambios.");
  }

  return response.json();
}

export async function transcribeProject(projectId) {
  const response = await fetch(`${API_BASE_URL}/api/transcribe/${projectId}`, {
    method: "POST",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "No se pudo transcribir el video.");
  }

  return response.json();
}

export async function generateSubtitles(projectId) {
  const response = await fetch(`${API_BASE_URL}/api/generate-subtitles/${projectId}`, {
    method: "POST",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "No se pudieron generar los subtitulos.");
  }

  return response.json();
}

export async function translateProject(projectId) {
  const response = await fetch(`${API_BASE_URL}/api/translate/${projectId}`, {
    method: "POST",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "No se pudieron generar los subtitulos en ingles.");
  }

  return response.json();
}

export async function applyManualSubtitles(projectId, textEs, textEn) {
  const response = await fetch(`${API_BASE_URL}/api/manual-subtitles/${projectId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text_es: textEs, text_en: textEn }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "No se pudo aplicar el texto manual.");
  }

  return response.json();
}

export async function exportProject(projectId, options = {}) {
  const response = await fetch(`${API_BASE_URL}/api/export/${projectId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(options),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "No se pudo generar el archivo ASS.");
  }

  return response.json();
}

export function getDownloadUrl(projectId) {
  return `${API_BASE_URL}/api/download/${projectId}`;
}

export function getMp3DownloadUrl(projectId) {
  return `${API_BASE_URL}/api/download/${projectId}/mp3`;
}
