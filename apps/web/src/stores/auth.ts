import { computed, ref } from "vue";
import { defineStore } from "pinia";
import { fetchCurrentUser, login as loginRequest } from "../api/auth";
import type { AuthUser, LoginPayload } from "../types/api";
import {
  clearStoredAuth,
  getStoredToken,
  getStoredUser,
  setStoredAuth,
  setStoredUser,
} from "../utils/auth-storage";

export const useAuthStore = defineStore("auth", () => {
  const token = ref<string>(getStoredToken());
  const currentUser = ref<AuthUser | null>(getStoredUser());
  const ready = ref(false);
  const loading = ref(false);

  const isAuthenticated = computed(() => Boolean(token.value));
  const displayName = computed(() => {
    if (!currentUser.value) return "";
    return currentUser.value.full_name || currentUser.value.username || currentUser.value.email || "当前用户";
  });
  const isAdmin = computed(() => currentUser.value?.role === "admin");

  function applySession(nextToken: string, nextUser: AuthUser | null) {
    token.value = nextToken;
    currentUser.value = nextUser;
    setStoredAuth(nextToken, nextUser);
  }

  function clearSession() {
    token.value = "";
    currentUser.value = null;
    clearStoredAuth();
  }

  async function restoreSession() {
    if (ready.value) {
      return;
    }

    token.value = getStoredToken();
    currentUser.value = getStoredUser();

    if (!token.value) {
      ready.value = true;
      return;
    }

    try {
      const me = await fetchCurrentUser();
      currentUser.value = me;
      setStoredUser(me);
    } catch {
      clearSession();
    } finally {
      ready.value = true;
    }
  }

  async function login(payload: LoginPayload) {
    loading.value = true;

    try {
      const response = await loginRequest(payload);
      applySession(response.access_token, response.user);

      if (!response.user) {
        const me = await fetchCurrentUser();
        currentUser.value = me;
        setStoredUser(me);
      }

      ready.value = true;
    } finally {
      loading.value = false;
    }
  }

  function logout() {
    clearSession();
    ready.value = true;
  }

  return {
    token,
    currentUser,
    ready,
    loading,
    isAuthenticated,
    displayName,
    isAdmin,
    restoreSession,
    login,
    logout,
    clearSession,
  };
});
