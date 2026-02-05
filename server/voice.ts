import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
import fs from "fs";

const ELEVENLABS_API_KEY = process.env.ELEVENLABS_API_KEY;

if (!ELEVENLABS_API_KEY) {
  console.warn("⚠ ELEVENLABS_API_KEY not set. Voice features disabled.");
}

export async function textToSpeech(text: string, voiceId = "21m00Tcm4TlvDq8ikWAM") {
  if (!ELEVENLABS_API_KEY) {
    throw new Error("ElevenLabs API key not configured");
  }

  try {
    const client = new ElevenLabsClient({ apiKey: ELEVENLABS_API_KEY });
    const audioStream = await client.textToSpeech.convert(voiceId, {
      text,
      model_id: "eleven_flash_v2_5",
    });

    // Convert stream to buffer
    const chunks: Buffer[] = [];
    for await (const chunk of audioStream) {
      chunks.push(chunk as Buffer);
    }
    return Buffer.concat(chunks);
  } catch (err) {
    throw new Error(`TTS error: ${String(err)}`);
  }
}

export async function speechToText(audioBuffer: Buffer) {
  if (!ELEVENLABS_API_KEY) {
    throw new Error("ElevenLabs API key not configured");
  }

  try {
    const client = new ElevenLabsClient({ apiKey: ELEVENLABS_API_KEY });
    const result = await client.speechToText.convert({
      file: audioBuffer,
      model_id: "scribe_v1",
    });
    return result.text || "";
  } catch (err) {
    throw new Error(`STT error: ${String(err)}`);
  }
}

export const voices = [
  { id: "21m00Tcm4TlvDq8ikWAM", name: "Rachel" },
  { id: "EXAVITQu4vr4xnSDxMaL", name: "Bella" },
  { id: "EXAVITQu4vr4xnSDxMaL", name: "Antoni" },
  { id: "g5CIjZEefAQLP7XZqsQH", name: "Arnold" },
  { id: "jBpfuIE2acCO8z3wKNLl", name: "Domi" },
];
