import { AgentIntentResult } from '../types/agent';

const INTENT_LIBRARY: { keywords: string[]; result: AgentIntentResult }[] = [
  {
    keywords: ["hour", "open", "close"],
    result: {
      intent: "hours",
      reply:
        "We're open Monday to Saturday, 9 AM to 7 PM. Would you like me to check availability?",
      requiresEscalation: false,
    },
  },
  {
    keywords: ["book", "appointment", "schedule"],
    result: {
      intent: "booking",
      reply: "I can check availability now. What day works best for you?",
      requiresEscalation: false,
    },
  },
  {
    keywords: ["available", "availability", "free", "slot"],
    result: {
      intent: "availability",
      reply:
        "Tuesday and Thursday afternoons are open this week. Shall I hold a slot for you?",
      requiresEscalation: false,
    },
  },
  {
    keywords: ["refund", "complaint", "legal", "emergency", "urgent"],
    result: {
      intent: "escalate",
      reply: "This needs a closer look from our team. Connecting you to a human now.",
      requiresEscalation: true,
    },
  },
];

const FALLBACK: AgentIntentResult = {
  intent: "general",
  reply:
    "Got it. Could you tell me a little more, or would you like me to connect you with someone?",
  requiresEscalation: false,
};

export function resolveIntent(input: string): AgentIntentResult {
  const normalized = input.toLowerCase();
  const match = INTENT_LIBRARY.find(({ keywords }) =>
    keywords.some((keyword) => normalized.includes(keyword))
  );
  return match ? match.result : FALLBACK;
}

const SAMPLE_UTTERANCES = [
  "Hi, are you open on Saturdays?",
  "I'd like to book an appointment for next week.",
  "Do you have any availability on Thursday?",
  "I have a billing complaint I need help with.",
];

export function mockTranscribe(durationMs: number): Promise<string> {
  const text =
    SAMPLE_UTTERANCES[Math.floor(Math.random() * SAMPLE_UTTERANCES.length)];
  return new Promise((resolve) => setTimeout(() => resolve(text), durationMs));
}