import { AgentMessage } from "../../types/agent";

interface ChatBubbleProps {
  message: AgentMessage;
}

export function ChatBubble({ message }: ChatBubbleProps) {
  const isVisitor = message.role === "visitor";

  return (
    <div className={`flex ${isVisitor ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isVisitor
            ? "rounded-br-sm bg-[#0F5C56] text-white"
            : "rounded-bl-sm border border-[#E3E6E9] bg-white text-[#14181C]"
        }`}
      >
        <p>{message.text}</p>
        <span
          className={`mt-1 block font-mono text-[10px] ${
            isVisitor ? "text-white/60" : "text-[#8A9199]"
          }`}
        >
          {message.timestamp}
        </span>
      </div>
    </div>
  );
}