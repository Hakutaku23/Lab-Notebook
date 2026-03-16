import type { AuthUser } from "../types/api";

const ACCESS_TOKEN_KEY = "lab-notebook.access-token";
const USER_KEY = "lab-notebook.current-user";

function canUseStorage() {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

export function getStoredToken(): string {
  if (!canUseStorage()) return "";
  return window.localStorage.getItem(ACCESS_TOKEN_KEY) ?? "";
}

export function setStoredToken(token: string) {
  if (!canUseStorage()) return;
  window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function removeStoredToken() {
  if (!canUseStorage()) return;
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
}

export function getStoredUser(): AuthUser | null {
  if (!canUseStorage()) return null;

  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) return null;

  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    window.localStorage.removeItem(USER_KEY);
    return null;
  }
}

export function setStoredUser(user: AuthUser | null) {
  if (!canUseStorage()) return;

  if (!user) {
    window.localStorage.removeItem(USER_KEY);
    return;
  }

  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function setStoredAuth(token: string, user: AuthUser | null) {
  setStoredToken(token);
  setStoredUser(user);
}

export function clearStoredAuth() {
  removeStoredToken();
  setStoredUser(null);
}