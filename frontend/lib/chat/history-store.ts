import type { AgentResponse, IntentType } from "@/types/api";

const STORE_KEY = "crm_local_conversations";
const ACTIVE_KEY = "crm_active_session_id";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  intent?: IntentType;
  booking?: AgentResponse["booking"];
  needsEscalation?: boolean;
}

export interface StoredConversation {
  sessionId: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: ChatMessage[];
}

function canUseStorage(): boolean {
  return typeof window !== "undefined" && typeof localStorage !== "undefined";
}

export function listConversations(): StoredConversation[] {
  if (!canUseStorage()) return [];
  try {
    const raw = localStorage.getItem(STORE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as StoredConversation[];
    if (!Array.isArray(parsed)) return [];
    return parsed.sort(
      (a, b) =>
        new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
    );
  } catch {
    return [];
  }
}

function writeAll(conversations: StoredConversation[]): void {
  if (!canUseStorage()) return;
  localStorage.setItem(STORE_KEY, JSON.stringify(conversations));
}

export function getConversation(sessionId: string): StoredConversation | null {
  return listConversations().find((c) => c.sessionId === sessionId) ?? null;
}

export function upsertConversation(
  sessionId: string,
  messages: ChatMessage[]
): StoredConversation {
  const now = new Date().toISOString();
  const existing = listConversations();
  const firstUser = messages.find((m) => m.role === "user");
  const title =
    firstUser?.content.slice(0, 72) ||
    existing.find((c) => c.sessionId === sessionId)?.title ||
    "New conversation";

  const prev = existing.find((c) => c.sessionId === sessionId);
  const next: StoredConversation = {
    sessionId,
    title,
    createdAt: prev?.createdAt || now,
    updatedAt: now,
    messages,
  };

  const others = existing.filter((c) => c.sessionId !== sessionId);
  writeAll([next, ...others]);
  setActiveSessionId(sessionId);
  return next;
}

export function deleteConversation(sessionId: string): void {
  writeAll(listConversations().filter((c) => c.sessionId !== sessionId));
  if (getActiveSessionId() === sessionId) {
    clearActiveSessionId();
  }
}

export function clearAllConversations(): void {
  if (!canUseStorage()) return;
  localStorage.removeItem(STORE_KEY);
  clearActiveSessionId();
}

export function getActiveSessionId(): string | null {
  if (!canUseStorage()) return null;
  return localStorage.getItem(ACTIVE_KEY);
}

export function setActiveSessionId(sessionId: string): void {
  if (!canUseStorage()) return;
  localStorage.setItem(ACTIVE_KEY, sessionId);
}

export function clearActiveSessionId(): void {
  if (!canUseStorage()) return;
  localStorage.removeItem(ACTIVE_KEY);
}

export function formatMessageTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}
