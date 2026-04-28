from pathlib import Path
import sqlite3


def connect(db_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_history_db(history_dir: str | Path) -> Path:
    history_dir = Path(history_dir)
    history_dir.mkdir(parents=True, exist_ok=True)
    db_path = history_dir / "proyectos.db"

    with connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                video_filename TEXT,
                video_url TEXT,
                project_json_path TEXT NOT NULL,
                cover_path TEXT,
                output_path TEXT,
                export_folder TEXT,
                status TEXT,
                block_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS hidden_projects (
                project_id TEXT PRIMARY KEY,
                hidden_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_projects_updated_at ON projects(updated_at DESC)")

    return db_path


def project_title(project: dict) -> str:
    if project.get("export_name"):
        return str(project["export_name"])
    if project.get("title"):
        return str(project["title"])
    video_filename = str(project.get("video_filename") or "")
    if video_filename:
        parts = video_filename.split("_", 1)
        return Path(parts[1] if len(parts) > 1 else video_filename).stem.replace("_", " ")
    return str(project.get("project_id") or "Proyecto")


def upsert_project_history(db_path: str | Path, project: dict, project_json_path: str | Path) -> None:
    project_id = project.get("project_id")
    if not project_id:
        return

    with connect(db_path) as connection:
        hidden = connection.execute(
            "SELECT 1 FROM hidden_projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        if hidden:
            return

        connection.execute(
            """
            INSERT INTO projects (
                project_id, title, video_filename, video_url, project_json_path,
                cover_path, output_path, export_folder, status, block_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id) DO UPDATE SET
                title = excluded.title,
                video_filename = excluded.video_filename,
                video_url = excluded.video_url,
                project_json_path = excluded.project_json_path,
                cover_path = excluded.cover_path,
                output_path = excluded.output_path,
                export_folder = excluded.export_folder,
                status = excluded.status,
                block_count = excluded.block_count,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                project_id,
                project_title(project),
                project.get("video_filename"),
                project.get("video_url"),
                str(project_json_path),
                project.get("cover_path"),
                project.get("output_path"),
                project.get("export_folder"),
                project.get("status"),
                len(project.get("blocks") or []),
            ),
        )


def list_project_history(db_path: str | Path, limit: int = 50) -> list[dict]:
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT project_id, title, video_filename, video_url, project_json_path,
                   cover_path, output_path, export_folder, status, block_count,
                   created_at, updated_at
            FROM projects
            ORDER BY datetime(updated_at) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def delete_project_history(db_path: str | Path, project_id: str) -> bool:
    with connect(db_path) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO hidden_projects (project_id, hidden_at) VALUES (?, CURRENT_TIMESTAMP)",
            (project_id,),
        )
        cursor = connection.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
        return cursor.rowcount > 0
