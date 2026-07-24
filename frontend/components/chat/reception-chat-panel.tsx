"use client";

import { useCallback, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { History, Plus, Volume2, VolumeX } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { MessageList } from "@/components/chat/message-list";
import { ChatComposer } from "@/components/chat/chat-composer";
import { ChatQuickActions } from "@/components/chat/quick-actions";
import { useReceptionChat } from "@/hooks/use-reception-chat";
import { speakText, stopSpeaking, useVoiceInput } from "@/hooks/use-voice";
import { useToast } from "@/components/ui/toast";

export function ReceptionChatPanel({
  title = "Reception",
  description = "Natural language through POST /api/v1/reception/message",
  resumeSessionId = null,
}: {
  title?: string;
  description?: string;
  resumeSessionId?: string | null;
}) {
  const router = useRouter();
  const toast = useToast();
  const [speakReplies, setSpeakReplies] = useState(false);
  const { messages, pending, error, send, sessionId, startNewConversation } =
    useReceptionChat({ resumeSessionId });

  const handleSend = useCallback(
    async (text: string) => {
      const result = await send(text);
      if (!result) {
        toast.error("Message failed", "The reception API could not process that request.");
        return;
      }
      if (result.booking?.success) {
        toast.success("Booking updated", result.booking.response || result.reply);
      } else if (result.needs_escalation) {
        toast.info("Escalated", "A staff member will follow up on this conversation.");
      }
      if (speakReplies && result.reply) {
        await speakText(result.reply);
      }
    },
    [send, speakReplies, toast]
  );

  const voice = useVoiceInput((text) => {
    void handleSend(text);
  });

  const toggleSpeak = () => {
    if (speakReplies) stopSpeaking();
    setSpeakReplies((v) => !v);
  };

  const handleNewChat = () => {
    startNewConversation();
    router.replace("/chat");
    toast.info("New conversation", "Started a fresh session.");
  };

  return (
    <Card className="flex h-[min(72vh,680px)] flex-col overflow-hidden">
      <CardHeader className="border-b border-border/70 bg-card/80">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <CardTitle>{title}</CardTitle>
            <CardDescription className="mt-1">{description}</CardDescription>
            <p className="mt-2 font-mono text-[11px] text-muted-foreground">
              session · {sessionId || "…"}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="outline" size="sm" asChild>
              <Link href="/history">
                <History className="h-3.5 w-3.5" aria-hidden />
                History
              </Link>
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={handleNewChat}>
              <Plus className="h-3.5 w-3.5" aria-hidden />
              New
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={toggleSpeak}
              aria-pressed={speakReplies}
            >
              {speakReplies ? (
                <Volume2 className="h-3.5 w-3.5" aria-hidden />
              ) : (
                <VolumeX className="h-3.5 w-3.5" aria-hidden />
              )}
              {speakReplies ? "Voice on" : "Voice off"}
            </Button>
          </div>
        </div>
        {error && (
          <p className="mt-3 text-sm text-destructive" role="alert">
            {error}
          </p>
        )}
      </CardHeader>
      <CardContent className="flex min-h-0 flex-1 flex-col p-4 sm:p-5">
        <MessageList messages={messages} pending={pending} />
        <ChatQuickActions disabled={pending} onSelect={(msg) => void handleSend(msg)} />
        <ChatComposer
          disabled={pending}
          onSend={(msg) => void handleSend(msg)}
          voiceSupported={voice.supported}
          listening={voice.listening}
          partial={voice.partial}
          onStartVoice={voice.start}
          onStopVoice={voice.stop}
        />
      </CardContent>
    </Card>
  );
}
