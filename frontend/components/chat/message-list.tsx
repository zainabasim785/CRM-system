"use client";

import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Volume2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ChatMessage } from "@/lib/chat/history-store";
import { formatMessageTime } from "@/lib/chat/history-store";
import { cn } from "@/lib/utils";

export function MessageList({
  messages,
  pending,
  showTimestamps = true,
  onSpeak,
}: {
  messages: ChatMessage[];
  pending?: boolean;
  showTimestamps?: boolean;
  onSpeak?: (text: string) => void;
}) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, pending]);

  const lastAssistant = [...messages]
    .reverse()
    .find((m) => m.role === "assistant");

  return (
    <div
      className="flex-1 space-y-3 overflow-y-auto px-0.5 py-1"
      role="log"
      aria-live="polite"
      aria-relevant="additions"
      aria-busy={pending || undefined}
    >
      {messages.length === 0 && !pending && (
        <p className="py-10 text-center text-sm text-muted-foreground">
          No messages yet. Ask about hours, availability, or booking.
        </p>
      )}
      {messages.map((message) => (
        <motion.div
          key={message.id}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
          className={cn(
            "flex",
            message.role === "user" ? "justify-end" : "justify-start"
          )}
        >
          <div
            className={cn(
              "max-w-[88%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm",
              message.role === "user" &&
                "rounded-br-md bg-primary text-primary-foreground",
              message.role === "assistant" &&
                "rounded-bl-md border bg-card text-card-foreground",
              message.role === "system" &&
                "w-full border border-amber-500/30 bg-amber-500/10 text-amber-900 dark:text-amber-100"
            )}
          >
            <p className="whitespace-pre-wrap">{message.content}</p>
            <div className="mt-2 flex flex-wrap items-center gap-1.5">
              {showTimestamps &&
                message.timestamp &&
                message.id !== "greeting" && (
                <time
                  dateTime={message.timestamp}
                  className={cn(
                    "text-[10px]",
                    message.role === "user"
                      ? "text-primary-foreground/65"
                      : "text-muted-foreground"
                  )}
                >
                  {formatMessageTime(message.timestamp)}
                </time>
              )}
              {message.intent && message.role === "assistant" && (
                <>
                  <Badge variant="secondary">{message.intent}</Badge>
                  {message.needsEscalation && (
                    <Badge variant="warning">escalation</Badge>
                  )}
                  {message.booking?.success && (
                    <Badge variant="success">booked</Badge>
                  )}
                </>
              )}
              {message.role === "assistant" && onSpeak && message.content && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-6 gap-1 px-2 text-[10px] text-muted-foreground"
                  onClick={() => onSpeak(message.content)}
                  aria-label="Listen to reply"
                >
                  <Volume2 className="h-3 w-3" aria-hidden />
                  Listen
                </Button>
              )}
            </div>
          </div>
        </motion.div>
      ))}
      {pending && (
        <div className="flex justify-start" aria-hidden="true">
          <div className="rounded-2xl rounded-bl-md border bg-card px-4 py-3 text-sm text-muted-foreground">
            <span className="inline-flex gap-1">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted-foreground/70" />
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted-foreground/70 [animation-delay:120ms]" />
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted-foreground/70 [animation-delay:240ms]" />
            </span>
          </div>
        </div>
      )}
      <div className="sr-only" aria-live="polite">
        {lastAssistant?.content}
      </div>
      <div ref={bottomRef} />
    </div>
  );
}
