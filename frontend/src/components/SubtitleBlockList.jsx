import React from "react";

function formatTime(value) {
  const totalSeconds = Math.max(0, Number(value) || 0);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = (totalSeconds % 60).toFixed(1).padStart(4, "0");
  return `${minutes}:${seconds}`;
}

export default function SubtitleBlockList({ blocks, selectedId, activeId, onAddAfter, onSelect }) {
  return (
    <aside className="side-panel left-panel">
      <div className="panel-header">
        <h2>Bloques</h2>
        <span>{blocks.length}</span>
      </div>

      <div className="block-list">
        {blocks.length ? (
          blocks.map((block) => (
            <div
              key={block.id}
              className={`block-card ${selectedId === block.id ? "selected" : ""} ${
                activeId === block.id ? "active" : ""
              }`}
            >
              <button className="block-content" onClick={() => onSelect(block.id)} type="button">
                <span className="block-time">
                  {formatTime(block.start)} - {formatTime(block.end)}
                </span>
                <strong>{block.text_es || "SIN TEXTO ES"}</strong>
                <small>{block.text_en || "Sin traduccion"}</small>
                {block.translation_warning ? <em>Revisar traduccion</em> : null}
                {block.translation_outdated ? <em>Ingles desactualizado</em> : null}
              </button>
              {selectedId === block.id || activeId === block.id ? (
                <button className="block-add-button" type="button" onClick={() => onAddAfter(block.id)}>
                  + bloque
                </button>
              ) : null}
            </div>
          ))
        ) : (
          <div className="empty-panel">Genera subtitulos para ver los bloques.</div>
        )}
      </div>
    </aside>
  );
}
