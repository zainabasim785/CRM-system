export type AgentMode = "voice" | "text";

export type AgentStatus =
  | "idle"
  | "listening"
  | "thinking"
  | "speaking"
  | "escalated";

export type MessageRole = "visitor" | "agent" | "system";

export interface AgentMessage {
  id: string;
  role: MessageRole;
  text: string;
  timestamp: string;
}

export type AgentIntent =
  | "hours"
  | "availability"
  | "booking"
  | "general"
  | "escalate";

export interface AgentIntentResult {
  intent: AgentIntent;
  reply: string;
  requiresEscalation: boolean;
}