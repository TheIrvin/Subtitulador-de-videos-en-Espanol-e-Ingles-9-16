from pathlib import Path
import re
import shutil
import subprocess


class FFmpegNotInstalledError(RuntimeError):
    pass


class RenderError(RuntimeError):
    pass


QUALITY_PRESETS = {
    "alta": {"crf": "18", "preset": "slow"},
    "media": {"crf": "23", "preset": "medium"},
    "baja": {"crf": "28", "preset": "fast"},
}

DEFAULT_FINAL_EXPORTS_DIR = Path.home() / "Downloads" / "Videos_Subtitulados"

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: InglesGlow,Montserrat,70,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,6,0,5,0,0,0,1
Style: EspanolPop,Montserrat,64,&H00F3F4F6,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,7,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def seconds_to_ass_time(seconds: float) -> str:
    total_centiseconds = max(0, int(round(float(seconds) * 100)))
    centiseconds = total_centiseconds % 100
    total_seconds = total_centiseconds // 100
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"


def safe_export_name(name: str) -> str:
    clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', " ", str(name or "")).strip()
    clean = re.sub(r"\s+", " ", clean)
    return clean or "video_subtitulado"


def resolve_export_root(output_dir: str | Path | None = None) -> Path:
    if not output_dir:
        return DEFAULT_FINAL_EXPORTS_DIR

    raw_path = str(output_dir).strip().strip('"')
    if not raw_path:
        return DEFAULT_FINAL_EXPORTS_DIR

    return Path(raw_path).expanduser()


def get_ffmpeg_path() -> str:
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path

    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        raise FFmpegNotInstalledError(
            "FFmpeg no esta instalado o no esta disponible. "
            "Instala imageio-ffmpeg con: python -m pip install imageio-ffmpeg"
        ) from exc


def escape_ass_text(text: str) -> str:
    return (
        str(text or "")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace("\r", " ")
        .replace("\n", " ")
        .strip()
        .upper()
    )


def ass_position_override(block: dict, font_size_key: str, y_key: str, default_font_size: int, default_y: int) -> str:
    x = int(round(float(block.get("x", 540))))
    y = int(round(float(block.get(y_key, default_y))))
    font_size = int(round(float(block.get(font_size_key, default_font_size))))
    return r"{\q2\fnMontserrat\fs" + str(font_size) + r"\fsp-3\bord7\shad0\pos(" + str(x) + "," + str(y) + ")}"


def build_english_glow_line(block: dict) -> str:
    start = seconds_to_ass_time(block.get("start", 0))
    end = seconds_to_ass_time(block.get("end", 0))
    x = int(round(float(block.get("x", 540))))
    y = int(round(float(block.get("y_en", 1440))))
    font_size = int(round(float(block.get("font_size_en", 70))))
    text = escape_ass_text(block.get("text_en", ""))
    override = (
        r"{\q2\fnMontserrat\fs"
        + str(font_size)
        + r"\fsp-3\bord12\blur8\shad0\1c&H49B2F5&\3c&H49B2F5&\pos("
        + str(x)
        + ","
        + str(y)
        + ")}"
    )
    return f"Dialogue: 0,{start},{end},InglesGlow,,0,0,0,,{override}{text}"


def build_english_text_line(block: dict) -> str:
    start = seconds_to_ass_time(block.get("start", 0))
    end = seconds_to_ass_time(block.get("end", 0))
    override = ass_position_override(block, "font_size_en", "y_en", 70, 1440)
    text = escape_ass_text(block.get("text_en", ""))
    return f"Dialogue: 1,{start},{end},InglesGlow,,0,0,0,,{override}{text}"


def spanish_text_with_active_word(text: str, active_index: int) -> str:
    words = str(text or "").split()
    parts = []

    for index, word in enumerate(words):
        escaped_word = escape_ass_text(word)
        if index == active_index:
            parts.append(r"{\c&H33E839&}" + escaped_word + r"{\c&HFFFFFF&}")
        else:
            parts.append(escaped_word)

    return " ".join(parts)


def build_spanish_line(block: dict, start: float, end: float, active_index: int = -1) -> str:
    override = ass_position_override(block, "font_size_es", "y_es", 64, 1540)
    text = spanish_text_with_active_word(block.get("text_es", ""), active_index)
    return f"Dialogue: 2,{seconds_to_ass_time(start)},{seconds_to_ass_time(end)},EspanolPop,,0,0,0,,{override}{text}"


def build_spanish_karaoke_lines(block: dict) -> list[str]:
    words = block.get("words") or []
    text_words = str(block.get("text_es", "")).split()

    if not words or len(words) != len(text_words):
        return [build_spanish_line(block, block.get("start", 0), block.get("end", 0))]

    lines = []
    for index, word in enumerate(words):
        lines.append(build_spanish_line(block, word.get("start", block.get("start", 0)), word.get("end", block.get("end", 0)), index))
    return lines


def build_ass_content(blocks: list[dict]) -> str:
    lines = [ASS_HEADER.rstrip()]

    for block in blocks:
        if block.get("text_en"):
            lines.append(build_english_glow_line(block))
            lines.append(build_english_text_line(block))
        lines.extend(build_spanish_karaoke_lines(block))

    return "\n".join(lines) + "\n"


def generate_ass_file(project: dict, outputs_dir: str | Path) -> dict:
    blocks = project.get("blocks") or []
    if not blocks:
        raise ValueError("El proyecto no tiene bloques para exportar")

    project_id = project.get("project_id")
    if not project_id:
        raise ValueError("El proyecto no tiene project_id")

    project_output_dir = Path(outputs_dir) / project_id
    project_output_dir.mkdir(parents=True, exist_ok=True)
    ass_path = project_output_dir / "subtitles.ass"
    ass_content = build_ass_content(blocks)
    ass_path.write_text(ass_content, encoding="utf-8")

    return {
        "ass_path": str(ass_path),
        "ass_filename": ass_path.name,
        "dialogue_count": sum(1 for line in ass_content.splitlines() if line.startswith("Dialogue:")),
    }


def run_ffmpeg(command: list[str], cwd: str | Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def render_video_with_ass(input_path: str | Path, ass_path: str | Path, output_path: str | Path, quality: str = "media") -> dict:
    ffmpeg_path = get_ffmpeg_path()

    input_path = Path(input_path)
    ass_path = Path(ass_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Archivo de video no existe: {input_path}")
    if not ass_path.exists():
        raise FileNotFoundError(f"Archivo ASS no existe: {ass_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    quality_settings = QUALITY_PRESETS.get(quality, QUALITY_PRESETS["media"])

    command = [
        ffmpeg_path,
        "-y",
        "-i",
        str(input_path),
        "-vf",
        "ass=subtitles.ass",
        "-c:v",
        "libx264",
        "-crf",
        quality_settings["crf"],
        "-preset",
        quality_settings["preset"],
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(output_path),
    ]

    result = run_ffmpeg(command, cwd=ass_path.parent)

    if result.returncode != 0:
        raise RenderError(result.stderr.strip() or "FFmpeg fallo sin devolver stderr")

    return {
        "output_path": str(output_path),
        "output_filename": output_path.name,
        "stderr": result.stderr,
    }


def export_cover_image(input_path: str | Path, output_path: str | Path, cover_time: float) -> dict:
    ffmpeg_path = get_ffmpeg_path()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        ffmpeg_path,
        "-y",
        "-ss",
        str(max(float(cover_time or 0), 0)),
        "-i",
        str(input_path),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(output_path),
    ]
    result = run_ffmpeg(command)
    if result.returncode != 0:
        raise RenderError(result.stderr.strip() or "FFmpeg fallo generando portada")

    return {"cover_path": str(output_path), "cover_filename": output_path.name}


def export_mp3_audio(input_path: str | Path, output_path: str | Path) -> dict:
    ffmpeg_path = get_ffmpeg_path()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        ffmpeg_path,
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "2",
        str(output_path),
    ]
    result = run_ffmpeg(command)
    if result.returncode != 0:
        raise RenderError(result.stderr.strip() or "FFmpeg fallo generando MP3")

    return {"mp3_path": str(output_path), "mp3_filename": output_path.name}


def export_video(
    project: dict,
    uploads_dir: str | Path,
    outputs_dir: str | Path,
    export_name: str = "",
    quality: str = "media",
    export_mp3: bool = False,
    cover_time: float | None = None,
    output_dir: str | Path | None = None,
) -> dict:
    video_filename = project.get("video_filename")
    if not video_filename:
        raise ValueError("El proyecto no tiene video asociado")

    input_path = Path(uploads_dir) / video_filename
    ass_info = generate_ass_file(project, outputs_dir)
    ass_path = Path(ass_info["ass_path"])
    final_name = safe_export_name(export_name or project.get("export_name") or project["project_id"])
    final_dir = resolve_export_root(output_dir or project.get("export_root")) / final_name
    output_path = final_dir / f"{final_name}.mp4"
    render_info = render_video_with_ass(input_path, ass_path, output_path, quality)
    cover_info = export_cover_image(output_path, final_dir / f"{final_name}_portada.jpg", cover_time or 0)
    mp3_info = export_mp3_audio(input_path, final_dir / f"{final_name}.mp3") if export_mp3 else {}

    return {
        **ass_info,
        **render_info,
        **cover_info,
        **mp3_info,
        "export_name": final_name,
        "export_folder": str(final_dir),
        "quality": quality,
    }
