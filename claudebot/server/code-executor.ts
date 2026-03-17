import { execSync } from "child_process";
import fs from "fs";
import path from "path";

export async function executeCode(
  code: string,
  language: "python" | "javascript" | "bash" = "javascript"
): Promise<{ output: string; error?: string }> {
  try {
    const tmpDir = "tmp_code";
    if (!fs.existsSync(tmpDir)) {
      fs.mkdirSync(tmpDir);
    }

    let tmpFile: string;
    let cmd: string;

    switch (language) {
      case "python":
        tmpFile = path.join(tmpDir, `code_${Date.now()}.py`);
        fs.writeFileSync(tmpFile, code);
        cmd = `python3 "${tmpFile}"`;
        break;

      case "javascript":
        tmpFile = path.join(tmpDir, `code_${Date.now()}.js`);
        fs.writeFileSync(tmpFile, code);
        cmd = `node "${tmpFile}"`;
        break;

      case "bash":
        cmd = code;
        break;

      default:
        return { output: "", error: "Unsupported language" };
    }

    const output = execSync(cmd, { encoding: "utf-8", timeout: 5000, maxBuffer: 10 * 1024 * 1024 });

    // Cleanup temp file
    if (language !== "bash" && fs.existsSync(tmpFile)) {
      fs.unlinkSync(tmpFile);
    }

    return { output: output.trim() };
  } catch (err: any) {
    return {
      output: "",
      error: err.message || String(err),
    };
  }
}
