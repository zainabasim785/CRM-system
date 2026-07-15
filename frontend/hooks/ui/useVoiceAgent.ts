"use client";

import { useCallback, useRef, useState } from "react";
import { AgentMessage, AgentMode, AgentStatus } from "../../types/agent";
import { mockTranscribe, resolveIntent } from "../../lib/mockAgentEngine";

function createId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
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
    (visitorText: string) => {
      setStatus("thinking");

      setTimeout(() => {
        const result = resolveIntent(visitorText);
        setStatus(result.requiresEscalation ? "escalated" : "speaking");
        pushMessage({ role: "agent", text: result.reply });

        if (resetTimer.current) clearTimeout(resetTimer.current);

        const holdDuration = result.requiresEscalation
          ? 2400
          : Math.min(3200, 900 + result.reply.length * 22);

        resetTimer.current = setTimeout(() => setStatus("idle"), holdDuration);
      }, 1100);
    },
    [pushMessage]
  );

  const startListening = useCallback(() => {
    if (status !== "idle") return;
    setStatus("listening");
    setPartialCaption("");

    mockTranscribe(1800).then((text) => {
      setPartialCaption(text);
      setTimeout(() => {
        pushMessage({ role: "visitor", text });
        setPartialCaption("");
        respond(text);
      }, 500);
    });
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