"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Mic, MessageSquare, Send, X } from "lucide-react";
import { useVoiceAgent } from "../../hooks/ui/useVoiceAgent";
import { ChatBubble } from "../../components/shared/ChatBubble";
import { CallRing } from "../../components/shared/CallRing";
import { AgentStatus } from "../../types/agent";

const STATUS_LABEL: Record<AgentStatus, string> = {
  idle: "Ready to help",
  listening: "Listening…",
  thinking: "Checking that for you…",
  speaking: "Speaking…",
  escalated: "Connecting you to our team…",
};

export function VoiceChatWidget() {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  const {
    mode,
    status,
    messages,
    partialCaption,
    startListening,
    sendTextMessage,
    toggleMode,
    speakGreeting,
  } = useVoiceAgent();

  // Speak the greeting aloud when the widget opens in voice mode
  useEffect(() => {
    if (open && mode === "voice" && messages.length === 1) {
      const timer = setTimeout(() => speakGreeting(), 400);
      return () => clearTimeout(timer);
    }
  }, [open, mode, messages.length, speakGreeting]);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, partialCaption]);

  const handleSend = () => {
    if (!draft.trim()) return;
    sendTextMessage(draft);
    setDraft("");
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 16, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.96 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="flex h-[560px] w-[360px] max-w-[92vw] flex-col overflow-hidden rounded-3xl border border-[#E3E6E9] bg-[#F5F6F8] shadow-2xl"
          >
            <div className="flex items-center justify-between border-b border-[#E3E6E9] bg-white px-4 py-3">
              <div>
                <p className="text-sm font-semibold text-[#14181C]">Front Desk</p>
                <p
                  className={`text-xs ${
                    status === "escalated" ? "text-[#B3492F]" : "text-[#0F5C56]"
                  }`}
                >
                  {STATUS_LABEL[status]}
                </p>
              </div>
              <button
                onClick={() => setOpen(false)}
                aria-label="Close front desk widget"
                className="rounded-full p-1.5 text-[#8A9199] transition-colors hover:bg-[#F0F1F3] hover:text-[#14181C]"
              >
                <X size={18} />
              </button>
            </div>

            <div
              ref={scrollRef}
              className="flex-1 space-y-3 overflow-y-auto px-4 py-4"
            >
              {messages.map((message) => (
                <ChatBubble key={message.id} message={message} />
              ))}
              {partialCaption && (
                <div className="flex justify-end">
                  <p className="max-w-[80%] rounded-2xl rounded-br-sm bg-[#0F5C56]/10 px-4 py-2.5 font-mono text-sm italic text-[#0F5C56]">
                    {partialCaption}
                  </p>
                </div>
              )}
            </div>

            <div className="border-t border-[#E3E6E9] bg-white px-4 py-3">
              <div className="mb-2 flex items-center justify-center gap-2">
                <button
                  onClick={toggleMode}
                  className="flex items-center gap-1.5 rounded-full bg-[#F0F1F3] px-3 py-1 text-xs font-medium text-[#5B6570] transition-colors hover:bg-[#E3E6E9]"
                >
                  {mode === "voice" ? (
                    <MessageSquare size={13} />
                  ) : (
                    <Mic size={13} />
                  )}
                  Switch to {mode === "voice" ? "chat" : "voice"}
                </button>
              </div>

              {mode === "voice" ? (
                <div className="flex flex-col items-center gap-2 pb-1">
                  <button
                    onClick={startListening}
                    disabled={status !== "idle"}
                    aria-label="Start speaking"
                    className="disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    <CallRing status={status} />
                  </button>
                  <p className="text-[11px] text-[#8A9199]">
                    {status === "idle" ? "Tap to talk" : STATUS_LABEL[status]}
                  </p>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <input
                    value={draft}
                    onChange={(event) => setDraft(event.target.value)}
                    onKeyDown={(event) => event.key === "Enter" && handleSend()}
                    disabled={status !== "idle"}
                    placeholder="Type a message…"
                    className="flex-1 rounded-full border border-[#E3E6E9] bg-[#F5F6F8] px-4 py-2 text-sm text-[#14181C] outline-none focus:border-[#0F5C56] disabled:opacity-60"
                  />
                  <button
                    onClick={handleSend}
                    disabled={status !== "idle" || !draft.trim()}
                    aria-label="Send message"
                    className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#0F5C56] text-white transition-opacity disabled:opacity-40"
                  >
                    <Send size={15} />
                  </button>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {!open && (
        <motion.button
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          whileHover={{ scale: 1.05 }}
          onClick={() => setOpen(true)}
          aria-label="Open front desk assistant"
          className="flex h-14 w-14 items-center justify-center rounded-full bg-[#0F5C56] text-white shadow-lg"
        >
          <MessageSquare size={22} />
        </motion.button>
      )}
    </div>
  );
}