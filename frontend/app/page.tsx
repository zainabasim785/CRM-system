"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  CalendarCheck,
  CalendarDays,
  Clock,
  Inbox,
  MessageSquare,
  Mic,
  Moon,
  PhoneOff,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const businessTypes = ["Clinics", "Salons", "Agencies", "Studios", "Offices"];

const capabilities = [
  {
    icon: MessageSquare,
    title: "Chat & voice",
    body: "Text by default. Mic input and read-aloud replies when you want them.",
    iconBg: "bg-sky-500/10 text-sky-700 dark:text-sky-300",
  },
  {
    icon: CalendarDays,
    title: "Booking & changes",
    body: "New slots, cancellations, reschedules — plain language in, calendar out.",
    iconBg: "bg-amber-500/10 text-amber-800 dark:text-amber-300",
  },
  {
    icon: Inbox,
    title: "Staff inbox",
    body: "Escalations and reminders in one place. Mark done when handled.",
    iconBg: "bg-rose-500/10 text-rose-700 dark:text-rose-300",
  },
  {
    icon: Mic,
    title: "Your FAQs",
    body: "Instant answers from your list. Everything else goes through triage.",
    iconBg: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
  },
];

const flow = [
  { title: "Visitor opens chat", body: "No app, no account — just your site." },
  { title: "Routine stuff gets handled", body: "Hours, slots, booking details." },
  { title: "Calendar updates", body: "Confirmed appointments land where you work." },
  { title: "Tricky cases escalate", body: "Staff sees it in the inbox." },
];

const moments = [
  {
    icon: Moon,
    label: "10:47 PM",
    title: "Someone checks hours before bed",
    body: "They get an answer instead of leaving.",
    wash: "from-indigo-500/5 to-transparent",
    iconBg: "bg-indigo-500/10 text-indigo-700 dark:text-indigo-300",
  },
  {
    icon: PhoneOff,
    label: "Busy afternoon",
    title: "Three calls, one front desk",
    body: "Chat keeps booking while you're on the phone.",
    wash: "from-amber-500/8 to-transparent",
    iconBg: "bg-amber-500/10 text-amber-800 dark:text-amber-300",
  },
  {
    icon: Clock,
    label: "Tuesday morning",
    title: "A client needs to move their slot",
    body: "They ask in chat — calendar updates on both sides.",
    wash: "from-emerald-500/5 to-transparent",
    iconBg: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
  },
];

const faqs = [
  {
    q: "Do visitors need to sign up?",
    a: "No. Chat is open to anyone. Staff sign in to connect a calendar and check the inbox.",
  },
  {
    q: "Where do bookings go?",
    a: "Your database, and Google Calendar if you've connected it.",
  },
  {
    q: "What if someone wants a real person?",
    a: "The chat flags it. You follow up the way you normally would — phone, email, whatever works.",
  },
  {
    q: "Can people cancel or reschedule?",
    a: "Yes, in conversation. The record and calendar both update.",
  },
];

const fade = {
  initial: { opacity: 0, y: 12 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-48px" },
  transition: { duration: 0.45, ease: "easeOut" as const },
};

const chatMessages = [
  { from: "visitor", text: "are you open saturday?" },
  {
    from: "desk",
    text: "Mon–Fri 9–6. Weekends by request — want me to find a slot?",
  },
  { from: "visitor", text: "book tuesday 2pm — sam, sam@mail.com" },
  { from: "desk", text: "Done. Tuesday 2:00 PM is on the calendar.", booked: true },
];

function ChatPreview() {
  return (
    <div className="relative">
      <div className="absolute -inset-4 -z-10 rounded-3xl bg-gradient-to-br from-amber-400/25 via-orange-500/15 to-rose-400/10 blur-2xl dark:from-amber-500/20 dark:via-orange-600/10 dark:to-rose-500/5" />

      <div className="overflow-hidden rounded-2xl border bg-card shadow-soft">
        <div className="flex items-center gap-2 border-b bg-muted/30 px-3 py-2.5">
          <div className="flex gap-1">
            <span className="h-2 w-2 rounded-full bg-red-400/80" />
            <span className="h-2 w-2 rounded-full bg-amber-400/80" />
            <span className="h-2 w-2 rounded-full bg-emerald-400/80" />
          </div>
          <p className="flex-1 truncate rounded-md border bg-background/80 px-2.5 py-0.5 text-center text-[11px] text-muted-foreground">
            yourbusiness.com
          </p>
        </div>

        <div className="border-b bg-muted/15 px-4 py-6">
          <div className="mx-auto max-w-[200px] space-y-2 opacity-40">
            <div className="h-2.5 w-full rounded bg-foreground/10" />
            <div className="h-2.5 w-4/5 rounded bg-foreground/10" />
            <div className="mt-3 h-16 rounded-lg bg-foreground/5" />
          </div>
        </div>

        <div className="border-t bg-card">
          <div className="flex items-center justify-between border-b px-4 py-2.5">
            <div>
              <p className="text-sm font-medium">Reception</p>
              <p className="text-xs text-muted-foreground">Usually replies quickly</p>
            </div>
            <span className="flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-700 dark:text-emerald-300">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              online
            </span>
          </div>

          <div className="space-y-3 p-4">
            {chatMessages.map((msg, i) => (
              <motion.div
                key={msg.text}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, delay: 0.35 + i * 0.2, ease: "easeOut" as const }}
                className={msg.from === "visitor" ? "flex justify-end" : "flex flex-col items-start gap-1.5"}
              >
                <p
                  className={
                    msg.from === "visitor"
                      ? "max-w-[88%] rounded-2xl rounded-br-sm bg-primary px-3.5 py-2.5 text-sm text-primary-foreground"
                      : "max-w-[88%] rounded-2xl rounded-bl-sm border bg-background px-3.5 py-2.5 text-sm leading-relaxed"
                  }
                >
                  {msg.text}
                </p>
                {"booked" in msg && msg.booked ? (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 1.35 }}
                    className="flex items-center gap-1.5 text-[11px] font-medium text-emerald-700 dark:text-emerald-400"
                  >
                    <CalendarCheck className="h-3 w-3" aria-hidden />
                    Added to Google Calendar
                  </motion.span>
                ) : null}
              </motion.div>
            ))}
          </div>

          <div className="border-t px-4 py-2.5">
            <p className="text-xs text-muted-foreground">
              Type a message…
              <span className="ml-0.5 inline-block h-3.5 w-px animate-pulse bg-foreground/35 align-middle" />
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LandingPage() {
  return (
    <div className="relative pb-24 pt-2 md:pb-32">
      {/* Full-bleed wash — extends behind header so there's no hard cutoff line */}
      <div
        className="pointer-events-none absolute left-1/2 -top-[5.5rem] -z-10 w-screen -translate-x-1/2 sm:-top-[6.5rem]"
        aria-hidden
      >
        <div className="hero-spotlight h-[min(1040px,calc(92vh+5.5rem))] sm:h-[min(1040px,calc(92vh+6.5rem))]" />
        <div className="hero-grid absolute inset-x-0 top-0 h-full opacity-40" />
        <div className="absolute left-[6%] top-32 h-80 w-80 animate-mesh-drift rounded-full bg-amber-400/18 blur-3xl dark:bg-amber-500/10" />
        <div className="absolute right-[4%] top-20 h-72 w-72 animate-mesh-drift-slow rounded-full bg-orange-400/14 blur-3xl dark:bg-orange-500/10" />
        <div className="absolute left-1/2 top-60 h-56 w-[32rem] -translate-x-1/2 rounded-full bg-rose-400/8 blur-3xl dark:bg-rose-500/5" />
      </div>

      {/* Hero */}
      <section className="grid gap-12 lg:grid-cols-2 lg:items-center lg:gap-14">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
          className="max-w-xl pt-6 md:pt-10"
        >
          <p className="inline-flex items-center gap-2 rounded-full border border-amber-500/20 bg-amber-500/10 px-3 py-1 text-sm text-amber-950 dark:text-amber-100/90">
            Built for small teams
          </p>
          <h1 className="mt-4 font-display text-4xl font-semibold leading-[1.1] tracking-tight sm:text-5xl">
            A reception desk{" "}
            <span className="relative whitespace-nowrap">
              <span className="relative z-10">on your site</span>
              <span className="absolute -inset-x-1 bottom-1 -z-0 h-3 rounded-sm bg-amber-400/35 dark:bg-amber-500/25" />
            </span>
            <span className="text-muted-foreground">.</span>
          </h1>
          <p className="mt-5 text-lg leading-relaxed text-muted-foreground">
            Front Desk handles hours, availability, booking, and rescheduling —
            then hands off the messy stuff to your team.
          </p>

          <div className="mt-5 flex flex-wrap gap-2">
            {businessTypes.map((type) => (
              <span
                key={type}
                className="rounded-md border bg-card/80 px-2.5 py-1 text-xs text-muted-foreground"
              >
                {type}
              </span>
            ))}
          </div>

          <div className="mt-8 flex flex-wrap gap-3">
            <Button size="lg" className="h-11" asChild>
              <Link href="/chat">
                Try the chat
                <ArrowRight className="h-4 w-4" aria-hidden />
              </Link>
            </Button>
            <Button size="lg" variant="outline" className="h-11" asChild>
              <Link href="/register">Staff login</Link>
            </Button>
          </div>
          <p className="mt-6 text-sm text-muted-foreground">
            No signup for visitors · Google Calendar for staff
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.1 }}
        >
          <ChatPreview />
          <p className="mt-4 text-center text-xs text-muted-foreground lg:text-left">
            Sits on your site like a real reception widget — your FAQs, your calendar.
          </p>
        </motion.div>
      </section>

      {/* Moments */}
      <motion.section {...fade} className="mt-28">
        <div className="max-w-xl">
          <p className="text-sm font-medium text-amber-800/80 dark:text-amber-400/80">
            Sound familiar?
          </p>
          <h2 className="mt-1 font-display text-2xl font-semibold tracking-tight sm:text-3xl">
            The moments you actually lose people
          </h2>
        </div>
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {moments.map((item, i) => (
            <motion.div
              key={item.title}
              {...fade}
              transition={{ ...fade.transition, delay: i * 0.06 }}
              className="group relative overflow-hidden rounded-2xl border bg-card p-6 shadow-soft transition-shadow hover:shadow-md"
            >
              <div
                className={`absolute inset-0 bg-gradient-to-br ${item.wash} opacity-80`}
              />
              <div className="relative">
                <div className="flex items-center gap-2.5">
                  <span
                    className={`flex h-8 w-8 items-center justify-center rounded-lg ${item.iconBg}`}
                  >
                    <item.icon className="h-4 w-4" aria-hidden />
                  </span>
                  <span className="text-xs font-medium text-muted-foreground">
                    {item.label}
                  </span>
                </div>
                <h3 className="mt-4 font-medium leading-snug">{item.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  {item.body}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* Two-up */}
      <motion.section {...fade} className="mt-28 grid gap-5 md:grid-cols-2">
        <div className="rounded-2xl border bg-card p-7 shadow-soft">
          <h2 className="font-display text-xl font-semibold tracking-tight">
            Most sites still say &ldquo;call us&rdquo;
          </h2>
          <p className="mt-3 leading-relaxed text-muted-foreground">
            People want answers at 10pm, not a voicemail. Give them chat without
            hiring overnight staff.
          </p>
        </div>
        <div className="rounded-2xl border border-amber-500/15 bg-gradient-to-br from-amber-500/8 to-transparent p-7 shadow-soft">
          <h2 className="font-display text-xl font-semibold tracking-tight">
            You stay in the loop
          </h2>
          <p className="mt-3 leading-relaxed text-muted-foreground">
            Dashboard for bookings, inbox for escalations, Google Calendar when
            you connect it. Easy tickets filtered out — you handle the rest.
          </p>
        </div>
      </motion.section>

      {/* Capabilities */}
      <motion.section {...fade} className="mt-28">
        <div className="max-w-xl">
          <h2 className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">
            What it does
          </h2>
          <p className="mt-2 text-muted-foreground">
            Hooked up to your database and calendar — not a widget template.
          </p>
        </div>
        <div className="mt-10 grid gap-4 sm:grid-cols-2">
          {capabilities.map((item, i) => (
            <motion.div
              key={item.title}
              {...fade}
              transition={{ ...fade.transition, delay: i * 0.05 }}
              className="group flex gap-4 rounded-2xl border bg-card p-5 shadow-soft transition-all hover:border-amber-500/20 hover:shadow-md"
            >
              <div
                className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${item.iconBg}`}
              >
                <item.icon className="h-[18px] w-[18px]" aria-hidden />
              </div>
              <div>
                <h3 className="font-medium">{item.title}</h3>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                  {item.body}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* Flow + quote */}
      <section className="mt-28 grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-start">
        <motion.div {...fade} className="rounded-2xl border bg-muted/25 p-7 sm:p-8">
          <h2 className="font-display text-2xl font-semibold tracking-tight">
            Typical flow
          </h2>
          <ol className="mt-8 space-y-0">
            {flow.map((step, i) => (
              <li key={step.title} className="relative flex gap-4 pb-8 last:pb-0">
                {i < flow.length - 1 ? (
                  <span className="absolute left-[11px] top-7 h-[calc(100%-12px)] w-px bg-gradient-to-b from-amber-500/35 to-border" />
                ) : null}
                <span className="relative z-10 mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-amber-500/25 bg-background text-xs font-medium">
                  {i + 1}
                </span>
                <div>
                  <p className="font-medium">{step.title}</p>
                  <p className="mt-0.5 text-sm text-muted-foreground">{step.body}</p>
                </div>
              </li>
            ))}
          </ol>
        </motion.div>

        <motion.blockquote
          {...fade}
          className="flex h-full flex-col justify-center rounded-2xl border border-amber-500/20 bg-gradient-to-br from-amber-500/8 to-transparent p-7 sm:p-8"
        >
          <p className="font-display text-xl leading-relaxed tracking-tight sm:text-2xl">
            Small teams shouldn&apos;t lose bookings because nobody picked up the
            phone.
          </p>
          <footer className="mt-5 text-sm text-muted-foreground">
            Why we built Front Desk
          </footer>
        </motion.blockquote>
      </section>

      {/* Staff */}
      <motion.section
        {...fade}
        className="mt-28 overflow-hidden rounded-2xl border bg-foreground text-background shadow-soft"
      >
        <div className="grid md:grid-cols-[1fr_auto] md:items-center">
          <div className="p-8 sm:p-10">
            <h2 className="font-display text-2xl font-semibold tracking-tight">
              For staff
            </h2>
            <p className="mt-3 max-w-md leading-relaxed text-background/75">
              Sign in, connect Google Calendar, check appointments and the inbox.
              That&apos;s the setup.
            </p>
          </div>
          <div className="border-t border-background/10 p-8 sm:p-10 md:border-l md:border-t-0">
            <Button
              size="lg"
              className="w-full bg-background text-foreground hover:bg-background/90 md:w-auto"
              asChild
            >
              <Link href="/dashboard">Open dashboard</Link>
            </Button>
          </div>
        </div>
      </motion.section>

      {/* FAQ */}
      <motion.section {...fade} className="mt-28">
        <h2 className="font-display text-2xl font-semibold tracking-tight">
          Questions
        </h2>
        <div className="mt-8 grid gap-3 sm:grid-cols-2">
          {faqs.map((item, i) => (
            <motion.div
              key={item.q}
              {...fade}
              transition={{ ...fade.transition, delay: i * 0.04 }}
              className="rounded-xl border bg-card/60 p-5 shadow-soft transition-colors hover:bg-card"
            >
              <h3 className="font-medium leading-snug">{item.q}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {item.a}
              </p>
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* CTA */}
      <motion.section
        {...fade}
        className="mt-28 rounded-2xl border border-amber-500/15 bg-gradient-to-br from-amber-500/6 via-muted/30 to-muted/20 px-6 py-10 sm:px-10 sm:py-12"
      >
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="font-display text-xl font-semibold tracking-tight">
              See it yourself
            </p>
            <p className="mt-1 text-muted-foreground">
              Chat as a visitor, or sign in as staff.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button size="lg" asChild>
              <Link href="/chat">Open chat</Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/book">Book form</Link>
            </Button>
          </div>
        </div>
      </motion.section>

      <footer className="mt-16 flex flex-col gap-4 border-t pt-8 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
        <span className="font-display text-base font-semibold text-foreground">
          Front Desk
        </span>
        <nav className="flex gap-6">
          <Link href="/chat" className="transition-colors hover:text-foreground">
            Chat
          </Link>
          <Link href="/dashboard" className="transition-colors hover:text-foreground">
            Dashboard
          </Link>
          <Link href="/login" className="transition-colors hover:text-foreground">
            Sign in
          </Link>
        </nav>
      </footer>
    </div>
  );
}
