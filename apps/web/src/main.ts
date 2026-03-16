import { createApp } from "vue";
import App from "./App.vue";
import { router } from "./router";
import { pinia } from "./stores";
import { useAuthStore } from "./stores/auth";
import "./style.css";

async function bootstrap() {
  const app = createApp(App);

  app.use(pinia);

  const authStore = useAuthStore(pinia);
  await authStore.restoreSession();

  app.use(router);
  await router.isReady();

  app.mount("#app");
}

bootstrap();