$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

python -m pip install -r backend\requirements.txt
python -m pip install pyinstaller

if (Test-Path dist-backend) {
  Remove-Item dist-backend -Recurse -Force
}

python -m PyInstaller `
  --noconfirm `
  --clean `
  --name mini-subtitles-backend `
  --onedir `
  --console `
  --collect-all faster_whisper `
  --collect-all imageio_ffmpeg `
  --collect-all argostranslate `
  --collect-all uvicorn `
  --hidden-import backend.main `
  --hidden-import backend.services.history `
  --hidden-import backend.services.renderer `
  --hidden-import backend.services.subtitle_builder `
  --hidden-import backend.services.transcriber `
  --hidden-import backend.services.translator `
  backend\desktop_server.py

New-Item -ItemType Directory -Force -Path dist-backend | Out-Null
Copy-Item -Path dist\mini-subtitles-backend\* -Destination dist-backend -Recurse -Force

Write-Host "Backend empaquetado en dist-backend"
