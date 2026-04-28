const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("subtitleDesktop", {
  chooseExportFolder: () => ipcRenderer.invoke("choose-export-folder"),
});
