"use client";

import { useCallback, useRef, useState } from "react";
import { AgentMessage, AgentMode, AgentStatus } from "../../types/agent";
import { api } from "../../lib/apiClient";

function createId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

/** Speak text using the browser's SpeechSynthesis API */
function speakText(text: string, onEnd: () => void) {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) {
    onEnd();
    return;
  }
  window.speechSynthesis.cancel(); // cancel any previous utterance
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-US";
  utterance.rate = 1.05;
  utterance.pitch = 1.0;
  utterance.onend = onEnd;
  utterance.onerror = onEnd;
  window.speechSynthesis.speak(utterance);
}

function timestampNow() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function buildGreeting(): AgentMessage {
  return {
    id: "greeting",
    role: "agent",
    text: "Hi, thanks for reaching out. I can check hours, availability, or book an appointment — how can I help?",
    timestamp: timestampNow(),
  };
}

export function useVoiceAgent() {
  const [mode, setMode] = useState<AgentMode>("voice");
  const [status, setStatus] = useState<AgentStatus>("idle");
  const [messages, setMessages] = useState<AgentMessage[]>([buildGreeting()]);
  const [partialCaption, setPartialCaption] = useState("");
  const convRef = useRef<string | null>(null);
  const resetTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const pushMessage = useCallback(
    (message: Omit<AgentMessage, "id" | "timestamp">) => {
      setMessages((prev) => [
        ...prev,
        { ...message, id: createId(), timestamp: timestampNow() },
      ]);
    },
    []
  );

  const respond = useCallback(
    async (visitorText: string) => {
      setStatus("thinking");

      try {
        // Call backend triage endpoint
        const result = await api.triage({
          message: visitorText,
          conversation_id: convRef.current ?? undefined,
        });

        // Save conversation ID for follow-ups
        convRef.current = result.conversation_id;

        pushMessage({ role: "agent", text: result.reply });

        if (result.requires_escalation) {
          setStatus("escalated");
          setTimeout(() => setStatus("idle"), 2400);
        } else {
          setStatus("speaking");
          // Speak the reply aloud using browser TTS
          speakText(result.reply, () => {
            setStatus("idle");
          });
        }
      } catch (err) {
        console.error("Triage API error:", err);
        pushMessage({
          role: "agent",
          text: "I'm sorry, I'm having trouble connecting right now. Please try again in a moment.",
        });
        setStatus("idle");
      }
    },
    [pushMessage]
  );

  const startListening = useCallback(() => {
    if (status !== "idle") return;
    setStatus("listening");
    setPartialCaption("");

    // Use browser SpeechRecognition if available, else simulate
    if (typeof window !== "undefined" && "webkitSpeechRecognition" in window) {
      const SpeechRecognition =
        (window as any).webkitSpeechRecognition ||
        (window as any).SpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.lang = "en-US";
      recognition.interimResults = true;

      recognition.onresult = (event: any) => {
        const transcript = Array.from(event.results)
          .map((r: any) => r[0].transcript)
          .join("");
        setPartialCaption(transcript);

        if (event.results[0].isFinal) {
          recognition.stop();
          pushMessage({ role: "visitor", text: transcript });
          setPartialCaption("");
          respond(transcript);
        }
      };

      recognition.onerror = () => {
        // Fall back to mock on error
        setStatus("idle");
        setPartialCaption("");
      };

      recognition.start();
    } else {
      // Fallback: mock transcription
      setTimeout(() => {
        const texts = [
          "Hi, are you open on Saturdays?",
          "I'd like to book an appointment for next week.",
          "Do you have any availability on Thursday?",
          "I have a billing complaint I need help with.",
        ];
        const text = texts[Math.floor(Math.random() * texts.length)];
        setPartialCaption(text);
        setTimeout(() => {
          pushMessage({ role: "visitor", text });
          setPartialCaption("");
          respond(text);
        }, 500);
      }, 1800);
    }
  }, [status, pushMessage, respond]);

  const sendTextMessage = useCallback(
    (text: string) => {
      if (!text.trim() || status !== "idle") return;
      pushMessage({ role: "visitor", text });
      respond(text);
    },
    [status, pushMessage, respond]
  );

  const toggleMode = useCallback(() => {
    setMode((prev) => (prev === "voice" ? "text" : "voice"));
  }, []);

  return {
    mode,
    status,
    messages,
    partialCaption,
    startListening,
    sendTextMessage,
    toggleMode,
  };
}