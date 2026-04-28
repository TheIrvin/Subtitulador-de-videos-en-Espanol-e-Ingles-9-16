const { app, BrowserWindow, dialog, ipcMain } = require("electron");
const path = require("node:path");
const { spawn } = require("node:child_process");

const BACKEND_URL = "http://127.0.0.1:8000";
let backendProcess = null;

function backendExecutablePath() {
  if (!app.isPackaged) {
    return null;
  }
  return path.join(process.resourcesPath, "backend", "mini-subtitles-backend.exe");
}

function startBackend() {
  const appDataDir = path.join(app.getPath("userData"), "data");
  const env = {
    ...process.env,
    SUBTITLE_APP_DATA_DIR: appDataDir,
  };

  if (app.isPackaged) {
    backendProcess = spawn(backendExecutablePath(), [], {
      env,
      windowsHide: true,
      stdio: "ignore",
    });
  } else {
    backendProcess = spawn(
      "python",
      ["-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
      {
        cwd: path.join(__dirname, ".."),
        env,
        windowsHide: true,
        stdio: "ignore",
      },
    );
  }

  backendProcess.on("exit", () => {
    backendProcess = null;
  });
}

async function waitForBackend(retries = 80) {
  for (let index = 0; index < retries; index += 1) {
    try {
      const response = await fetch(`${BACKEND_URL}/api/health`);
      if (response.ok) return;
    } catch (_error) {
      // Backend is still starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error("No se pudo iniciar el backend local.");
}

function createWindow() {
  const window = new BrowserWindow({
    width: 1320,
    height: 840,
    minWidth: 1100,
    minHeight: 720,
    backgroundColor: "#0e1014",
    title: "Mini Editor de Subtitulos",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.cjs"),
    },
  });

  if (app.isPackaged) {
    window.loadFile(path.join(__dirname, "..", "frontend", "dist", "index.html"));
  } else {
    window.loadURL("http://127.0.0.1:5173");
  }
}

ipcMain.handle("choose-export-folder", async () => {
  const result = await dialog.showOpenDialog({
    title: "Elegir carpeta para guardar exports",
    properties: ["openDirectory", "createDirectory"],
  });

  if (result.canceled || !result.filePaths.length) {
    return "";
  }

  return result.filePaths[0];
});

app.whenReady().then(async () => {
  try {
    startBackend();
    await waitForBackend();
    createWindow();
  } catch (error) {
    dialog.showErrorBox("Error al iniciar", error.message);
    app.quit();
  }
});

app.on("window-all-closed", () => {
  app.quit();
});

app.on("before-quit", () => {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
});
