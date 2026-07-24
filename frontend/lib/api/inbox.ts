import { api } from "@/lib/api/client";
import type {
  InboxConversationItem,
  InboxReminderItem,
  InboxResponse,
} from "@/types/api";

export async function getInbox(): Promise<InboxResponse> {
  const { data } = await api.get<InboxResponse>("/api/v1/inbox");
  return data;
}

export async function resolveConversation(
  conversationId: string
): Promise<InboxConversationItem> {
  const { data } = await api.patch<InboxConversationItem>(
    `/api/v1/inbox/conversations/${conversationId}`,
    { status: "closed" }
  );
  return data;
}

export async function completeReminder(
  reminderId: string
): Promise<InboxReminderItem> {
  const { data } = await api.patch<InboxReminderItem>(
    `/api/v1/inbox/reminders/${reminderId}`,
    { status: "sent" }
  );
  return data;
}
