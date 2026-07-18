"use client";

import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth/auth-context";

export function AccountCard() {
  const { user, loading, isAuthenticated } = useAuth();

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6 text-sm text-muted-foreground">
          Loading account…
        </CardContent>
      </Card>
    );
  }

  if (!isAuthenticated || !user) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="font-display">Account</CardTitle>
          <CardDescription>
            Sign in to load GET /api/v1/auth/me
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted-foreground">
            You’re signed out. Auth-only features (calendar connect) need a JWT.
          </p>
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
        <CardTitle className="font-display">Account</CardTitle>
        <CardDescription>From GET /api/v1/auth/me</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div className="flex flex-wrap gap-2">
          <Badge variant="secondary">{user.role}</Badge>
          <Badge variant={user.is_active ? "success" : "warning"}>
            {user.is_active ? "active" : "inactive"}
          </Badge>
          <Badge variant={user.google_calendar_connected ? "success" : "outline"}>
            calendar: {user.google_calendar_connected ? "yes" : "no"}
          </Badge>
        </div>
        <dl className="grid gap-2">
          <div>
            <dt className="text-muted-foreground">Email</dt>
            <dd>{user.email}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Name</dt>
            <dd>{user.full_name || "—"}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Phone</dt>
            <dd>{user.phone || "—"}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">User id</dt>
            <dd className="break-all font-mono text-xs">{user.id}</dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
}
