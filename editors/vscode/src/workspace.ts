import * as vscode from "vscode";
import * as path from "path";
import * as fs from "fs";

/** Markers that indicate a projio-managed workspace. */
const PROJIO_CONFIG = ".projio/config.yml";
const PROJIO_DIR = ".projio";

export interface WorkspaceInfo {
  detected: boolean;
  root?: string;
  configPath?: string;
  subsystems: string[];
}

/** Known projio subsystem directories inside .projio/ */
const KNOWN_SUBSYSTEMS = ["indexio", "notio", "codio", "biblio"] as const;

/**
 * Detect whether the current VS Code workspace contains a projio project.
 *
 * Checks each workspace folder for `.projio/config.yml`.
 * Returns info about the first match found.
 */
export async function detectWorkspace(): Promise<WorkspaceInfo> {
  const folders = vscode.workspace.workspaceFolders;
  if (!folders || folders.length === 0) {
    return { detected: false, subsystems: [] };
  }

  for (const folder of folders) {
    const configPath = path.join(folder.uri.fsPath, PROJIO_CONFIG);
    if (fs.existsSync(configPath)) {
      const projioDir = path.join(folder.uri.fsPath, PROJIO_DIR);
      const subsystems = KNOWN_SUBSYSTEMS.filter((s) =>
        fs.existsSync(path.join(projioDir, s))
      );

      return {
        detected: true,
        root: folder.uri.fsPath,
        configPath,
        subsystems,
      };
    }
  }

  return { detected: false, subsystems: [] };
}
