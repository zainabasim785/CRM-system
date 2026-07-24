import Link from "next/link";
import { InboxPanel } from "@/components/dashboard/inbox-panel";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";

export default function InboxPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Workspace"
        title="Staff inbox"
        description="Escalated visitor chats and internal follow-up reminders — no paid notification services."
        actions={
          <Button variant="outline" asChild>
            <Link href="/dashboard">Back to dashboard</Link>
          </Button>
        }
      />
      <InboxPanel />
    </div>
  );
}
