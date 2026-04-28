import React from "react";
import { ClipboardCheck } from "lucide-react";

export default function ManualScriptPanel({
  textEs,
  textEn,
  disabled,
  onTextEsChange,
  onTextEnChange,
  onApply,
}) {
  return (
    <section className="manual-script">
      <div className="manual-header">
        <h3>Texto manual</h3>
        <span>cadenas por parrafo</span>
      </div>

      <label>
        Espanol
        <textarea
          value={textEs}
          onChange={(event) => onTextEsChange(event.target.value)}
          placeholder="Pega aqui el texto en espanol..."
        />
      </label>

      <label>
        Ingles
        <textarea
          value={textEn}
          onChange={(event) => onTextEnChange(event.target.value)}
          placeholder="Pega aqui el texto en ingles..."
        />
      </label>

      <button type="button" onClick={onApply} disabled={disabled || !textEs.trim()}>
        <ClipboardCheck size={18} />
        Aplicar texto manual
      </button>
    </section>
  );
}
