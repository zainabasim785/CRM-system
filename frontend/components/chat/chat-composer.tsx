"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Mic, MicOff, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  chatMessageSchema,
  type ChatMessageFormValues,
} from "@/lib/validations";

export function ChatComposer({
  disabled,
  onSend,
  voiceSupported,
  listening,
  partial,
  onStartVoice,
  onStopVoice,
}: {
  disabled?: boolean;
  onSend: (message: string) => void;
  voiceSupported?: boolean;
  listening?: boolean;
  partial?: string;
  onStartVoice?: () => void;
  onStopVoice?: () => void;
}) {
  const form = useForm<ChatMessageFormValues>({
    resolver: zodResolver(chatMessageSchema),
    defaultValues: { message: "" },
  });

  const submit = form.handleSubmit((values) => {
    onSend(values.message);
    form.reset({ message: "" });
  });

  const messageError = form.formState.errors.message?.message;

  return (
    <div className="space-y-2 border-t bg-background pt-3">
      {listening && (
        <p className="px-1 text-xs italic text-muted-foreground" aria-live="polite">
          {partial || "Listening…"}
        </p>
      )}
      <form onSubmit={submit} className="flex items-center gap-2">
        {voiceSupported && (
          <Button
            type="button"
            variant={listening ? "destructive" : "outline"}
            size="icon"
            disabled={disabled}
            onClick={listening ? onStopVoice : onStartVoice}
            aria-label={listening ? "Stop listening" : "Start voice input"}
            aria-pressed={listening}
          >
            {listening ? <MicOff size={16} aria-hidden /> : <Mic size={16} aria-hidden />}
          </Button>
        )}
        <Input
          placeholder="Ask about hours, availability, or booking…"
          disabled={disabled || listening}
          aria-invalid={Boolean(messageError)}
          aria-describedby={messageError ? "chat-message-error" : undefined}
          {...form.register("message")}
        />
        <Button
          type="submit"
          size="icon"
          disabled={disabled || listening}
          aria-label="Send message"
        >
          <Send size={16} aria-hidden />
        </Button>
      </form>
      {messageError && (
        <p id="chat-message-error" className="text-xs text-destructive" role="alert">
          {messageError}
        </p>
      )}
    </div>
  );
}
