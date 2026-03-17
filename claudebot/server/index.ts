import express, { Request, Response } from "express";
import cors from "cors";
import { WebSocketServer } from "ws";
import http from "http";
import { storage } from "./storage.js";
import { chat } from "./claude.js";
import { initDb } from "./db.js";
import { upload, analyzeFile } from "./files.js";
import { textToSpeech, voices } from "./voice.js";
import { executeCode } from "./code-executor.js";

const app = express();
const server = http.createServer(app);
const wss = new WebSocketServer({ server });

app.use(cors());
app.use(express.json());

// Initialize database
await initDb();

// Serve React frontend
app.use(express.static("dist"));

// REST API Routes

// Get all conversations
app.get("/api/conversations", async (_req: Request, res: Response) => {
  try {
    const convs = await storage.getConversations();
    res.json(convs);
  } catch (err) {
    res.status(500).json({ error: String(err) });
  }
});

// Create new conversation
app.post("/api/conversations", async (req: Request, res: Response) => {
  try {
    const conv = await storage.createConversation(req.body.title);
    res.json(conv);
  } catch (err) {
    res.status(500).json({ error: String(err) });
  }
});

// Get conversation messages
app.get("/api/conversations/:id/messages", async (req: Request, res: Response) => {
  try {
    const msgs = await storage.getMessages(req.params.id);
    res.json(msgs);
  } catch (err) {
    res.status(500).json({ error: String(err) });
  }
});

// Send message (REST endpoint for non-WebSocket clients)
app.post("/api/conversations/:id/messages", async (req: Request, res: Response) => {
  try {
    const { content } = req.body;
    const conversationId = req.params.id;

    // Save user message
    await storage.createMessage(conversationId, "user", content);

    // Get conversation history
    const msgs = await storage.getMessages(conversationId);
    const history = msgs.map((m) => ({ role: m.role as "user" | "assistant", content: m.content }));

    // Get Claude response
    const reply = await chat(history);

    // Save assistant message
    const assistantMsg = await storage.createMessage(conversationId, "assistant", reply);

    res.json(assistantMsg);
  } catch (err) {
    res.status(500).json({ error: String(err) });
  }
});

// File upload and analysis
app.post("/api/files/upload", upload.single("file"), async (req: Request, res: Response) => {
  try {
    if (!req.file) {
      res.status(400).json({ error: "No file provided" });
      return;
    }

    const analysis = await analyzeFile(req.file.path, req.file.mimetype);
    res.json({
      filename: req.file.originalname,
      mimetype: req.file.mimetype,
      size: req.file.size,
      analysis,
    });
  } catch (err) {
    res.status(500).json({ error: String(err) });
  }
});

// Text-to-Speech
app.post("/api/voice/tts", async (req: Request, res: Response) => {
  try {
    const { text, voiceId } = req.body;
    const audio = await textToSpeech(text, voiceId);
    res.set("Content-Type", "audio/mpeg");
    res.send(audio);
  } catch (err) {
    res.status(500).json({ error: String(err) });
  }
});

// Get available voices
app.get("/api/voice/voices", (_req: Request, res: Response) => {
  res.json(voices);
});

// Code execution
app.post("/api/execute", async (req: Request, res: Response) => {
  try {
    const { code, language } = req.body;
    const result = await executeCode(code, language || "javascript");
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: String(err) });
  }
});

// WebSocket for real-time chat
wss.on("connection", (ws) => {
  console.log("Client connected");

  ws.on("message", async (data) => {
    try {
      const { conversationId, content } = JSON.parse(data.toString());

      // Save user message
      const userMsg = await storage.createMessage(conversationId, "user", content);
      ws.send(JSON.stringify({ type: "message", data: userMsg }));

      // Get conversation history
      const msgs = await storage.getMessages(conversationId);
      const history = msgs.map((m) => ({ role: m.role as "user" | "assistant", content: m.content }));

      // Get Claude response
      const reply = await chat(history);

      // Save assistant message
      const assistantMsg = await storage.createMessage(conversationId, "assistant", reply);
      ws.send(JSON.stringify({ type: "message", data: assistantMsg }));
    } catch (err) {
      ws.send(JSON.stringify({ type: "error", message: String(err) }));
    }
  });

  ws.on("close", () => console.log("Client disconnected"));
});

// Health check
app.get("/api/health", (_req: Request, res: Response) => {
  res.json({ status: "ok" });
});

// Serve React app for all other routes
app.get("*", (_req: Request, res: Response) => {
  res.sendFile("dist/index.html", { root: "." });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`✓ Server running on http://localhost:${PORT}`);
});
