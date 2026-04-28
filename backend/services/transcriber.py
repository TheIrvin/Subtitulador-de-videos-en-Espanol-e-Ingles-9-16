from functools import lru_cache
from pathlib import Path


WHISPER_MODEL_SIZE = "base"
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"


@lru_cache(maxsize=1)
def get_model():
    from faster_whisper import WhisperModel

    return WhisperModel(
        WHISPER_MODEL_SIZE,
        device=WHISPER_DEVICE,
        compute_type=WHISPER_COMPUTE_TYPE,
    )


def transcribe_video(video_path: str | Path) -> dict:
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video no encontrado: {path}")

    model = get_model()
    segments, info = model.transcribe(
        str(path),
        language="es",
        vad_filter=True,
    )

    raw_segments = [
        {
            "start": float(segment.start),
            "end": float(segment.end),
            "text": segment.text.strip(),
        }
        for segment in segments
        if segment.text.strip()
    ]

    return {
        "language": getattr(info, "language", "es"),
        "duration": float(getattr(info, "duration", 0.0) or 0.0),
        "segments": raw_segments,
    }
