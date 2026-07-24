"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { AlertCircle, Bell, Check, RefreshCw } from "lucide-react";
import {
  completeReminder,
  getInbox,
  resolveConversation,
} from "@/lib/api/inbox";
import { getErrorMessage } from "@/lib/api/client";
import { useAuth } from "@/lib/auth/auth-context";
import type { InboxConversationItem, InboxReminderItem } from "@/types/api";
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

function formatWhen(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function InboxPanel({ compact = false }: { compact?: boolean }) {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [escalated, setEscalated] = useState<InboxConversationItem[]>([]);
  const [reminders, setReminders] = useState<InboxReminderItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!isAuthenticated) {
      setEscalated([]);
      setReminders([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await getInbox();
      setEscalated(compact ? data.escalated.slice(0, 3) : data.escalated);
      setReminders(compact ? data.reminders.slice(0, 3) : data.reminders);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [compact, isAuthenticated]);

  useEffect(() => {
    if (!authLoading) void load();
  }, [authLoading, load]);

  const handleResolve = async (id: string) => {
    setBusyId(id);
    try {
      await resolveConversation(id);
      setEscalated((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusyId(null);
    }
  };

  const handleReminderDone = async (id: string) => {
    setBusyId(id);
    try {
      await completeReminder(id);
      setReminders((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusyId(null);
    }
  };

  if (authLoading || loading) {
    return (
      <Card>
        <CardContent className="p-6 text-sm text-muted-foreground">
          Loading inbox…
        </CardContent>
      </Card>
    );
  }

  if (!isAuthenticated) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="font-display">Staff inbox</CardTitle>
          <CardDescription>Sign in to view escalations and reminders.</CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild>
            <Link href="/login">Sign in</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  const empty = escalated.length === 0 && reminders.length === 0;

  return (
    <Card className={compact ? undefined : "col-span-full"}>
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
        <div>
          <CardTitle className="font-display flex items-center gap-2">
            <Bell className="h-4 w-4" aria-hidden />
            Staff inbox
          </CardTitle>
          <CardDescription>
            Escalated chats and follow-up reminders — stored in your free PostgreSQL database.
          </CardDescription>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => void load()}>
            <RefreshCw className="h-3.5 w-3.5" aria-hidden />
          </Button>
          {compact ? (
            <Button variant="outline" size="sm" asChild>
              <Link href="/dashboard/inbox">Open inbox</Link>
            </Button>
          ) : null}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        {empty ? (
          <EmptyState
            icon={Bell}
            title="Inbox is clear"
            description="Escalations and follow-up reminders from the AI agents will show up here."
          />
        ) : (
          <>
            {escalated.length > 0 ? (
              <section className="space-y-2">
                <h3 className="flex items-center gap-2 text-sm font-medium">
                  <AlertCircle className="h-4 w-4 text-amber-600" aria-hidden />
                  Escalated ({escalated.length})
                </h3>
                <ul className="divide-y rounded-xl border">
                  {escalated.map((item) => (
                    <li key={item.id} className="space-y-2 px-4 py-3">
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <div className="min-w-0">
                          <p className="font-medium">
                            {item.summary || "Needs human help"}
                          </p>
                          <p className="text-sm text-muted-foreground line-clamp-2">
                            {item.last_message || "No transcript yet"}
                          </p>
                          <p className="mt-1 text-xs text-muted-foreground">
                            Updated {formatWhen(item.updated_at)}
                          </p>
                        </div>
                        <Badge variant="warning">escalated</Badge>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {item.session_id ? (
                          <Button variant="outline" size="sm" asChild>
                            <Link href={`/chat?session=${item.session_id}`}>
                              Open chat
                            </Link>
                          </Button>
                        ) : null}
                        <Button
                          size="sm"
                          disabled={busyId === item.id}
                          onClick={() => void handleResolve(item.id)}
                        >
                          <Check className="h-3.5 w-3.5" aria-hidden />
                          Mark resolved
                        </Button>
                      </div>
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}

            {reminders.length > 0 ? (
              <section className="space-y-2">
                <h3 className="text-sm font-medium">
                  Reminders ({reminders.length})
                </h3>
                <ul className="divide-y rounded-xl border">
                  {reminders.map((item) => (
                    <li
                      key={item.id}
                      className="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
                    >
                      <div>
                        <p className="text-sm">{item.note}</p>
                        <p className="text-xs text-muted-foreground">
                          Due {formatWhen(item.remind_at)}
                        </p>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={busyId === item.id}
                        onClick={() => void handleReminderDone(item.id)}
                      >
                        Done
                      </Button>
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}
          </>
        )}
      </CardContent>
    </Card>
  );
}
