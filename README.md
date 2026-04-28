# Subtitulador de videos en Espanol e Ingles 9:16

Aplicacion local de escritorio para crear videos verticales 9:16 con subtitulos en espanol e ingles. Esta pensada para clips cortos tipo TikTok/Reels/Shorts: subes un video, generas o pegas subtitulos, editas bloques, ves el preview y exportas el MP4 final con subtitulos quemados.

No usa APIs externas, servicios cloud ni marcas de agua. Todo corre localmente.

## Funciones principales

- Editor visual de subtitulos para video vertical 9:16.
- Preview con HTML5 video y subtitulos HTML encima del video.
- Generacion automatica de subtitulos en espanol con `faster-whisper`.
- Generacion automatica de ingles desde los bloques espanoles ya creados.
- Modo manual: puedes pegar el texto completo en espanol y tambien el texto completo en ingles.
- Comparacion por parrafos/cadenas: si pegas varios parrafos en espanol y los mismos parrafos en ingles, el sistema intenta alinear cada parrafo espanol con su parrafo ingles correspondiente para que terminen en tiempos similares.
- Bloques editables: texto, tamano, posicion vertical, karaoke en espanol y ajustes por bloque.
- Exportacion con FFmpeg local a MP4 con subtitulos quemados.
- Exportacion opcional de MP3.
- Seleccion de portada usando el frame actual del video.
- Historial local de proyectos con SQLite.
- App de escritorio con Electron y backend Python empaquetado.

## Flujo de uso

1. Sube un video vertical.
2. Opcion automatica:
   - Presiona `Generar espanol`.
   - El backend transcribe el audio con `faster-whisper`.
   - Luego puedes presionar `Generar ingles`.
   - El ingles se genera desde los bloques actuales en `text_es`.
3. Opcion manual:
   - Pega el texto completo en espanol.
   - Opcionalmente pega tambien el texto completo en ingles.
   - El sistema separa los textos por parrafos/cadenas.
   - Compara la cadena 1 en espanol con la cadena 1 en ingles, la cadena 2 con la cadena 2, y asi sucesivamente.
   - Usa los tiempos detectados de voz para distribuir esos bloques y mantenerlos sincronizados.
4. Revisa y edita los bloques.
5. Elige una carpeta de exportacion.
6. Exporta el video.

## Arquitectura

```text
backend/
  main.py
  desktop_server.py
  services/
    transcriber.py
    translator.py
    subtitle_builder.py
    renderer.py
    history.py

frontend/
  src/
    App.jsx
    api.js
    components/

desktop/
  main.cjs
  preload.cjs
  Icono/

scripts/
  build_backend.ps1
```

## Backend

Stack:

- Python
- FastAPI
- faster-whisper
- Argos Translate / fallback local
- imageio-ffmpeg
- SQLite para historial

Endpoints principales:

- `POST /api/upload`
- `GET /api/project/{project_id}`
- `PUT /api/project/{project_id}/blocks`
- `POST /api/transcribe/{project_id}`
- `POST /api/translate/{project_id}`
- `POST /api/manual-subtitles/{project_id}`
- `POST /api/export/{project_id}`
- `GET /api/download/{project_id}`
- `GET /api/download/{project_id}/mp3`

## Frontend

Stack:

- React
- Vite
- CSS simple
- HTML5 video
- Overlay HTML absoluto para subtitulos

La interfaz tiene:

- Panel izquierdo con historial y bloques.
- Preview central 9:16.
- Panel derecho de edicion.
- Barra inferior de acciones.

## Requisitos para desarrollo

Instala:

- Python 3.11 o superior
- Node.js 20 o superior
- Git

FFmpeg no necesita estar instalado en el PATH si usas `imageio-ffmpeg`, porque el backend lo resuelve localmente.

## Instalar dependencias

Desde la raiz del proyecto:

```powershell
python -m pip install -r backend\requirements.txt
npm install
npm run frontend:install
```

## Ejecutar en modo desarrollo

Terminal 1, backend:

```powershell
cd C:\ruta\al\proyecto
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2, frontend:

```powershell
cd C:\ruta\al\proyecto\frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Abre:

```text
http://127.0.0.1:5173
```

## Ejecutar como app de escritorio en desarrollo

Primero levanta Vite:

```powershell
cd C:\ruta\al\proyecto\frontend
npm run dev
```

Luego:

```powershell
cd C:\ruta\al\proyecto
npm run desktop:dev
```

## Crear app Windows

Construir frontend:

```powershell
npm run frontend:build
```

Empaquetar backend Python:

```powershell
npm run backend:build
```

Crear app portable:

```powershell
npm run pack:win:ready
```

Crear instalador:

```powershell
npm run dist:win:ready
```

Salidas:

```text
release\win-unpacked\Mini Editor Subtitulos.exe
release\Mini Editor Subtitulos Setup 0.1.0.exe
```

## Datos locales

La app empaquetada guarda proyectos, videos subidos, historial y outputs internos en:

```text
%APPDATA%\Mini Editor Subtitulos\data
```

Los videos finales se guardan en la carpeta que el usuario elige antes de exportar.

## Traduccion

El flujo recomendado es:

1. Generar o corregir primero el espanol.
2. Luego generar ingles desde esos bloques espanoles.

La traduccion automatica trabaja sobre:

```text
project.blocks[i].text_es
```

y guarda en:

```text
project.blocks[i].text_en
```

No vuelve a transcribir, no cambia tiempos, no modifica posiciones y no borra los bloques.

Si el traductor local falla en un bloque, el sistema intenta un fallback local y marca `translation_warning`.

## Exportacion

El backend genera un archivo `.ass` y luego usa FFmpeg para crear el MP4 final:

```text
video original + subtitles.ass -> output.mp4
```

La exportacion respeta:

- `text_es`
- `text_en`
- `font_size_es`
- `font_size_en`
- `y_es`
- `y_en`
- `x`
- karaoke en espanol

## Importante para GitHub

No se deben subir:

- `node_modules/`
- `frontend/dist/`
- `build/`
- `dist/`
- `dist-backend/`
- `release/`
- videos subidos
- videos exportados
- base de datos local del historial
- modelos locales de Argos/Whisper

Eso ya esta cubierto en `.gitignore`.

## Estado del proyecto

Proyecto local funcional en Windows. El codigo base puede adaptarse a macOS/Linux, pero el instalador actual se genera para Windows con Electron Builder.
