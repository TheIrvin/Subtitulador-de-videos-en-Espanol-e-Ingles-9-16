# Subtitulador de videos en Espanol e Ingles 9:16

Aplicacion de escritorio para crear videos verticales 9:16 con subtitulos en espanol e ingles. Esta pensada para contenido corto tipo TikTok, Reels y Shorts: cargas un video, generas o pegas subtitulos, ajustas los bloques visualmente y exportas un MP4 final con subtitulos quemados.

Funciona localmente en Windows y no agrega marca de agua.

## Crear e instalar el paquete de Windows

El repositorio todavía no publica instaladores en **Releases**. Puedes generarlos localmente desde el código fuente:

1. Instala Node.js y Python para Windows.
2. Crea y activa un entorno Python; después instala las dependencias:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

3. Instala las dependencias de Electron y del frontend, y compila:

```powershell
npm install
npm run frontend:install
npm run dist:win
```

El instalador NSIS y la versión portable se generan en `release/`. El paquete incluye el backend y sus dependencias; no requiere instalar FFmpeg por separado. La transcripción automática puede descargar el modelo de voz la primera vez que se usa.

## Uso rapido

1. Abre la aplicacion.
2. Sube un video vertical.
3. Genera subtitulos automaticamente o pega tu guion manual.
4. Revisa y edita los bloques.
5. Elige una carpeta para guardar el resultado.
6. Exporta el video final.

## Funciones principales

- Subtitulos en espanol e ingles para videos 9:16.
- Transcripcion automatica del espanol desde el audio.
- Generacion de ingles desde los bloques en espanol.
- Modo manual para pegar texto en espanol e ingles.
- Alineacion por parrafos entre espanol e ingles.
- Editor visual por bloques.
- Preview en tiempo real.
- Karaoke por palabra en el subtitulo espanol.
- Ajuste de texto, tamano y posicion vertical.
- Exportacion MP4 con subtitulos quemados.
- Exportacion opcional de MP3.
- Seleccion de portada desde el frame actual.
- Historial local de proyectos.

## Flujo automatico

El flujo automatico sirve cuando quieres que la app detecte el audio y cree los subtitulos iniciales.

1. Sube el video.
2. Presiona **Generar espanol**.
3. La app transcribe el audio y crea bloques en espanol.
4. Corrige el texto espanol si hace falta.
5. Presiona **Generar ingles**.
6. La app genera el ingles desde los bloques actuales en espanol.
7. Ajusta los bloques visualmente.
8. Exporta el video.

La traduccion al ingles se hace desde el espanol ya guardado en los bloques. No vuelve a transcribir ni cambia los tiempos del video.

## Flujo manual con texto en espanol e ingles

El modo manual sirve cuando ya tienes el guion correcto.

Puedes pegar el texto completo en espanol:

```text
Primer parrafo del guion en espanol.

Segundo parrafo del guion en espanol.

Tercer parrafo del guion en espanol.
```

Y tambien pegar su version en ingles:

```text
First paragraph of the script in English.

Second paragraph of the script in English.

Third paragraph of the script in English.
```

La app separa ambos textos por parrafos y los empareja en orden:

```text
parrafo 1 espanol -> parrafo 1 ingles
parrafo 2 espanol -> parrafo 2 ingles
parrafo 3 espanol -> parrafo 3 ingles
```

Luego usa los tiempos detectados de voz para distribuir los subtitulos, buscando que cada parrafo en espanol y su equivalente en ingles terminen aproximadamente al mismo tiempo.

Este flujo ayuda cuando la traduccion ya esta corregida y solo quieres sincronizarla con el video.

## Editor visual

La interfaz esta organizada como un editor simple:

```text
Panel izquierdo   Preview central   Panel derecho
Barra inferior de acciones
```

Panel izquierdo:

- Historial de proyectos.
- Lista de bloques de subtitulos.
- Indicador del bloque seleccionado.
- Indicador del bloque activo durante la reproduccion.
- Opcion para agregar un bloque vacio si necesitas corregir una parte.

Preview central:

- Video vertical 9:16.
- Ingles arriba.
- Espanol abajo.
- Karaoke en palabras del espanol.
- Vista previa actualizada en tiempo real.

Panel derecho:

- Editar texto espanol.
- Editar texto ingles.
- Cambiar tamano del espanol o ingles.
- Subir o bajar posicion vertical.
- Guardar cambios.

## Exportacion

Antes de exportar, la app pide elegir una carpeta de destino. Dentro de esa carpeta crea una subcarpeta con el nombre del proyecto/video.

Ejemplo:

```text
Carpeta elegida/
  video_promocional/
    video_promocional.mp4
    video_promocional_portada.jpg
    video_promocional.mp3
```

El archivo principal exportado es el MP4 con subtitulos quemados. La portada y el MP3 se generan si activas esas opciones.

## Version portable

Ademas del instalador, el proyecto puede generar una version portable:

```text
Mini Editor Subtitulos.exe
```

Esta version sirve para probar la app sin instalarla.

## Datos locales

La aplicacion instalada guarda sus proyectos e historial local en:

```text
%APPDATA%\Mini Editor Subtitulos\data
```

Los videos finales se guardan en la carpeta que eliges al exportar.

## Desarrollo

Esta seccion es solo para quienes quieran modificar el codigo fuente o compilar una nueva version del instalador.

Tecnologias principales:

- Electron
- React
- Vite
- Python
- FastAPI
- faster-whisper
- imageio-ffmpeg
- PyInstaller
- electron-builder

Instalar dependencias:

```powershell
python -m pip install -r backend\requirements.txt
npm install
npm run frontend:install
```

Ejecutar en modo desarrollo:

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

En otra terminal:

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Ejecutar Electron en desarrollo:

```powershell
npm run desktop:dev
```

Compilar instalador de Windows:

```powershell
npm run frontend:build
npm run backend:build
npm run dist:win:ready
```

Los archivos generados quedan en:

```text
release/
```
