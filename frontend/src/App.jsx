import React, { useEffect, useMemo, useRef, useState } from "react";
import { Download, FileVideo, FolderOpen, Sparkles } from "lucide-react";
import {
  applyManualSubtitles,
  deleteProjectHistory,
  exportProject,
  getDownloadUrl,
  getMp3DownloadUrl,
  getProject,
  getProjectHistory,
  resolveMediaUrl,
  saveBlocks,
  translateProject,
  transcribeProject,
  uploadVideo,
} from "./api.js";
import ManualScriptPanel from "./components/ManualScriptPanel.jsx";
import ProjectHistory from "./components/ProjectHistory.jsx";
import SubtitleBlockList from "./components/SubtitleBlockList.jsx";
import SubtitleEditorPanel from "./components/SubtitleEditorPanel.jsx";
import VideoPreview from "./components/VideoPreview.jsx";

export default function App() {
  const fileInputRef = useRef(null);
  const [projectId, setProjectId] = useState("");
  const [videoUrl, setVideoUrl] = useState("");
  const [blocks, setBlocks] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [currentTime, setCurrentTime] = useState(0);
  const [status, setStatus] = useState("Listo para iniciar.");
  const [isGenerating, setIsGenerating] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [isPreviewPlaying, setIsPreviewPlaying] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState("");
  const [mp3DownloadUrl, setMp3DownloadUrl] = useState("");
  const [exportName, setExportName] = useState("");
  const [exportFolder, setExportFolder] = useState("");
  const [exportQuality, setExportQuality] = useState("media");
  const [shouldExportMp3, setShouldExportMp3] = useState(false);
  const [coverTime, setCoverTime] = useState(0);
  const [manualTextEs, setManualTextEs] = useState("");
  const [manualTextEn, setManualTextEn] = useState("");
  const [historyProjects, setHistoryProjects] = useState([]);

  const activeBlock = useMemo(
    () => blocks.find((block) => currentTime >= block.start && currentTime < block.end) || null,
    [blocks, currentTime],
  );

  const selectedBlock = useMemo(
    () => blocks.find((block) => block.id === selectedId) || activeBlock || blocks[0] || null,
    [activeBlock, blocks, selectedId],
  );

  const overlayBlock = activeBlock || (isPreviewPlaying ? null : selectedBlock);
  const isBusy = isGenerating || isExporting;

  useEffect(() => {
    refreshHistory();
  }, []);

  async function refreshHistory() {
    try {
      const history = await getProjectHistory();
      setHistoryProjects(history.projects || []);
    } catch (error) {
      setStatus(error.message);
    }
  }

  function hydrateProject(project) {
    setProjectId(project.project_id);
    setVideoUrl(resolveMediaUrl(project.video_url));
    setBlocks(project.blocks || []);
    setSelectedId(project.blocks?.[0]?.id || "");
    setDownloadUrl(project.output_path ? getDownloadUrl(project.project_id) : "");
    setMp3DownloadUrl(project.mp3_path ? getMp3DownloadUrl(project.project_id) : "");
    setExportName(project.export_name || "");
    setExportFolder(project.export_root || "");
    setExportQuality(project.export_quality || "media");
    setStatus(project.status || "Proyecto cargado.");
  }

  async function handleOpenHistoryProject(projectIdToOpen) {
    try {
      setStatus("Abriendo proyecto...");
      const project = await getProject(projectIdToOpen);
      hydrateProject(project);
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function handleDeleteHistoryProject(project) {
    const confirmed = window.confirm(`¿Seguro que quieres eliminar "${project.title || "este proyecto"}" del historial?`);
    if (!confirmed) return;

    try {
      await deleteProjectHistory(project.project_id);
      await refreshHistory();
      if (project.project_id === projectId) {
        setStatus("Proyecto eliminado del historial. El proyecto actual sigue abierto.");
      } else {
        setStatus("Proyecto eliminado del historial.");
      }
    } catch (error) {
      setStatus(error.message);
    }
  }

  function buildWordsForBlock(text, start, end) {
    const words = String(text || "").trim().split(/\s+/).filter(Boolean);
    if (!words.length) return [];

    const duration = Math.max(Number(end) - Number(start), 0.01);
    const secondsPerWord = duration / words.length;

    return words.map((word, index) => ({
      word: word.toUpperCase(),
      start: Number((Number(start) + index * secondsPerWord).toFixed(2)),
      end: Number((Number(start) + (index + 1) * secondsPerWord).toFixed(2)),
    }));
  }

  async function handleUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setStatus("Subiendo video...");
      const upload = await uploadVideo(file);
      const project = await getProject(upload.project_id);

      hydrateProject(project);
      await refreshHistory();
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function handleGenerateSpanish() {
    if (!projectId) {
      setStatus("Sube un video antes de generar espanol.");
      return;
    }

    try {
      setIsGenerating(true);
      setStatus("Transcribiendo espanol...");
      await transcribeProject(projectId);

      const project = await getProject(projectId);

      setBlocks(project.blocks || []);
      setSelectedId(project.blocks?.[0]?.id || "");
      setDownloadUrl("");
      setMp3DownloadUrl("");
      setStatus(project.status || "Subtitulos en espanol generados");
      await refreshHistory();
    } catch (error) {
      setStatus(error.message);
    } finally {
      setIsGenerating(false);
    }
  }

  async function handleGenerateEnglish() {
    if (!projectId) {
      setStatus("Genera espanol antes de generar ingles.");
      return;
    }

    try {
      setIsGenerating(true);
      setStatus("Traduciendo a ingles...");
      await translateProject(projectId);

      const project = await getProject(projectId);

      setBlocks(project.blocks || []);
      setSelectedId(project.blocks?.[0]?.id || "");
      setDownloadUrl("");
      setMp3DownloadUrl("");
      setStatus(project.status || "Subtitulos en ingles generados");
      await refreshHistory();
    } catch (error) {
      setStatus(error.message);
    } finally {
      setIsGenerating(false);
    }
  }

  async function handleApplyManualText() {
    if (!projectId) {
      setStatus("Sube un video antes de aplicar texto manual.");
      return;
    }

    if (!manualTextEs.trim()) {
      setStatus("Pega el texto en espanol antes de aplicarlo.");
      return;
    }

    try {
      setIsGenerating(true);
      setStatus("Detectando tiempos y aplicando texto manual...");
      if (blocks.length) {
        await saveBlocks(projectId, blocks);
      }
      await applyManualSubtitles(projectId, manualTextEs, manualTextEn);

      const project = await getProject(projectId);

      setBlocks(project.blocks || []);
      setSelectedId(project.blocks?.[0]?.id || "");
      setDownloadUrl("");
      setMp3DownloadUrl("");
      setStatus(project.status || "Texto manual aplicado");
      await refreshHistory();
    } catch (error) {
      setStatus(error.message);
    } finally {
      setIsGenerating(false);
    }
  }

  function handleBlockChange(updatedBlock) {
    setBlocks((current) =>
      current.map((block) => {
        if (block.id !== updatedBlock.id) return block;

        if (updatedBlock.text_es !== block.text_es) {
          return {
            ...updatedBlock,
            text_es: updatedBlock.text_es.toUpperCase(),
            words: buildWordsForBlock(updatedBlock.text_es, updatedBlock.start, updatedBlock.end),
            translation_outdated: true,
            translation_warning: false,
            x: updatedBlock.x ?? 540,
          };
        }

        return { ...updatedBlock, x: updatedBlock.x ?? 540 };
      }),
    );
    setSelectedId(updatedBlock.id);
    setStatus("Cambios pendientes.");
  }

  function createEmptyBlock(sourceBlock, start, end, index) {
    return {
      id: `block_${String(index + 1).padStart(3, "0")}`,
      chain_index: sourceBlock.chain_index,
      start: Number(start.toFixed(2)),
      end: Number(end.toFixed(2)),
      text_es: "",
      text_en: "",
      font_size_es: sourceBlock.font_size_es ?? 64,
      font_size_en: sourceBlock.font_size_en ?? 70,
      y_es: sourceBlock.y_es ?? 1540,
      y_en: sourceBlock.y_en ?? 1440,
      x: sourceBlock.x ?? 540,
      words: [],
      translation_warning: false,
      translation_outdated: false,
    };
  }

  function renumberBlocks(nextBlocks) {
    return nextBlocks.map((block, index) => ({ ...block, id: `block_${String(index + 1).padStart(3, "0")}` }));
  }

  function handleAddBlockAfter(blockId) {
    const blockIndex = blocks.findIndex((block) => block.id === blockId);
    if (blockIndex < 0) return;

    const sourceBlock = blocks[blockIndex];
    const start = Number(sourceBlock.start);
    const end = Number(sourceBlock.end);
    const duration = Math.max(end - start, 0.2);
    const splitTime = Number((start + duration / 2).toFixed(2));

    const updatedSource = {
      ...sourceBlock,
      end: splitTime,
      words: buildWordsForBlock(sourceBlock.text_es, start, splitTime),
    };
    const emptyBlock = createEmptyBlock(sourceBlock, splitTime, end, blockIndex + 1);
    const nextBlocks = renumberBlocks([
      ...blocks.slice(0, blockIndex),
      updatedSource,
      emptyBlock,
      ...blocks.slice(blockIndex + 1),
    ]);

    const insertedId = nextBlocks[blockIndex + 1].id;
    setBlocks(nextBlocks);
    setSelectedId(insertedId);
    setStatus("Bloque vacio agregado. Ajusta el texto y guarda cambios.");
  }

  async function handleSave() {
    if (!projectId) {
      setStatus("Sube un video antes de guardar.");
      return;
    }

    try {
      setStatus("Guardando cambios...");
      const project = await saveBlocks(projectId, blocks);
      setBlocks(project.blocks);
      setStatus(project.status || "Cambios guardados.");
      await refreshHistory();
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function handleExport() {
    if (!projectId) {
      setStatus("Sube un video antes de exportar.");
      return;
    }

    if (!exportFolder.trim()) {
      setStatus("Elige una carpeta antes de exportar.");
      return;
    }

    try {
      setIsExporting(true);
      setDownloadUrl("");
      setMp3DownloadUrl("");
      setStatus("Exportando video...");
      await saveBlocks(projectId, blocks);
      await exportProject(projectId, {
        name: exportName,
        quality: exportQuality,
        export_mp3: shouldExportMp3,
        cover_time: coverTime,
        output_dir: exportFolder,
      });
      const project = await getProject(projectId);
      setDownloadUrl(getDownloadUrl(projectId));
      setMp3DownloadUrl(project.mp3_path ? getMp3DownloadUrl(projectId) : "");
      setStatus(project.status || "Video exportado correctamente");
      await refreshHistory();
    } catch (error) {
      setStatus(error.message);
    } finally {
      setIsExporting(false);
    }
  }

  async function handleChooseExportFolder() {
    if (window.subtitleDesktop?.chooseExportFolder) {
      const folder = await window.subtitleDesktop.chooseExportFolder();
      if (folder) {
        setExportFolder(folder);
        setStatus(`Carpeta de exportacion: ${folder}`);
      }
      return;
    }

    const folder = window.prompt("Ruta donde guardar exports", exportFolder);
    if (folder !== null) {
      setExportFolder(folder.trim());
    }
  }

  return (
    <main className="app-shell">
      <div className="editor-grid">
        <div className="left-column">
          <ProjectHistory
            activeProjectId={projectId}
            projects={historyProjects}
            onDelete={handleDeleteHistoryProject}
            onOpen={handleOpenHistoryProject}
          />
          <SubtitleBlockList
            blocks={blocks}
            selectedId={selectedBlock?.id || ""}
            activeId={activeBlock?.id || ""}
            onAddAfter={handleAddBlockAfter}
            onSelect={setSelectedId}
          />
        </div>

        <VideoPreview
          videoUrl={videoUrl}
          activeBlock={overlayBlock}
          currentTime={currentTime}
          onPlaybackChange={setIsPreviewPlaying}
          onTimeUpdate={setCurrentTime}
        />

        <div className="right-column">
          <ManualScriptPanel
            textEs={manualTextEs}
            textEn={manualTextEn}
            disabled={isBusy}
            onTextEsChange={setManualTextEs}
            onTextEnChange={setManualTextEn}
            onApply={handleApplyManualText}
          />
          <SubtitleEditorPanel block={selectedBlock} onChange={handleBlockChange} onSave={handleSave} />
        </div>
      </div>

      <footer className="bottom-bar">
        <input ref={fileInputRef} className="hidden-input" type="file" accept="video/*" onChange={handleUpload} />
        <button type="button" onClick={() => fileInputRef.current?.click()} disabled={isBusy}>
          <FileVideo size={18} />
          Subir video
        </button>
        <button type="button" onClick={handleGenerateSpanish} disabled={isBusy}>
          <Sparkles size={18} />
          Generar espanol
        </button>
        <button type="button" onClick={handleGenerateEnglish} disabled={isBusy}>
          <Sparkles size={18} />
          Generar ingles
        </button>
        <button type="button" onClick={handleExport} disabled={isBusy}>
          <Download size={18} />
          Exportar video
        </button>
        <input
          className="export-name-input"
          value={exportName}
          onChange={(event) => setExportName(event.target.value)}
          placeholder="Nombre del video"
          disabled={isBusy}
        />
        <button type="button" onClick={handleChooseExportFolder} disabled={isBusy}>
          <FolderOpen size={18} />
          Carpeta
        </button>
        {exportFolder ? <span className="export-folder-label" title={exportFolder}>{exportFolder}</span> : null}
        <select
          className="export-select"
          value={exportQuality}
          onChange={(event) => setExportQuality(event.target.value)}
          disabled={isBusy}
        >
          <option value="alta">Alta</option>
          <option value="media">Media</option>
          <option value="baja">Baja</option>
        </select>
        <label className="export-check">
          <input
            type="checkbox"
            checked={shouldExportMp3}
            onChange={(event) => setShouldExportMp3(event.target.checked)}
            disabled={isBusy}
          />
          MP3
        </label>
        <button type="button" onClick={() => { setCoverTime(currentTime); setStatus(`Portada en ${currentTime.toFixed(2)}s`); }} disabled={isBusy || !videoUrl}>
          Portada frame actual
        </button>
        {downloadUrl ? (
          <a className="download-link" href={downloadUrl} download>
            Descargar MP4
          </a>
        ) : null}
        {mp3DownloadUrl ? (
          <a className="download-link" href={mp3DownloadUrl} download>
            Descargar MP3
          </a>
        ) : null}
        <span className={`status-text ${isBusy ? "loading" : ""}`}>{status}</span>
      </footer>
    </main>
  );
}
