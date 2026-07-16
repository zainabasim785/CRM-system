// =============================================================================
// API endpoint types — matches FastAPI backend routes
// =============================================================================

/** Common response wrapper */
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string;
}

/** Triage endpoint: POST /api/triage */
export interface TriageRequest {
  message: string;
  conversation_id?: string;
}

export interface TriageResponse {
  intent: "hours" | "availability" | "booking" | "general" | "escalate";
  reply: string;
  requires_escalation: boolean;
  conversation_id: string;
}

/** Booking endpoint: POST /api/booking */
export interface BookingRequest {
  date: string;          // "YYYY-MM-DD"
  time?: string;         // "HH:MM"
  name: string;
  email: string;
  phone?: string;
  notes?: string;
}

export interface BookingResponse {
  confirmed: boolean;
  appointment_id?: string;
  message: string;
}

/** Availability endpoint: GET /api/availability */
export interface AvailabilityQuery {
  date?: string;         // "YYYY-MM-DD"
}

export interface AvailabilityResponse {
  slots: { date: string; time: string; available: boolean }[];
}

/** Follow-up endpoint: POST /api/follow-up */
export interface FollowUpRequest {
  conversation_id: string;
  message: string;
}

export interface FollowUpResponse {
  reply: string;
  requires_escalation: boolean;
}