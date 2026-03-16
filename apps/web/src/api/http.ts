import axios from "axios";
import { clearStoredAuth, getStoredToken } from "../utils/auth-storage";

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
  timeout: 10000,
});

http.interceptors.request.use((config) => {
  const token = getStoredToken();

  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

http.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error?.response?.status;

    if (status === 401) {
      clearStoredAuth();

      if (typeof window !== "undefined") {
        const currentPath = `${window.location.pathname}${window.location.search}`;
        const isOnLoginPage = window.location.pathname === "/login";

        if (!isOnLoginPage) {
          const redirect = encodeURIComponent(currentPath || "/projects");
          window.location.assign(`/login?redirect=${redirect}`);
        }
      }
    }

    return Promise.reject(error);
  },
);
