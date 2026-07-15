"use client";

import { motion } from "framer-motion";
import { AgentStatus } from "../../types/agent";

const TICK_COUNT = 24;

const STATUS_COLOR: Record<AgentStatus, string> = {
  idle: "#C7CCD1",
  listening: "#0F5C56",
  thinking: "#C08A3E",
  speaking: "#0F5C56",
  escalated: "#B3492F",
};

interface CallRingProps {
  status: AgentStatus;
}

export function CallRing({ status }: CallRingProps) {
  const color = STATUS_COLOR[status];
  const active = status !== "idle";

  return (
    <div className="relative flex h-24 w-24 items-center justify-center">
      <svg viewBox="0 0 100 100" className="absolute h-full w-full">
        {Array.from({ length: TICK_COUNT }).map((_, i) => {
          const angle = (360 / TICK_COUNT) * i;
          const delay = (i / TICK_COUNT) * 1.2;
          return (
            <motion.rect
              key={i}
              x="49"
              y="4"
              width="2"
              height="8"
              rx="1"
              fill={color}
              transform={`rotate(${angle} 50 50)`}
              animate={active ? { opacity: [0.25, 1, 0.25] } : { opacity: 0.3 }}
              transition={
                active
                  ? { duration: 1.2, repeat: Infinity, delay, ease: "easeInOut" }
                  : { duration: 0.3 }
              }
            />
          );
        })}
      </svg>
      <div
        className="flex h-14 w-14 items-center justify-center rounded-full transition-colors duration-300"
        style={{ backgroundColor: `${color}1A` }}
      >
        <div
          className="h-3 w-3 rounded-full transition-colors duration-300"
          style={{ backgroundColor: color }}
        />
      </div>
    </div>
  );
}