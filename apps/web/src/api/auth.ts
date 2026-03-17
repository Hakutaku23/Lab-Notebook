import type {
  AuthUser,
  LoginPayload,
  LoginResponse,
  RegisterPayload,
} from "../types/api";
import { http } from "./http";

function normalizeAuthUser(payload: any): AuthUser | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }

  return {
    id: String(payload.id ?? ""),
    username: String(payload.username ?? payload.email ?? ""),
    email: payload.email ?? null,
    full_name: payload.full_name ?? payload.fullName ?? null,
    role: payload.role ?? null,
    is_active: payload.is_active ?? payload.isActive ?? true,
  };
}

function normalizeLoginResponse(payload: any): LoginResponse {
  const accessToken = payload?.access_token ?? payload?.accessToken ?? payload?.token ?? "";

  if (!accessToken) {
    throw new Error("登录响应中缺少 access token。");
  }

  return {
    access_token: String(accessToken),
    token_type: String(payload?.token_type ?? payload?.tokenType ?? "bearer"),
    expires_in:
      typeof payload?.expires_in === "number"
        ? payload.expires_in
        : typeof payload?.expiresIn === "number"
          ? payload.expiresIn
          : null,
    user: normalizeAuthUser(payload?.user ?? payload?.current_user ?? payload?.profile ?? null),
  };
}

export async function login(payload: LoginPayload): Promise<LoginResponse> {
  try {
    const { data } = await http.post("/auth/login", payload);
    return normalizeLoginResponse(data);
  } catch (error: any) {
    const status = error?.response?.status;

    if (status !== 415 && status !== 422) {
      throw error;
    }
  }

  const formData = new URLSearchParams();
  formData.set("username", payload.username);
  formData.set("password", payload.password);

  const { data } = await http.post("/auth/login", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  return normalizeLoginResponse(data);
}

export async function register(payload: RegisterPayload): Promise<LoginResponse> {
  const { data } = await http.post("/auth/register", payload);
  return normalizeLoginResponse(data);
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  const { data } = await http.get("/auth/me");
  const user = normalizeAuthUser(data);

  if (!user) {
    throw new Error("当前用户信息解析失败。");
  }

  return user;
}
