from pathlib import Path
from uuid import uuid4
import json
import os
import re

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.services.history import delete_project_history, init_history_db, list_project_history, upsert_project_history
from backend.services.renderer import FFmpegNotInstalledError, RenderError, export_video
from backend.services.subtitle_builder import build_blocks_from_manual_text, build_blocks_from_segments, refresh_block_words
from backend.services.transcriber import transcribe_video
from backend.services.translator import MissingTranslationPackageError, translate_blocks


SOURCE_BACKEND_DIR = Path(__file__).resolve().parent
SOURCE_ROOT_DIR = SOURCE_BACKEND_DIR.parent
APP_DATA_DIR = os.environ.get("SUBTITLE_APP_DATA_DIR")
ROOT_DIR = Path(APP_DATA_DIR) if APP_DATA_DIR else SOURCE_ROOT_DIR
BASE_DIR = ROOT_DIR / "backend" if APP_DATA_DIR else SOURCE_BACKEND_DIR
UPLOADS_DIR = BASE_DIR / "uploads"
PROJECTS_DIR = BASE_DIR / "projects"
OUTPUTS_DIR = BASE_DIR / "outputs"
HISTORY_DIR = ROOT_DIR / "historial"

for folder in (UPLOADS_DIR, PROJECTS_DIR, OUTPUTS_DIR, HISTORY_DIR):
    folder.mkdir(parents=True, exist_ok=True)

HISTORY_DB_PATH = init_history_db(HISTORY_DIR)

app = FastAPI(title="Mini Editor de Subtitulos")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "null", "file://"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


@app.get("/api/health")
def health_check():
    return {"ok": True}


class BlocksPayload(BaseModel):
    blocks: list[dict]


class ManualSubtitlesPayload(BaseModel):
    text_es: str
    text_en: str = ""


class ExportPayload(BaseModel):
    name: str = ""
    quality: str = "media"
    export_mp3: bool = False
    cover_time: float | None = None
    output_dir: str = ""


def project_path(project_id: str) -> Path:
    return PROJECTS_DIR / f"{project_id}.json"


def read_project(project_id: str) -> dict:
    path = project_path(project_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return json.loads(path.read_text(encoding="utf-8"))


def write_project(project_id: str, data: dict) -> None:
    path = project_path(project_id)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    upsert_project_history(HISTORY_DB_PATH, data, path)


def safe_filename(filename: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9._-]+", "_", Path(filename).name).strip("_")
    return clean or "video.mp4"


def sync_existing_projects_to_history() -> None:
    for path in PROJECTS_DIR.glob("*.json"):
        try:
            project = json.loads(path.read_text(encoding="utf-8"))
            upsert_project_history(HISTORY_DB_PATH, project, path)
        except Exception as exc:
            print(f"No se pudo indexar historial {path}: {exc}")


sync_existing_projects_to_history()


@app.post("/api/upload")
async def upload_video(video: UploadFile = File(...)):
    project_id = uuid4().hex
    stored_name = f"{project_id}_{safe_filename(video.filename or 'video.mp4')}"
    destination = UPLOADS_DIR / stored_name

    with destination.open("wb") as output:
        while chunk := await video.read(1024 * 1024):
            output.write(chunk)

    project = {
        "project_id": project_id,
        "video_filename": stored_name,
        "video_url": f"/uploads/{stored_name}",
        "blocks": [],
        "transcription": None,
        "status": "Video subido. Listo para transcribir.",
    }
    write_project(project_id, project)

    return {"project_id": project_id}


@app.get("/api/project/{project_id}")
def get_project(project_id: str):
    return read_project(project_id)


@app.get("/api/history")
def get_history():
    return {"projects": list_project_history(HISTORY_DB_PATH)}


@app.delete("/api/history/{project_id}")
def delete_history_project(project_id: str):
    deleted = delete_project_history(HISTORY_DB_PATH, project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado en historial")
    return {"project_id": project_id, "deleted": True}


@app.post("/api/transcribe/{project_id}")
def transcribe_project(project_id: str):
    project = read_project(project_id)
    video_filename = project.get("video_filename")

    if not video_filename:
        raise HTTPException(status_code=400, detail="El proyecto no tiene video asociado")

    video_path = UPLOADS_DIR / video_filename
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video no encontrado")

    try:
        transcription = transcribe_video(video_path)
        blocks = build_blocks_from_segments(transcription["segments"])
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error de transcripcion: {exc}") from exc

    project["transcription"] = transcription
    project["blocks"] = blocks
    project["status"] = "Subtitulos en espanol generados."
    write_project(project_id, project)

    return {"project_id": project_id, "blocks": blocks}


@app.post("/api/translate/{project_id}")
def translate_project(project_id: str):
    project = read_project(project_id)
    blocks = project.get("blocks") or []

    if not blocks:
        raise HTTPException(status_code=400, detail="El proyecto no tiene bloques en espanol para traducir")

    try:
        translated_blocks = translate_blocks(blocks)
    except MissingTranslationPackageError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error de traduccion: {exc}") from exc

    project["blocks"] = translated_blocks
    project["status"] = "Subtitulos en ingles generados."
    write_project(project_id, project)

    return {"project_id": project_id, "blocks": translated_blocks}


@app.post("/api/manual-subtitles/{project_id}")
def manual_subtitles_project(project_id: str, payload: ManualSubtitlesPayload):
    project = read_project(project_id)
    video_filename = project.get("video_filename")
    transcription = project.get("transcription")

    if not payload.text_es.strip():
        raise HTTPException(status_code=400, detail="Pega primero el texto en espanol")

    if not transcription or not transcription.get("segments"):
        if not video_filename:
            raise HTTPException(status_code=400, detail="El proyecto no tiene video asociado")

        video_path = UPLOADS_DIR / video_filename
        if not video_path.exists():
            raise HTTPException(status_code=404, detail="Video no encontrado")

        try:
            # Solo se usa para detectar los momentos donde hay voz; el texto final lo pone el usuario.
            transcription = transcribe_video(video_path)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Error detectando tiempos de voz: {exc}") from exc

    blocks = build_blocks_from_manual_text(
        payload.text_es,
        payload.text_en,
        segments=transcription.get("segments", []),
        existing_blocks=project.get("blocks", []),
    )

    if not blocks:
        raise HTTPException(status_code=400, detail="No se pudieron crear bloques con el texto enviado")

    project["transcription"] = transcription
    project["blocks"] = blocks
    project["status"] = "Texto manual aplicado sobre los tiempos de voz."
    write_project(project_id, project)

    return {"project_id": project_id, "blocks": blocks}


@app.post("/api/generate-subtitles/{project_id}")
def generate_subtitles(project_id: str):
    return translate_project(project_id)


@app.post("/api/export/{project_id}")
def export_project(project_id: str, payload: ExportPayload | None = None):
    project = read_project(project_id)
    payload = payload or ExportPayload()

    if not payload.output_dir.strip():
        raise HTTPException(status_code=400, detail="Elige una carpeta de exportacion antes de exportar")

    try:
        export_info = export_video(
            project,
            UPLOADS_DIR,
            OUTPUTS_DIR,
            export_name=payload.name,
            quality=payload.quality,
            export_mp3=payload.export_mp3,
            cover_time=payload.cover_time,
            output_dir=payload.output_dir,
        )
    except FFmpegNotInstalledError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RenderError as exc:
        raise HTTPException(status_code=500, detail=f"Error al renderizar con FFmpeg: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al exportar video: {exc}") from exc

    project["ass_path"] = export_info["ass_path"]
    project["output_path"] = export_info["output_path"]
    project["output_filename"] = export_info["output_filename"]
    project["export_folder"] = export_info["export_folder"]
    project["export_root"] = payload.output_dir
    project["export_name"] = export_info["export_name"]
    project["export_quality"] = export_info["quality"]
    project["cover_path"] = export_info.get("cover_path")
    project["mp3_path"] = export_info.get("mp3_path")
    project["status"] = "Video exportado correctamente."
    write_project(project_id, project)

    return {
        "project_id": project_id,
        "ass_path": export_info["ass_path"],
        "ass_filename": export_info["ass_filename"],
        "output_path": export_info["output_path"],
        "output_filename": export_info["output_filename"],
        "export_folder": export_info["export_folder"],
        "cover_path": export_info.get("cover_path"),
        "cover_filename": export_info.get("cover_filename"),
        "mp3_path": export_info.get("mp3_path"),
        "mp3_filename": export_info.get("mp3_filename"),
        "dialogue_count": export_info["dialogue_count"],
        "download_url": f"/api/download/{project_id}",
        "mp3_download_url": f"/api/download/{project_id}/mp3" if export_info.get("mp3_path") else None,
    }


@app.get("/api/download/{project_id}")
def download_project(project_id: str):
    project = read_project(project_id)
    output_path = project.get("output_path")

    if not output_path:
        raise HTTPException(status_code=404, detail="El proyecto no tiene video exportado")

    path = Path(output_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Video exportado no encontrado")

    return FileResponse(
        path,
        media_type="video/mp4",
        filename=project.get("output_filename") or f"{project_id}_output.mp4",
    )


@app.get("/api/download/{project_id}/mp3")
def download_project_mp3(project_id: str):
    project = read_project(project_id)
    mp3_path = project.get("mp3_path")

    if not mp3_path:
        raise HTTPException(status_code=404, detail="El proyecto no tiene MP3 exportado")

    path = Path(mp3_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="MP3 exportado no encontrado")

    return FileResponse(
        path,
        media_type="audio/mpeg",
        filename=path.name,
    )


@app.put("/api/project/{project_id}/blocks")
def update_blocks(project_id: str, payload: BlocksPayload):
    project = read_project(project_id)
    previous_blocks = {block.get("id"): block for block in project.get("blocks", [])}
    updated_blocks = []

    for block in payload.blocks:
        updated_block = dict(block)
        previous_block = previous_blocks.get(updated_block.get("id"), {})
        previous_text_es = str(previous_block.get("text_es", ""))
        current_text_es = str(updated_block.get("text_es", ""))

        if current_text_es != previous_text_es:
            updated_block = refresh_block_words(updated_block)
            updated_block["translation_outdated"] = True
            updated_block.pop("translation_warning", None)
        else:
            updated_block["x"] = updated_block.get("x", 540)

        updated_blocks.append(updated_block)

    project["blocks"] = updated_blocks
    project["status"] = "Cambios guardados."
    write_project(project_id, project)
    return project
