import React from "react";
import { ArrowDown, ArrowUp, Minus, Plus, Save } from "lucide-react";

const MIN_FONT_SIZE = 20;
const MAX_FONT_SIZE = 120;
const MIN_Y = 0;
const MAX_Y = 1920;
const FONT_STEP = 4;
const POSITION_STEP = 10;

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

export default function SubtitleEditorPanel({ block, onChange, onSave }) {
  const updateField = (field, value) => {
    onChange({ ...block, [field]: value, x: block.x ?? 540 });
  };

  const adjustFontSize = (field, amount) => {
    onChange({
      ...block,
      [field]: clamp(Number(block[field]) + amount, MIN_FONT_SIZE, MAX_FONT_SIZE),
      x: block.x ?? 540,
    });
  };

  const adjustPosition = (field, amount) => {
    onChange({
      ...block,
      [field]: clamp(Number(block[field]) + amount, MIN_Y, MAX_Y),
      x: block.x ?? 540,
    });
  };

  return (
    <aside className="side-panel editor-panel">
      <div className="panel-header">
        <h2>Editor</h2>
        {block ? <span>{block.id}</span> : null}
      </div>

      {block ? (
        <div className="editor-form">
          <label>
            Texto espanol
            <textarea value={block.text_es} onChange={(event) => updateField("text_es", event.target.value)} />
          </label>

          <label>
            Texto ingles
            <textarea value={block.text_en} onChange={(event) => updateField("text_en", event.target.value)} />
          </label>

          <div className="control-section">
            <span>Tamano</span>
            <div className="control-grid">
              <button type="button" onClick={() => adjustFontSize("font_size_es", -FONT_STEP)} title="ES -">
                <Minus size={16} /> ES
              </button>
              <button type="button" onClick={() => adjustFontSize("font_size_es", FONT_STEP)} title="ES +">
                <Plus size={16} /> ES
              </button>
              <button type="button" onClick={() => adjustFontSize("font_size_en", -FONT_STEP)} title="EN -">
                <Minus size={16} /> EN
              </button>
              <button type="button" onClick={() => adjustFontSize("font_size_en", FONT_STEP)} title="EN +">
                <Plus size={16} /> EN
              </button>
            </div>
            <div className="value-row">
              <span>ES {block.font_size_es}px</span>
              <span>EN {block.font_size_en}px</span>
            </div>
          </div>

          <div className="control-section">
            <span>Posicion vertical</span>
            <div className="control-grid">
              <button type="button" onClick={() => adjustPosition("y_es", -POSITION_STEP)} title="Subir ES">
                <ArrowUp size={16} /> ES
              </button>
              <button type="button" onClick={() => adjustPosition("y_es", POSITION_STEP)} title="Bajar ES">
                <ArrowDown size={16} /> ES
              </button>
              <button type="button" onClick={() => adjustPosition("y_en", -POSITION_STEP)} title="Subir EN">
                <ArrowUp size={16} /> EN
              </button>
              <button type="button" onClick={() => adjustPosition("y_en", POSITION_STEP)} title="Bajar EN">
                <ArrowDown size={16} /> EN
              </button>
            </div>
            <div className="value-row">
              <span>ES y {block.y_es}</span>
              <span>EN y {block.y_en}</span>
            </div>
          </div>

          <button className="primary-action" type="button" onClick={onSave}>
            <Save size={18} />
            Guardar cambios
          </button>
        </div>
      ) : (
        <div className="empty-panel">Selecciona un bloque para editar</div>
      )}
    </aside>
  );
}
