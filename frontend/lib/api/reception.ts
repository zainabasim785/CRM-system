import { api } from "@/lib/api/client";
import type { AgentRequest, AgentResponse } from "@/types/api";

export async function sendReceptionMessage(
  payload: AgentRequest
): Promise<AgentResponse> {
  const { data } = await api.post<AgentResponse>(
    "/api/v1/reception/message",
    payload
  );
  return data;
}
