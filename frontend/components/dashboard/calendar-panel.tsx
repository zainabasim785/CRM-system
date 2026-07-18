"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  connectCalendar,
  disconnectCalendar,
  getCalendarStatus,
} from "@/lib/api/calendar";
import { getErrorMessage } from "@/lib/api/client";
import { useAuth } from "@/lib/auth/auth-context";
import { useToast } from "@/components/ui/toast";
import type { CalendarStatusResponse } from "@/types/api";

export function CalendarPanel() {
  const { isAuthenticated, refreshUser } = useAuth();
  const toast = useToast();
  const [status, setStatus] = useState<CalendarStatusResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    if (!isAuthenticated) {
      setStatus(null);
      return;
    }
    setLoading(true);
    try {
      setError("");
      setStatus(await getCalendarStatus());
    } catch (err) {
      setError(getErrorMessage(err));
      setStatus(null);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    void load();
  }, [load]);

  // Refresh when user returns from Google OAuth tab
  useEffect(() => {
    const onFocus = () => {
      if (isAuthenticated) void load();
    };
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [isAuthenticated, load]);

  const onConnect = async () => {
    setBusy(true);
    setError("");
    try {
      const { authorization_url } = await connectCalendar();
      window.open(authorization_url, "_blank", "noopener,noreferrer");
      toast.info("Complete Google sign-in", "Return here and refresh status after approving access.");
    } catch (err) {
      const message = getErrorMessage(err);
      setError(message);
      toast.error("Could not start calendar connect", message);
    } finally {
      setBusy(false);
    }
  };

  const onDisconnect = async () => {
    setBusy(true);
    setError("");
    try {
      await disconnectCalendar();
      await refreshUser();
      await load();
      toast.success("Calendar disconnected");
    } catch (err) {
      const message = getErrorMessage(err);
      setError(message);
      toast.error("Disconnect failed", message);
    } finally {
      setBusy(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="font-display">Google Calendar</CardTitle>
          <CardDescription>
            Sign in to connect your calendar for real bookings.
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
    <Card>
      <CardHeader>
        <CardTitle className="font-display">Google Calendar</CardTitle>
        <CardDescription>
          Uses /api/v1/calendar/connect, /status, and /disconnect
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {loading && !status ? (
          <p className="text-sm text-muted-foreground">Loading status…</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            <Badge variant={status?.connected ? "success" : "warning"}>
              {status?.connected ? "connected" : "not connected"}
            </Badge>
            <Badge variant="secondary">
              oauth configured:{" "}
              {String(status?.google_oauth_configured ?? "unknown")}
            </Badge>
          </div>
        )}
        {status?.token_expiry && (
          <p className="text-sm text-muted-foreground">
            Token expiry: {status.token_expiry}
          </p>
        )}
        {error && (
          <p className="text-sm text-destructive" role="alert">
            {error}
          </p>
        )}
        <div className="flex flex-wrap gap-2">
          <Button onClick={onConnect} disabled={busy || loading}>
            Connect calendar
          </Button>
          <Button
            variant="outline"
            onClick={() => void load()}
            disabled={busy || loading}
          >
            Refresh status
          </Button>
          {status?.connected && (
            <Button
              variant="destructive"
              onClick={onDisconnect}
              disabled={busy || loading}
            >
              Disconnect
            </Button>
          )}
        </div>
        <p className="text-xs text-muted-foreground">
          After Google approval, return here and click Refresh status (or refocus
          this tab) to update the UI.
        </p>
      </CardContent>
    </Card>
  );
}
