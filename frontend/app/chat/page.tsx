"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { ReceptionChatPanel } from "@/components/chat/reception-chat-panel";
import { PageHeader } from "@/components/layout/page-header";
import { Skeleton } from "@/components/ui/skeleton";

function ChatPageInner() {
  const searchParams = useSearchParams();
  const session = searchParams.get("session");

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Workspace"
        title="Chat"
        description={
          session
            ? "Continuing a saved local session through the reception API."
            : "Message the reception agents. History is saved locally in your browser."
        }
      />
      <ReceptionChatPanel title="AI reception" resumeSessionId={session} />
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense
      fallback={
        <div className="space-y-6">
          <Skeleton className="h-16 w-full max-w-xl" />
          <Skeleton className="h-[480px] w-full rounded-2xl" />
        </div>
      }
    >
      <ChatPageInner />
    </Suspense>
  );
}
