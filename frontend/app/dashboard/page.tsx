import Link from "next/link";
import { AccountCard } from "@/components/dashboard/account-card";
import { ApiStatusCard } from "@/components/dashboard/api-status-card";
import { AppointmentsPanel } from "@/components/dashboard/appointments-panel";
import { CalendarPanel } from "@/components/dashboard/calendar-panel";
import { InboxPanel } from "@/components/dashboard/inbox-panel";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Workspace"
        title="Dashboard"
        description="Account, calendar connection, and API health from existing endpoints only."
        actions={
          <>
            <Button asChild>
              <Link href="/chat">Open chat</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/book">Book</Link>
            </Button>
          </>
        }
      />

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        <AccountCard />
        <CalendarPanel />
        <ApiStatusCard />
      </div>

      <AppointmentsPanel upcomingOnly compact />

      <InboxPanel compact />

      <Card>
        <CardHeader>
          <CardTitle>Quick actions</CardTitle>
          <CardDescription>
            Booking, cancel, and reschedule flow through the reception agent.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Button asChild>
            <Link href="/chat">Chat with agents</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/history">View history</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/dashboard/appointments">All appointments</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/dashboard/inbox">Staff inbox</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
