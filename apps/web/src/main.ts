import "./shims/browser-env";
import { createApp } from "vue";
import App from "./App.vue";
import { router } from "./router";
import { pinia } from "./stores";
import { useAuthStore } from "./stores/auth";
import "./style.css";

function bootstrap() {
  const app = createApp(App);

  app.use(pinia);
  app.use(router);
  app.mount("#app");

  const authStore = useAuthStore(pinia);
  void authStore.restoreSession();
}

bootstrap();
