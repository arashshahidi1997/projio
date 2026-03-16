import * as vscode from "vscode";
import { detectWorkspace } from "./workspace";

export function activate(context: vscode.ExtensionContext) {
  console.log("Projio extension activated");

  context.subscriptions.push(
    vscode.commands.registerCommand("projio.hello", () => {
      vscode.window.showInformationMessage(
        "Hello from Projio! Your research workspace assistant is ready."
      );
    }),

    vscode.commands.registerCommand("projio.detectWorkspace", async () => {
      const info = await detectWorkspace();
      if (info.detected) {
        const subs =
          info.subsystems.length > 0
            ? `\nActive subsystems: ${info.subsystems.join(", ")}`
            : "";
        vscode.window.showInformationMessage(
          `Projio workspace detected at ${info.root}${subs}`
        );
      } else {
        vscode.window.showWarningMessage(
          "No projio workspace found. Run `projio init .` in your project to set one up."
        );
      }
    }),

    vscode.commands.registerCommand("projio.showStatus", async () => {
      const info = await detectWorkspace();
      if (!info.detected) {
        vscode.window.showWarningMessage("No projio workspace detected.");
        return;
      }

      const lines = [
        `Projio workspace: ${info.root}`,
        `Config: ${info.configPath}`,
        `Subsystems: ${info.subsystems.length > 0 ? info.subsystems.join(", ") : "none detected"}`,
      ];

      const doc = await vscode.workspace.openTextDocument({
        content: lines.join("\n"),
        language: "markdown",
      });
      await vscode.window.showTextDocument(doc, { preview: true });
    })
  );
}

export function deactivate() {}
