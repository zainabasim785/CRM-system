"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { MessageSquare, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { MessageList } from "@/components/chat/message-list";
import { PageHeader } from "@/components/layout/page-header";
import { useToast } from "@/components/ui/toast";
import {
  clearAllConversations,
  deleteConversation,
  formatMessageTime,
  listConversations,
  type StoredConversation,
} from "@/lib/chat/history-store";

export function HistoryPageClient() {
  const router = useRouter();
  const toast = useToast();
  const [conversations, setConversations] = useState<StoredConversation[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);

  const refresh = useCallback(() => {
    const items = listConversations();
    setConversations(items);
    setSelectedId((prev) => {
      if (prev && items.some((c) => c.sessionId === prev)) return prev;
      return items[0]?.sessionId ?? null;
    });
  }, []);

  useEffect(() => {
    refresh();
    setHydrated(true);
    const onStorage = (event: StorageEvent) => {
      if (event.key === "crm_local_conversations" || event.key === null) {
        refresh();
      }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, [refresh]);

  const selected = useMemo(
    () => conversations.find((c) => c.sessionId === selectedId) ?? null,
    [conversations, selectedId]
  );

  const handleClearAll = () => {
    if (
      !window.confirm(
        "Clear all local chat history on this device? This cannot be undone."
      )
    ) {
      return;
    }
    clearAllConversations();
    refresh();
    toast.success("History cleared", "Local conversations were removed from this browser.");
  };

  const handleDeleteOne = (sessionId: string) => {
    if (!window.confirm("Delete this conversation from local history?")) return;
    deleteConversation(sessionId);
    refresh();
    toast.info("Conversation deleted", "Removed from local history only.");
  };

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Workspace"
        title="Conversation history"
        description="Stored in your browser only. Continue a session with the same session id via the reception API."
        actions={
          <>
            <Button asChild>
              <Link href="/chat">
                <MessageSquare className="h-3.5 w-3.5" aria-hidden />
                New chat
              </Link>
            </Button>
            <Button
              variant="outline"
              onClick={handleClearAll}
              disabled={conversations.length === 0}
            >
              <Trash2 className="h-3.5 w-3.5" aria-hidden />
              Clear local
            </Button>
          </>
        }
      />

      {!hydrated ? (
        <div className="grid gap-4 lg:grid-cols-[300px_1fr]">
          <div className="h-72 animate-pulse rounded-2xl bg-muted" />
          <div className="h-72 animate-pulse rounded-2xl bg-muted" />
        </div>
      ) : conversations.length === 0 ? (
        <EmptyState
          icon={MessageSquare}
          title="No conversations yet"
          description="Start chatting and messages will appear here with timestamps."
          actionLabel="Open chat"
          onAction={() => router.push("/chat")}
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Previous chats</CardTitle>
              <CardDescription>{conversations.length} saved locally</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {conversations.map((conversation) => {
                const active = conversation.sessionId === selectedId;
                const count = conversation.messages.filter(
                  (m) => m.role === "user" || m.role === "assistant"
                ).length;
                return (
                  <button
                    key={conversation.sessionId}
                    type="button"
                    onClick={() => setSelectedId(conversation.sessionId)}
                    className={`w-full rounded-xl border px-3 py-2.5 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                      active
                        ? "border-foreground/15 bg-secondary"
                        : "hover:bg-secondary/70"
                    }`}
                    aria-current={active ? "true" : undefined}
                  >
                    <p className="line-clamp-2 text-sm font-medium">
                      {conversation.title}
                    </p>
                    <div className="mt-1.5 flex flex-wrap items-center gap-2">
                      <time
                        dateTime={conversation.updatedAt}
                        className="text-[11px] text-muted-foreground"
                      >
                        {formatMessageTime(conversation.updatedAt)}
                      </time>
                      <Badge variant="secondary">{count}</Badge>
                    </div>
                  </button>
                );
              })}
            </CardContent>
          </Card>

          <Card className="flex min-h-[480px] flex-col">
            {selected ? (
              <>
                <CardHeader className="border-b border-border/70">
                  <CardTitle className="text-lg">{selected.title}</CardTitle>
                  <CardDescription className="space-y-1">
                    <span className="block font-mono text-[11px]">
                      {selected.sessionId}
                    </span>
                    <span className="block">
                      Updated {formatMessageTime(selected.updatedAt)}
                    </span>
                  </CardDescription>
                  <div className="flex flex-wrap gap-2 pt-2">
                    <Button
                      size="sm"
                      onClick={() =>
                        router.push(
                          `/chat?session=${encodeURIComponent(selected.sessionId)}`
                        )
                      }
                    >
                      Continue
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDeleteOne(selected.sessionId)}
                    >
                      Delete locally
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="flex min-h-0 flex-1 flex-col p-4">
                  <MessageList messages={selected.messages} showTimestamps />
                </CardContent>
              </>
            ) : (
              <CardContent className="flex flex-1 items-center justify-center p-8">
                <p className="text-sm text-muted-foreground">
                  Select a conversation to view messages.
                </p>
              </CardContent>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
