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

function getRecognition(): SpeechRecognitionLike | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as {
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
    SpeechRecognition?: new () => SpeechRecognitionLike;
  };
  const Ctor = w.SpeechRecognition || w.webkitSpeechRecognition;
  return Ctor ? new Ctor() : null;
}

/** Prefer calm, natural English voices; avoid novelty / robotic defaults. */
function pickNaturalVoice(): SpeechSynthesisVoice | null {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) {
    return null;
  }
  const voices = window.speechSynthesis.getVoices();
  if (!voices.length) return null;

  const english = voices.filter((v) => v.lang.toLowerCase().startsWith("en"));
  const pool = english.length ? english : voices;

  const preferred = [
    /samantha/i,
    /karen/i,
    /moira/i,
    /aria/i,
    /jenny/i,
    /google us english/i,
    /microsoft aria/i,
    /microsoft jenny/i,
    /natural/i,
    /enhanced/i,
  ];

  for (const pattern of preferred) {
    const match = pool.find((v) => pattern.test(v.name));
    if (match) return match;
  }

  // Prefer local high-quality voices over remote novelty ones
  const local = pool.find((v) => v.localService && /en-?us/i.test(v.lang));
  if (local) return local;

  return pool.find((v) => /en-?us/i.test(v.lang)) || pool[0] || null;
}

/** Strip markdown / symbols that sound weird when spoken. */
export function cleanForSpeech(text: string): string {
  return text
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/[*_#~>]+/g, " ")
    .replace(/https?:\/\/\S+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
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
    // Fallback if event never fires
    setTimeout(() => {
      window.speechSynthesis.removeEventListener("voiceschanged", onChange);
      resolve(window.speechSynthesis.getVoices());
    }, 500);
  });
}

export async function speakText(text: string): Promise<void> {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) {
    return;
  }

  const cleaned = cleanForSpeech(text);
  if (!cleaned) return;

  await waitForVoices();
  window.speechSynthesis.cancel();

  // Chrome sometimes needs a tiny pause after cancel
  await new Promise((r) => setTimeout(r, 40));

  return new Promise((resolve) => {
    const utterance = new SpeechSynthesisUtterance(cleaned);
    const voice = pickNaturalVoice();
    if (voice) {
      utterance.voice = voice;
      utterance.lang = voice.lang || "en-US";
    } else {
      utterance.lang = "en-US";
    }
    // Calm, natural delivery — avoid fast/high “robot” defaults
    utterance.rate = 0.92;
    utterance.pitch = 1.0;
    utterance.volume = 0.9;
    utterance.onend = () => resolve();
    utterance.onerror = () => resolve();
    window.speechSynthesis.speak(utterance);
  });
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
    if (!recognition) return;
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
    };
    recognition.onend = () => {
      setListening(false);
    };
    recognition.start();
  }, [onFinal]);

  return { listening, partial, supported, start, stop };
}
