import os
from pathlib import Path

import uvicorn


def main() -> None:
    os.environ.setdefault(
        "SUBTITLE_APP_DATA_DIR",
        str(Path.home() / "AppData" / "Local" / "MiniEditorSubtitulos"),
    )
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )


if __name__ == "__main__":
    main()
