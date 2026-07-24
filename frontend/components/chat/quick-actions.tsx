"use client";

import { Button } from "@/components/ui/button";

const ACTIONS = [
  { label: "Business hours", message: "What are your business hours?" },
  {
    label: "Book appointment",
    message: "I'd like to book an appointment — what times are available?",
  },
  {
    label: "Cancel",
    message: "I need to cancel my appointment. Can you list my upcoming bookings?",
  },
  {
    label: "Reschedule",
    message: "I need to reschedule my appointment to a different time.",
  },
  {
    label: "Talk to human",
    message: "I'd like to speak with a human receptionist please.",
  },
] as const;

export function ChatQuickActions({
  disabled,
  onSelect,
}: {
  disabled?: boolean;
  onSelect: (message: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2 pb-2">
      {ACTIONS.map((action) => (
        <Button
          key={action.label}
          type="button"
          variant="outline"
          size="sm"
          className="h-8 rounded-full text-xs"
          disabled={disabled}
          onClick={() => onSelect(action.message)}
        >
          {action.label}
        </Button>
      ))}
    </div>
  );
}
