"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/toast";
import { sendReceptionMessage } from "@/lib/api/reception";
import { getErrorMessage } from "@/lib/api/client";
import { useAuth } from "@/lib/auth/auth-context";
import { bookingSchema, type BookingFormValues } from "@/lib/validations";
import type { AgentResponse } from "@/types/api";

function buildBookingMessage(values: BookingFormValues): string {
  const notes = values.notes?.trim();
  return [
    `Please book an appointment for ${values.name}.`,
    `Email: ${values.email}.`,
    `Requested date: ${values.date} at ${values.time}.`,
    notes ? `Notes: ${notes}.` : null,
  ]
    .filter(Boolean)
    .join(" ");
}

export function BookingForm() {
  const { isAuthenticated, user } = useAuth();
  const toast = useToast();
  const [result, setResult] = useState<AgentResponse | null>(null);
  const [error, setError] = useState("");
  const form = useForm<BookingFormValues>({
    resolver: zodResolver(bookingSchema),
    defaultValues: {
      name: "",
      email: "",
      date: "",
      time: "15:00",
      notes: "",
    },
  });

  useEffect(() => {
    if (!user) return;
    if (!form.getValues("name") && user.full_name) {
      form.setValue("name", user.full_name);
    }
    if (!form.getValues("email") && user.email) {
      form.setValue("email", user.email);
    }
  }, [user, form]);

  const onSubmit = form.handleSubmit(async (values) => {
    setError("");
    setResult(null);
    try {
      const response = await sendReceptionMessage({
        message: buildBookingMessage(values),
        session_id: `book-${Date.now()}`,
      });
      setResult(response);
      if (response.booking?.success) {
        toast.success("Booking request accepted", response.reply);
      } else {
        toast.info("Agent replied", response.reply.slice(0, 120));
      }
    } catch (err) {
      const message = getErrorMessage(err);
      setError(message);
      toast.error("Booking request failed", message);
    }
  });

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="font-display">Request an appointment</CardTitle>
          <CardDescription>
            Submitted through POST /api/v1/reception/message (no separate booking
            endpoint exists). Sign in and connect Google Calendar for real
            calendar writes.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!isAuthenticated && (
            <p
              className="mb-4 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900"
              role="status"
            >
              You can send a request without signing in, but booking against your
              calendar requires{" "}
              <Link href="/login" className="underline">
                sign in
              </Link>{" "}
              + calendar connect on the dashboard.
            </p>
          )}
          <form onSubmit={onSubmit} className="space-y-4" noValidate>
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                aria-invalid={Boolean(form.formState.errors.name)}
                {...form.register("name")}
              />
              {form.formState.errors.name && (
                <p className="text-xs text-destructive" role="alert">
                  {form.formState.errors.name.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                aria-invalid={Boolean(form.formState.errors.email)}
                {...form.register("email")}
              />
              {form.formState.errors.email && (
                <p className="text-xs text-destructive" role="alert">
                  {form.formState.errors.email.message}
                </p>
              )}
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="date">Date</Label>
                <Input
                  id="date"
                  type="date"
                  aria-invalid={Boolean(form.formState.errors.date)}
                  {...form.register("date")}
                />
                {form.formState.errors.date && (
                  <p className="text-xs text-destructive" role="alert">
                    {form.formState.errors.date.message}
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="time">Time</Label>
                <Input
                  id="time"
                  type="time"
                  aria-invalid={Boolean(form.formState.errors.time)}
                  {...form.register("time")}
                />
                {form.formState.errors.time && (
                  <p className="text-xs text-destructive" role="alert">
                    {form.formState.errors.time.message}
                  </p>
                )}
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="notes">Notes</Label>
              <Textarea id="notes" {...form.register("notes")} />
            </div>
            {error && (
              <p className="text-sm text-destructive" role="alert">
                {error}
              </p>
            )}
            <Button type="submit" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting ? "Sending…" : "Send booking request"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="font-display">Agent response</CardTitle>
          <CardDescription>
            Exact fields returned by the reception API
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {!result && !error && (
            <p className="text-sm text-muted-foreground">
              Submit the form to see intent, reply, and booking payload.
            </p>
          )}
          {result && (
            <>
              <div className="flex flex-wrap gap-2">
                <Badge variant="secondary">{result.intent}</Badge>
                {result.booking && (
                  <Badge variant={result.booking.success ? "success" : "warning"}>
                    booking.success={String(result.booking.success)}
                  </Badge>
                )}
              </div>
              <p className="text-sm leading-relaxed">{result.reply}</p>
              {result.booking && (
                <pre className="overflow-x-auto rounded-lg bg-secondary p-3 text-xs">
                  {JSON.stringify(result.booking, null, 2)}
                </pre>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
