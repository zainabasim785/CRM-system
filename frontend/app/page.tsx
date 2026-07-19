"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  CalendarDays,
  MessageSquare,
  Mic,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const features = [
  {
    icon: MessageSquare,
    title: "AI chat",
    body: "Natural conversation through the reception agent endpoint — FAQs, booking, and escalation.",
  },
  {
    icon: Mic,
    title: "Voice interface",
    body: "Optional browser speech input and gentle TTS layered on the same chat API.",
  },
  {
    icon: CalendarDays,
    title: "Calendar aware",
    body: "Connect Google Calendar after sign-in so the agent can book against real availability.",
  },
];

const fade = {
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0 },
};

export default function LandingPage() {
  return (
    <div className="relative space-y-24 pb-20">
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[520px] surface-grid" />

      <section className="pt-10 md:pt-16">
        <motion.div
          {...fade}
          transition={{ duration: 0.45, ease: "easeOut" }}
          className="mx-auto max-w-3xl text-center"
        >
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border bg-card/80 px-3 py-1 text-xs text-muted-foreground shadow-soft">
            <Sparkles className="h-3.5 w-3.5" aria-hidden />
            AI reception for modern teams
          </div>
          <h1 className="font-display text-balance text-4xl font-semibold tracking-tight sm:text-5xl md:text-6xl">
            Front Desk
          </h1>
          <p className="mx-auto mt-3 max-w-xl text-balance text-lg text-muted-foreground sm:text-xl">
            Answers questions, checks availability, and books appointments —
            so people only step in when a human is needed.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Button size="lg" asChild>
              <Link href="/chat">
                Open chat <ArrowRight className="h-4 w-4" aria-hidden />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/register">Create account</Link>
            </Button>
          </div>
        </motion.div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {features.map((feature, index) => (
          <motion.div
            key={feature.title}
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ delay: index * 0.07, duration: 0.35 }}
            className="rounded-2xl border bg-card/90 p-6 shadow-soft"
          >
            <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-lg border bg-background">
              <feature.icon className="h-4 w-4" aria-hidden />
            </div>
            <h2 className="font-display text-base font-semibold tracking-tight">
              {feature.title}
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              {feature.body}
            </p>
          </motion.div>
        ))}
      </section>

      <motion.section
        initial={{ opacity: 0, y: 10 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="rounded-3xl border bg-foreground px-6 py-12 text-background shadow-soft sm:px-10"
      >
        <div className="flex flex-col items-start justify-between gap-6 md:flex-row md:items-center">
          <div>
            <h2 className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">
              Ready when your backend is.
            </h2>
            <p className="mt-2 max-w-lg text-sm text-background/70">
              Point NEXT_PUBLIC_API_URL at your API and start chatting.
            </p>
          </div>
          <Button
            size="lg"
            className="bg-background text-foreground hover:bg-background/90"
            asChild
          >
            <Link href="/dashboard">Go to dashboard</Link>
          </Button>
        </div>
      </motion.section>
    </div>
  );
}
