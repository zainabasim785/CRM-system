"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { CalendarDays, RefreshCw } from "lucide-react";
import { listAppointments } from "@/lib/api/appointments";
import { getErrorMessage } from "@/lib/api/client";
import { useAuth } from "@/lib/auth/auth-context";
import type { AppointmentRead } from "@/types/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";

function formatWhen(startsAt: string, endsAt: string): string {
  const start = new Date(startsAt);
  const end = new Date(endsAt);
  const date = start.toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  });
  const startTime = start.toLocaleTimeString(undefined, {
    hour: "numeric",
    minute: "2-digit",
  });
  const endTime = end.toLocaleTimeString(undefined, {
    hour: "numeric",
    minute: "2-digit",
  });
  return `${date} · ${startTime} – ${endTime}`;
}

function statusVariant(
  status: AppointmentRead["status"]
): "success" | "warning" | "secondary" | "outline" {
  switch (status) {
    case "scheduled":
      return "success";
    case "cancelled":
      return "warning";
    case "rescheduled":
      return "secondary";
    default:
      return "outline";
  }
}

export function AppointmentsPanel({
  upcomingOnly = false,
  compact = false,
}: {
  upcomingOnly?: boolean;
  compact?: boolean;
}) {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [items, setItems] = useState<AppointmentRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!isAuthenticated) {
      setItems([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await listAppointments({
        upcomingOnly,
        limit: compact ? 5 : 50,
      });
      setItems(data.items);
    } catch (err) {
      setError(getErrorMessage(err));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [compact, isAuthenticated, upcomingOnly]);

  useEffect(() => {
    if (!authLoading) {
      void load();
    }
  }, [authLoading, load]);

  if (authLoading || loading) {
    return (
      <Card>
        <CardContent className="p-6 text-sm text-muted-foreground">
          Loading appointments…
        </CardContent>
      </Card>
    );
  }

  if (!isAuthenticated) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="font-display">Appointments</CardTitle>
          <CardDescription>
            Sign in to view bookings saved in your database.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild>
            <Link href="/login">Sign in</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={compact ? undefined : "col-span-full"}>
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
        <div>
          <CardTitle className="font-display flex items-center gap-2">
            <CalendarDays className="h-4 w-4" aria-hidden />
            Appointments
          </CardTitle>
          <CardDescription>
            From your PostgreSQL database — no extra paid services.
          </CardDescription>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => void load()}
            aria-label="Refresh appointments"
          >
            <RefreshCw className="h-3.5 w-3.5" aria-hidden />
          </Button>
          {compact ? (
            <Button variant="outline" size="sm" asChild>
              <Link href="/dashboard/appointments">View all</Link>
            </Button>
          ) : null}
        </div>
      </CardHeader>
      <CardContent>
        {error ? (
          <p className="text-sm text-destructive">{error}</p>
        ) : items.length === 0 ? (
          <EmptyState
            icon={CalendarDays}
            title="No appointments yet"
            description="Bookings from chat appear here after a visitor completes a reservation."
            actionLabel="Open chat"
            onAction={() => {
              window.location.href = "/chat";
            }}
          />
        ) : (
          <ul className="divide-y rounded-xl border">
            {items.map((appt) => (
              <li
                key={appt.id}
                className="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="min-w-0 space-y-1">
                  <p className="font-medium leading-snug">{appt.summary}</p>
                  <p className="text-sm text-muted-foreground">
                    {formatWhen(appt.starts_at, appt.ends_at)}
                  </p>
                  {(appt.attendee_name || appt.attendee_email) && (
                    <p className="text-sm text-muted-foreground">
                      {[appt.attendee_name, appt.attendee_email]
                        .filter(Boolean)
                        .join(" · ")}
                    </p>
                  )}
                </div>
                <Badge variant={statusVariant(appt.status)}>{appt.status}</Badge>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
