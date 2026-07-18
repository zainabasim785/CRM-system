import axios from "axios";
import { clearAccessToken, getAccessToken } from "@/lib/auth/token";

const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const AUTH_LOST_EVENT = "crm:auth-lost";

export const api = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 180_000,
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      const url = String(error.config?.url || "");
      if (!url.includes("/auth/login") && !url.includes("/auth/register")) {
        clearAccessToken();
        window.dispatchEvent(new Event(AUTH_LOST_EVENT));
      }
    }
    return Promise.reject(error);
  }
);

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
      if (/rate limit/i.test(detail)) {
        return "The AI provider is rate-limited. Wait ~30 seconds and try again.";
      }
      return detail;
    }
    if (Array.isArray(detail)) {
      return detail
        .map((item) =>
          typeof item === "object" && item && "msg" in item
            ? String(item.msg)
            : JSON.stringify(item)
        )
        .join(", ");
    }
    if (status === 502 || status === 503) {
      return "Reception agents are temporarily unavailable. Please try again shortly.";
    }
    if (error.code === "ECONNABORTED") {
      return "The request timed out. Please try again.";
    }
    if (!error.response) {
      return "Cannot reach the API. Is the backend running on NEXT_PUBLIC_API_URL?";
    }
    if (error.message) return error.message;
  }
  if (error instanceof Error) return error.message;
  return "Something went wrong";
}
