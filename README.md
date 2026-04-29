# Subtitulador de videos en Espanol e Ingles 9:16

Editor de escritorio para crear videos verticales 9:16 con subtitulos en espanol e ingles. Esta pensado para contenido corto tipo TikTok, Reels y Shorts: cargas un video, generas o pegas subtitulos, ajustas los bloques visualmente y exportas un MP4 final con subtitulos quemados.

La aplicacion funciona localmente en Windows y no agrega marca de agua.

## Que permite hacer

- Subir videos verticales 9:16.
- Generar subtitulos en espanol automaticamente desde el audio.
- Generar subtitulos en ingles desde el texto espanol ya creado.
- Pegar guiones manuales en espanol e ingles.
- Alinear parrafos de espanol con sus parrafos equivalentes en ingles.
- Editar cada bloque de subtitulo.
- Ajustar texto, tamano y posicion vertical.
- Ver preview en tiempo real.
- Usar karaoke en palabras del subtitulo espanol.
- Exportar video final MP4 con subtitulos quemados.
- Exportar audio MP3 opcional.
- Elegir portada desde el frame actual del video.
- Guardar historial local de proyectos.

## App de escritorio

El proyecto esta preparado como aplicacion de escritorio con Electron y backend Python empaquetado. El usuario final no necesita abrir servidores manualmente: al iniciar la app, Electron levanta el backend local en segundo plano.

Archivos generados al compilar:

```text
release/win-unpacked/Mini Editor Subtitulos.exe
release/Mini Editor Subtitulos Setup 0.1.0.exe
```

Puedes usar:

- `Mini Editor Subtitulos.exe`: version portable para probar la app sin instalar.
- `Mini Editor Subtitulos Setup 0.1.0.exe`: instalador para Windows.

## Flujo automatico

1. Abre la app.
2. Sube un video.
3. Presiona `Generar espanol`.
4. La app transcribe el audio y crea bloques en espanol.
5. Revisa o corrige el espanol si hace falta.
6. Presiona `Generar ingles`.
7. La app genera el ingles desde los bloques actuales en espanol.
8. Ajusta posicion, tamano o texto de cualquier bloque.
9. Elige una carpeta de exportacion.
10. Exporta el video final.

## Flujo manual por parrafos

Tambien puedes trabajar pegando el guion completo.

Ejemplo:

```text
Parrafo 1 en espanol

Parrafo 2 en espanol

Parrafo 3 en espanol
```

y su version en ingles:

```text
Paragraph 1 in English

Paragraph 2 in English

Paragraph 3 in English
```

La app separa ambos textos por parrafos. Luego compara:

```text
parrafo 1 espanol -> parrafo 1 ingles
parrafo 2 espanol -> parrafo 2 ingles
parrafo 3 espanol -> parrafo 3 ingles
```

Con esa relacion, distribuye los subtitulos sobre los tiempos detectados de voz para que cada bloque en espanol y su bloque en ingles terminen aproximadamente al mismo tiempo.

Este modo es util cuando ya tienes el texto correcto y solo quieres que la app lo sincronice con el video.

## Edicion visual

La interfaz se organiza como un editor simple:

```text
Panel izquierdo   Preview central   Panel derecho
Barra inferior de acciones
```

Panel izquierdo:

- Historial de proyectos.
- Lista de bloques.
- Indicador del bloque activo.
- Boton para agregar un bloque vacio si necesitas corregir una parte.

Preview central:

- Video vertical 9:16.
- Subtitulo ingles arriba.
- Subtitulo espanol abajo.
- Karaoke en el espanol.
- Actualizacion en tiempo real.

Panel derecho:

- Edicion de texto espanol.
- Edicion de texto ingles.
- Controles de tamano.
- Controles de posicion vertical.
- Guardado de cambios.

## Exportacion

Antes de exportar debes elegir una carpeta de destino. La app crea una carpeta con el nombre del video y guarda ahi los archivos generados.

Ejemplo:

```text
Carpeta elegida/
  silver chariot/
    silver chariot.mp4
    silver chariot_portada.jpg
    silver chariot.mp3
```

El MP4 final se exporta con subtitulos quemados usando FFmpeg local.

## Tecnologias

Frontend:

- React
- Vite
- CSS
- HTML5 video

Backend:

- Python
- FastAPI
- faster-whisper
- Argos Translate / fallback local
- imageio-ffmpeg
- SQLite

Escritorio:

- Electron
- PyInstaller
- electron-builder

## Ejecutar en desarrollo

Requisitos:

- Python 3.11 o superior
- Node.js 20 o superior
- Git

Instalar dependencias:

```powershell
python -m pip install -r backend\requirements.txt
npm install
npm run frontend:install
```

Levantar backend:

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Levantar frontend:

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Abrir:

```text
http://127.0.0.1:5173
```

## Ejecutar como escritorio en desarrollo

Con Vite abierto en el puerto `5173`, ejecuta desde la raiz:

```powershell
npm run desktop:dev
```

## Crear instalador de Windows

Construir frontend:

```powershell
npm run frontend:build
```

Empaquetar backend Python:

```powershell
npm run backend:build
```

Crear version portable:

```powershell
npm run pack:win:ready
```

Crear instalador:

```powershell
npm run dist:win:ready
```

Los archivos quedan en:

```text
release/
```

## Datos de la app

La version instalada guarda sus datos locales en:

```text
%APPDATA%\Mini Editor Subtitulos\data
```

Los videos finales se guardan en la carpeta que el usuario elige al exportar.
