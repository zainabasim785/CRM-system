import { api } from "@/lib/api/client";
import type {
  CalendarConnectResponse,
  CalendarDisconnectResponse,
  CalendarStatusResponse,
} from "@/types/api";

export async function connectCalendar(): Promise<CalendarConnectResponse> {
  const { data } = await api.get<CalendarConnectResponse>(
    "/api/v1/calendar/connect"
  );
  return data;
}

export async function getCalendarStatus(): Promise<CalendarStatusResponse> {
  const { data } = await api.get<CalendarStatusResponse>(
    "/api/v1/calendar/status"
  );
  return data;
}

export async function disconnectCalendar(): Promise<CalendarDisconnectResponse> {
  const { data } = await api.delete<CalendarDisconnectResponse>(
    "/api/v1/calendar/disconnect"
  );
  return data;
}
