import { api } from "@/lib/api/client";
import type {
  LoginRequest,
  RegisterRequest,
  RegisterResponse,
  TokenResponse,
  UserRead,
} from "@/types/api";

export async function registerUser(
  payload: RegisterRequest
): Promise<RegisterResponse> {
  const { data } = await api.post<RegisterResponse>(
    "/api/v1/auth/register",
    payload
  );
  return data;
}

export async function loginUser(payload: LoginRequest): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/api/v1/auth/login", payload);
  return data;
}

export async function getCurrentUser(): Promise<UserRead> {
  const { data } = await api.get<UserRead>("/api/v1/auth/me");
  return data;
}
