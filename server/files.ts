import multer from "multer";
import fs from "fs";
import path from "path";

const uploadDir = "uploads";
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir);
}

export const upload = multer({
  dest: uploadDir,
  limits: { fileSize: 50 * 1024 * 1024 }, // 50MB
  fileFilter: (_req, file, cb) => {
    const allowed = [
      "image/jpeg",
      "image/png",
      "application/pdf",
      "text/plain",
      "text/csv",
      "video/mp4",
      "audio/mpeg",
      "audio/wav",
    ];
    if (allowed.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error("File type not supported"));
    }
  },
});

export async function analyzeFile(filePath: string, mimeType: string): Promise<string> {
  try {
    if (mimeType.startsWith("image/")) {
      return `[Image file: ${path.basename(filePath)}]`;
    }
    if (mimeType === "application/pdf") {
      return `[PDF document: ${path.basename(filePath)}]`;
    }
    if (mimeType.startsWith("text/")) {
      const content = fs.readFileSync(filePath, "utf-8");
      return content.substring(0, 1000); // First 1000 chars
    }
    if (mimeType.startsWith("audio/")) {
      return `[Audio file: ${path.basename(filePath)}]`;
    }
    if (mimeType.startsWith("video/")) {
      return `[Video file: ${path.basename(filePath)}]`;
    }
    return `[File: ${path.basename(filePath)}]`;
  } catch (err) {
    return `[Error reading file: ${String(err)}]`;
  }
}
