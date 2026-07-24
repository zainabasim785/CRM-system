import { api } from "@/lib/api/client";
import type { AppointmentListResponse } from "@/types/api";

export async function listAppointments(options?: {
  upcomingOnly?: boolean;
  limit?: number;
  skip?: number;
}): Promise<AppointmentListResponse> {
  const { data } = await api.get<AppointmentListResponse>("/api/v1/appointments", {
    params: {
      upcoming_only: options?.upcomingOnly ?? false,
      limit: options?.limit ?? 50,
      skip: options?.skip ?? 0,
    },
  });
  return data;
}
