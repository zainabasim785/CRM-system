/** Types matching backend app/schemas exactly — no invented fields. */

export type IntentType =
  | "faq"
  | "booking"
  | "cancel"
  | "reschedule"
  | "availability"
  | "escalate"
  | "general"
  | "follow_up";

export interface ConversationMessage {
  role: string;
  content: string;
}

export interface AgentRequest {
  message: string;
  session_id?: string | null;
  user_id?: string | null;
  conversation_history?: ConversationMessage[];
  metadata?: Record<string, unknown>;
}

export interface TriageResult {
  intent: IntentType;
  confidence: number;
  response: string;
  needs_escalation: boolean;
  escalate_reason?: string | null;
  faq_matched: boolean;
  raw_output?: string | null;
}

export interface BookingResult {
  success: boolean;
  action?: string | null;
  response: string;
  appointment_details: Record<string, unknown>;
  raw_output?: string | null;
}

export interface FollowUpResult {
  logged: boolean;
  summary: string;
  reminder_scheduled: boolean;
  reminder_details: Record<string, unknown>;
  raw_output?: string | null;
}

export interface AgentResponse {
  session_id?: string | null;
  intent: IntentType;
  reply: string;
  needs_escalation: boolean;
  escalate_reason?: string | null;
  triage?: TriageResult | null;
  booking?: BookingResult | null;
  follow_up?: FollowUpResult | null;
  metadata?: Record<string, unknown>;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string | null;
  phone?: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserRead {
  id: string;
  email: string;
  full_name?: string | null;
  phone?: string | null;
  role: "admin" | "receptionist" | "customer";
  is_active: boolean;
  created_at: string;
  updated_at: string;
  google_calendar_connected: boolean;
}

export interface RegisterResponse {
  user: UserRead;
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface CalendarConnectResponse {
  authorization_url: string;
}

export interface CalendarStatusResponse {
  connected: boolean;
  google_oauth_configured: boolean;
  token_expiry?: string | null;
}

export interface CalendarDisconnectResponse {
  connected: boolean;
  message: string;
}

export interface HealthResponse {
  status: string;
  environment: string;
}

export type AppointmentStatus =
  | "scheduled"
  | "cancelled"
  | "completed"
  | "rescheduled";

export interface AppointmentRead {
  id: string;
  user_id?: string | null;
  summary: string;
  description?: string | null;
  attendee_email?: string | null;
  attendee_name?: string | null;
  starts_at: string;
  ends_at: string;
  calendar_id: string;
  google_event_id?: string | null;
  status: AppointmentStatus;
  created_at: string;
  updated_at: string;
}

export interface AppointmentListResponse {
  items: AppointmentRead[];
  total: number;
}

export type ConversationStatus = "active" | "closed" | "escalated";
export type ReminderStatus = "scheduled" | "sent" | "cancelled" | "failed";

export interface InboxConversationItem {
  id: string;
  session_id: string;
  summary?: string | null;
  status: ConversationStatus;
  extra_data: Record<string, unknown>;
  updated_at: string;
  last_message?: string | null;
}

export interface InboxReminderItem {
  id: string;
  conversation_id?: string | null;
  session_id?: string | null;
  note: string;
  remind_at: string;
  status: ReminderStatus;
  created_at: string;
  updated_at: string;
}

export interface InboxResponse {
  escalated: InboxConversationItem[];
  reminders: InboxReminderItem[];
}
