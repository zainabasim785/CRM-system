"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { sendReceptionMessage } from "@/lib/api/reception";
import { getErrorMessage } from "@/lib/api/client";
import {
  getConversation,
  upsertConversation,
  type ChatMessage,
} from "@/lib/chat/history-store";
import type { AgentResponse, ConversationMessage } from "@/types/api";

export type { ChatMessage };

function createId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function createSessionId() {
  return `web-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function nowIso() {
  return new Date().toISOString();
}

function toHistory(messages: ChatMessage[]): ConversationMessage[] {
  return messages
    .filter((m) => m.id !== "greeting" && m.role !== "system")
    .slice(-12)
    .map((m) => ({
      role: m.role === "user" ? "user" : "assistant",
      content: m.content,
    }));
}

const DEFAULT_GREETING =
  "Hi — I can answer FAQs, check availability, or help book, reschedule, or cancel an appointment.";

/** Stable greeting timestamp so SSR and the first client paint match. */
const GREETING_TIMESTAMP = "1970-01-01T00:00:00.000Z";

export function useReceptionChat(options?: {
  initialGreeting?: string;
  resumeSessionId?: string | null;
  onAssistantReply?: (reply: string) => void;
}) {
  const greeting = options?.initialGreeting ?? DEFAULT_GREETING;
  const resumeSessionId = options?.resumeSessionId ?? null;
  const onAssistantReply = options?.onAssistantReply;

  const buildGreeting = useCallback(
    (): ChatMessage => ({
      id: "greeting",
      role: "assistant",
      content: greeting,
      timestamp: GREETING_TIMESTAMP,
    }),
    [greeting]
  );

  // Defer random/localStorage session ids until after mount to avoid hydration mismatch.
  const [sessionId, setSessionId] = useState(() => resumeSessionId ?? "");
  const [messages, setMessages] = useState<ChatMessage[]>(() => [buildGreeting()]);
  const [ready, setReady] = useState(false);

  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResponse, setLastResponse] = useState<AgentResponse | null>(null);
  const pendingRef = useRef(false);
  const messagesRef = useRef(messages);
  const sessionRef = useRef(sessionId);
  messagesRef.current = messages;
  sessionRef.current = sessionId;

  useEffect(() => {
    if (resumeSessionId) {
      const stored = getConversation(resumeSessionId);
      if (stored) {
        setSessionId(stored.sessionId);
        setMessages(stored.messages.length ? stored.messages : [buildGreeting()]);
      } else {
        setSessionId(resumeSessionId);
        setMessages([buildGreeting()]);
      }
    } else {
      setSessionId(createSessionId());
      setMessages([buildGreeting()]);
    }
    setError(null);
    setLastResponse(null);
    setReady(true);
  }, [resumeSessionId, buildGreeting]);

  // Persist locally whenever messages change (frontend-only history)
  useEffect(() => {
    if (!ready || !sessionId) return;
    const hasUserTurn = messages.some((m) => m.role === "user");
    if (!hasUserTurn) return;
    upsertConversation(sessionId, messages);
  }, [messages, sessionId, ready]);

  const startNewConversation = useCallback(() => {
    const nextId = createSessionId();
    setSessionId(nextId);
    setMessages([buildGreeting()]);
    setError(null);
    setLastResponse(null);
    setReady(true);
  }, [buildGreeting]);

  const send = useCallback(async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || pendingRef.current) return null;

    // Ensure a session exists before the first API call (client-only ids).
    let activeSession = sessionRef.current;
    if (!activeSession) {
      activeSession = createSessionId();
      sessionRef.current = activeSession;
      setSessionId(activeSession);
    }

    pendingRef.current = true;
    setError(null);
    setPending(true);

    const history = toHistory(messagesRef.current);
    const userMessage: ChatMessage = {
      id: createId(),
      role: "user",
      content: trimmed,
      timestamp: nowIso(),
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const result = await sendReceptionMessage({
        message: trimmed,
        session_id: activeSession,
        conversation_history: history,
      });

      if (result.session_id && result.session_id !== sessionRef.current) {
        setSessionId(result.session_id);
      }

      setLastResponse(result);
      if (result.reply) {
        onAssistantReply?.(result.reply);
      }
      setMessages((prev) => [
        ...prev,
        {
          id: createId(),
          role: "assistant",
          content: result.reply,
          timestamp: nowIso(),
          intent: result.intent,
          booking: result.booking,
          needsEscalation: result.needs_escalation,
        },
      ]);
      return result;
    } catch (err) {
      const message = getErrorMessage(err);
      setError(message);
      setMessages((prev) => [
        ...prev,
        {
          id: createId(),
          role: "system",
          content: message,
          timestamp: nowIso(),
        },
      ]);
      return null;
    } finally {
      pendingRef.current = false;
      setPending(false);
    }
  }, [onAssistantReply]);

  return {
    messages,
    pending,
    error,
    lastResponse,
    sessionId,
    ready,
    send,
    startNewConversation,
  };
}
