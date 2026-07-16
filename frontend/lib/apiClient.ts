// =============================================================================
// API client — wraps fetch with a configurable base URL from env
// =============================================================================

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  headers?: Record<string, string>;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, headers = {} } = options;

  const url = `${BASE_URL}${path}`;

  const config: RequestInit = {
    method,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
  };

  if (body !== undefined) {
    config.body = JSON.stringify(body);
  }

  const res = await fetch(url, config);

  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`API ${res.status} on ${method} ${path}: ${errorBody}`);
  }

  return res.json();
}

// =============================================================================
// Exported endpoint helpers
// =============================================================================

import type {
  TriageRequest,
  TriageResponse,
  BookingRequest,
  BookingResponse,
  AvailabilityQuery,
  AvailabilityResponse,
  FollowUpRequest,
  FollowUpResponse,
} from "../types/api";

export const api = {
  /** POST /api/triage — classify intent & get a reply */
  triage(data: TriageRequest) {
    return request<TriageResponse>("/api/triage", {
      method: "POST",
      body: data,
    });
  },

  /** POST /api/booking — book an appointment */
  book(data: BookingRequest) {
    return request<BookingResponse>("/api/booking", {
      method: "POST",
      body: data,
    });
  },

  /** GET /api/availability — check available slots */
  getAvailability(query?: AvailabilityQuery) {
    const params = query?.date ? `?date=${query.date}` : "";
    return request<AvailabilityResponse>(`/api/availability${params}`);
  },

  /** POST /api/follow-up — continue a conversation */
  followUp(data: FollowUpRequest) {
    return request<FollowUpResponse>("/api/follow-up", {
      method: "POST",
      body: data,
    });
  },
};