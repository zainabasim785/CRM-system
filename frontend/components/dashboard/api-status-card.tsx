"use client";

import { useEffect, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getHealth } from "@/lib/api/health";
import { getErrorMessage } from "@/lib/api/client";

export function ApiStatusCard() {
  const [status, setStatus] = useState<"loading" | "ok" | "down">("loading");
  const [environment, setEnvironment] = useState<string>("");
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const health = await getHealth();
        if (cancelled) return;
        setStatus(health.status === "ok" ? "ok" : "down");
        setEnvironment(health.environment);
      } catch (err) {
        if (cancelled) return;
        setStatus("down");
        setError(getErrorMessage(err));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="font-display">API status</CardTitle>
        <CardDescription>GET /health</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        {status === "loading" && (
          <p className="text-muted-foreground">Checking…</p>
        )}
        {status !== "loading" && (
          <div className="flex flex-wrap gap-2">
            <Badge variant={status === "ok" ? "success" : "warning"}>
              {status === "ok" ? "reachable" : "unreachable"}
            </Badge>
            {environment && <Badge variant="secondary">{environment}</Badge>}
          </div>
        )}
        {error && (
          <p className="text-destructive" role="alert">
            {error}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
