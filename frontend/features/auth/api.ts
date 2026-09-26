import { apiFetch } from "@/lib/api-client";
import { setToken } from "@/lib/auth-token";
import type { RegisterFormValues, LoginFormValues } from "@/lib/schemas/auth";

interface TokenResponse { access_token: string; token_type: string; }
interface UserResponse { id: string; email: string; full_name: string; }

export async function registerUser(payload: RegisterFormValues): Promise<UserResponse> {
  return apiFetch<UserResponse>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function loginUser(payload: LoginFormValues): Promise<TokenResponse> {
  const res = await apiFetch<TokenResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  setToken(res.access_token);
  return res;
}