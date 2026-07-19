import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

export const registerSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .max(128, "Password is too long"),
  full_name: z.string().max(200).optional().or(z.literal("")),
  phone: z.string().max(32).optional().or(z.literal("")),
});

export type RegisterFormValues = z.infer<typeof registerSchema>;

export const chatMessageSchema = z.object({
  message: z.string().min(1, "Message cannot be empty").max(4000),
});

export type ChatMessageFormValues = z.infer<typeof chatMessageSchema>;

/** Booking is submitted via POST /reception/message — no separate booking API. */
export const bookingSchema = z.object({
  name: z.string().min(1, "Name is required"),
  email: z.string().email("Enter a valid email"),
  date: z.string().min(1, "Date is required"),
  time: z.string().min(1, "Time is required"),
  notes: z.string().max(1000).optional().or(z.literal("")),
});

export type BookingFormValues = z.infer<typeof bookingSchema>;
