import React from "react";
import { Trash2 } from "lucide-react";

function formatDate(value) {
  if (!value) return "";
  const date = new Date(`${value.replace(" ", "T")}Z`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString();
}

export default function ProjectHistory({ activeProjectId, projects, onDelete, onOpen }) {
  return (
    <section className="history-panel">
      <div className="history-header">
        <h3>Historial</h3>
        <span>{projects.length}</span>
      </div>
      <div className="history-list">
        {projects.length ? (
          projects.map((project) => (
            <div
              className={`history-item ${activeProjectId === project.project_id ? "current" : ""}`}
              key={project.project_id}
            >
              <button className="history-open-button" onClick={() => onOpen(project.project_id)} type="button">
                <strong>{project.title || "Proyecto"}</strong>
                <small>
                  {project.block_count || 0} bloques · {formatDate(project.updated_at)}
                </small>
              </button>
              <button className="history-delete-button" onClick={() => onDelete(project)} title="Eliminar historial" type="button">
                <Trash2 size={14} />
              </button>
            </div>
          ))
        ) : (
          <div className="history-empty">Sin proyectos guardados</div>
        )}
      </div>
    </section>
  );
}
