import React from "react";

function getActiveWordIndex(block, currentTime) {
  const words = block?.words || [];
  if (!words.length) return -1;

  return words.findIndex((word) => currentTime >= Number(word.start) && currentTime < Number(word.end));
}

function HighlightedSpanish({ block, currentTime }) {
  const text = block?.text_es || "";
  const parts = String(text).split(/(\s+)/);
  const highlightIndex = getActiveWordIndex(block, currentTime);
  let visibleIndex = -1;

  return parts.map((part, index) => {
    if (/^\s+$/.test(part)) return part;

    visibleIndex += 1;
    return (
      <span key={`${part}-${index}`} className={visibleIndex === highlightIndex ? "subtitle-highlight" : undefined}>
        {part}
      </span>
    );
  });
}

export default function SubtitleOverlay({ block, currentTime = 0 }) {
  if (!block) return null;

  const positionStyle = (fontSize, y) => ({
    left: `${((block.x ?? 540) / 1080) * 100}%`,
    top: `${(y / 1920) * 100}%`,
    fontSize: `clamp(12px, ${(fontSize / 1080) * 100}cqw, ${fontSize}px)`,
  });

  return (
    <div className="subtitle-layer" aria-hidden="true">
      <div className="subtitle-line subtitle-en" style={positionStyle(block.font_size_en, block.y_en)}>
        {block.text_en}
      </div>
      <div className="subtitle-line subtitle-es" style={positionStyle(block.font_size_es, block.y_es)}>
        <HighlightedSpanish block={block} currentTime={currentTime} />
      </div>
    </div>
  );
}
