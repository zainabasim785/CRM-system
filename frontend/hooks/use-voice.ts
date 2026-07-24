"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type SpeechRecognitionLike = {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  start: () => void;
  stop: () => void;
  onresult:
    | ((event: {
        results: ArrayLike<ArrayLike<{ transcript: string }>> & {
          [index: number]: ArrayLike<{ transcript: string }> & {
            isFinal?: boolean;
          };
        };
      }) => void)
    | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
};

let cachedVoice: SpeechSynthesisVoice | null = null;
let voicesReady = false;

function preloadVoices(): void {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
  const voices = window.speechSynthesis.getVoices();
  if (voices.length) {
    resolveVoice(voices);
    voicesReady = true;
  }
}

function getRecognition(): SpeechRecognitionLike | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as {
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
    SpeechRecognition?: new () => SpeechRecognitionLike;
  };
  const Ctor = w.SpeechRecognition || w.webkitSpeechRecognition;
  return Ctor ? new Ctor() : null;
}

function scoreVoice(voice: SpeechSynthesisVoice): number {
  const name = voice.name.toLowerCase();
  let score = 0;

  if (/neural|natural|online|premium|enhanced/i.test(name)) score += 120;
  if (/microsoft (jenny|aria|sonia|libby|natasha|emma)/i.test(name)) score += 90;
  if (/google.*english.*(female|male|us|uk)/i.test(name)) score += 70;
  if (/samantha|karen|moira|daniel|fiona|tessa|veena/i.test(name)) score += 60;
  if (/en-us|en-gb/i.test(voice.lang)) score += 20;
  if (voice.localService && /natural|neural/i.test(name)) score += 15;

  // Old/default voices that sound robotic on Windows.
  if (/zira|david desktop|mark|helen|richard|james|linda|george|robot|compact|espeak|sapi/i.test(name)) {
    score -= 100;
  }
  if (/microsoft david|microsoft zira|microsoft mark/i.test(name)) score -= 80;

  return score;
}

/** Pick the most natural-sounding English voice available on this device. */
function pickNaturalVoice(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null {
  if (!voices.length) return null;

  const english = voices.filter((v) => v.lang.toLowerCase().startsWith("en"));
  const pool = english.length ? english : voices;

  const ranked = [...pool].sort((a, b) => scoreVoice(b) - scoreVoice(a));
  return ranked[0] ?? null;
}

function resolveVoice(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null {
  if (cachedVoice && voices.some((v) => v.name === cachedVoice!.name)) {
    return cachedVoice;
  }
  cachedVoice = pickNaturalVoice(voices);
  return cachedVoice;
}

/** Strip markdown / symbols that sound weird when spoken. */
export function cleanForSpeech(text: string): string {
  return text
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/[*_#~>]+/g, " ")
    .replace(/https?:\/\/\S+/g, " ")
    .replace(/\b(API|URL|OAuth|CRM)\b/gi, (_, word: string) => word.split("").join(" "))
    .replace(/(\d{1,2}):(\d{2})\s*(am|pm)?/gi, (_, h, m, ap) => {
      const suffix = ap ? ` ${ap.toUpperCase()}` : "";
      return `${h} ${m}${suffix}`;
    })
    .replace(/\s+/g, " ")
    .trim();
}

function splitForSpeech(text: string): string[] {
  // Short replies: one utterance starts instantly (no gap between sentences).
  if (text.length <= 260) return [text];
  const parts = text
    .split(/(?<=[.!?])\s+/)
    .map((part) => part.trim())
    .filter(Boolean);
  return parts.length ? parts : [text];
}

function waitForVoices(): Promise<SpeechSynthesisVoice[]> {
  return new Promise((resolve) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      resolve([]);
      return;
    }
    const existing = window.speechSynthesis.getVoices();
    if (existing.length) {
      resolve(existing);
      return;
    }
    const onChange = () => {
      window.speechSynthesis.removeEventListener("voiceschanged", onChange);
      resolve(window.speechSynthesis.getVoices());
    };
    window.speechSynthesis.addEventListener("voiceschanged", onChange);
    setTimeout(() => {
      window.speechSynthesis.removeEventListener("voiceschanged", onChange);
      resolve(window.speechSynthesis.getVoices());
    }, 1200);
  });
}

/** Call on a user click so Chrome/Edge allow speech later. */
export function primeSpeech(): boolean {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) {
    return false;
  }
  preloadVoices();
  window.speechSynthesis.resume();
  return true;
}

/** Warm up voices as soon as the chat page loads. */
export function preloadSpeech(): void {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
  preloadVoices();
  window.speechSynthesis.addEventListener("voiceschanged", preloadVoices, { once: true });
}

export function isSpeechSupported(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}

function speakOnce(text: string, voice: SpeechSynthesisVoice | null): Promise<boolean> {
  return new Promise((resolve) => {
    const utterance = new SpeechSynthesisUtterance(text);
    if (voice) {
      utterance.voice = voice;
      utterance.lang = voice.lang || "en-US";
    } else {
      utterance.lang = "en-US";
    }
    // Natural but not sluggish.
    utterance.rate = 1.02;
    utterance.pitch = 1.0;
    utterance.volume = 1;

    let finished = false;
    let started = false;
    let chromeFix: ReturnType<typeof setInterval> | null = null;

    const finish = (ok: boolean) => {
      if (finished) return;
      finished = true;
      if (chromeFix) clearInterval(chromeFix);
      resolve(ok && started);
    };

    utterance.onstart = () => {
      started = true;
    };
    utterance.onend = () => finish(true);
    utterance.onerror = () => finish(false);

    window.speechSynthesis.resume();
    window.speechSynthesis.speak(utterance);

    chromeFix = setInterval(() => {
      const synth = window.speechSynthesis;
      if (!synth.speaking && !synth.pending) {
        if (chromeFix) clearInterval(chromeFix);
        return;
      }
      synth.resume();
    }, 250);

    setTimeout(() => {
      if (!started) finish(false);
    }, 4000);
  });
}

function speakNow(text: string, voice: SpeechSynthesisVoice | null): void {
  const utterance = new SpeechSynthesisUtterance(text);
  if (voice) {
    utterance.voice = voice;
    utterance.lang = voice.lang || "en-US";
  } else {
    utterance.lang = "en-US";
  }
  utterance.rate = 1.02;
  utterance.pitch = 1.0;
  utterance.volume = 1;
  window.speechSynthesis.resume();
  window.speechSynthesis.speak(utterance);
}

export function speakText(text: string): Promise<boolean> {
  if (!isSpeechSupported()) {
    return Promise.resolve(false);
  }

  const cleaned = cleanForSpeech(text);
  if (!cleaned) return Promise.resolve(false);

  preloadVoices();
  const voice = resolveVoice(window.speechSynthesis.getVoices());
  if (window.speechSynthesis.speaking || window.speechSynthesis.pending) {
    window.speechSynthesis.cancel();
  }

  const chunks = splitForSpeech(cleaned);
  // Start the first chunk in the same tick as the message appearing.
  speakNow(chunks[0], voice);

  if (chunks.length === 1) {
    return Promise.resolve(true);
  }

  return (async () => {
    let anyStarted = true;
    for (let i = 1; i < chunks.length; i++) {
      await new Promise((r) => setTimeout(r, 60));
      const ok = await speakOnce(chunks[i], voice);
      anyStarted = anyStarted || ok;
    }
    return anyStarted;
  })();
}

export function stopSpeaking(): void {
  if (typeof window !== "undefined" && "speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
}

export function useVoiceInput(onFinal: (text: string) => void) {
  const [listening, setListening] = useState(false);
  const [partial, setPartial] = useState("");
  const [supported, setSupported] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);

  useEffect(() => {
    setSupported(Boolean(getRecognition()));
  }, []);

  const stop = useCallback(() => {
    recognitionRef.current?.stop();
    setListening(false);
  }, []);

  const start = useCallback(() => {
    const recognition = getRecognition();
    if (!recognition) {
      setError("Voice input needs Chrome or Edge.");
      return;
    }
    setError(null);
    stopSpeaking();
    recognitionRef.current = recognition;
    recognition.lang = "en-US";
    recognition.interimResults = true;
    recognition.continuous = false;
    setPartial("");
    setListening(true);

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0]?.transcript || "")
        .join("");
      setPartial(transcript);
      const last = event.results[event.results.length - 1] as
        | (ArrayLike<{ transcript: string }> & { isFinal?: boolean })
        | undefined;
      if (last?.isFinal) {
        setListening(false);
        setPartial("");
        onFinal(transcript.trim());
      }
    };
    recognition.onerror = () => {
      setListening(false);
      setPartial("");
      setError("Microphone blocked or unavailable. Allow mic access in browser settings.");
    };
    recognition.onend = () => {
      setListening(false);
    };
    recognition.start();
  }, [onFinal]);

  return { listening, partial, supported, error, start, stop };
}
