import Link from "next/link";
import { AppointmentsPanel } from "@/components/dashboard/appointments-panel";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";

export default function AppointmentsPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Workspace"
        title="Appointments"
        description="All bookings stored in your database. Google Calendar sync uses the free OAuth API you already connected."
        actions={
          <>
            <Button variant="outline" asChild>
              <Link href="/dashboard">Back to dashboard</Link>
            </Button>
            <Button asChild>
              <Link href="/chat">New booking via chat</Link>
            </Button>
          </>
        }
      />
      <AppointmentsPanel upcomingOnly={false} />
    </div>
  );
}
