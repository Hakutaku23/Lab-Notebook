<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const form = reactive({
  username: "",
  password: "",
});

const errorMessage = ref("");

async function handleSubmit() {
  errorMessage.value = "";

  try {
    await authStore.login({
      username: form.username.trim(),
      password: form.password,
    });

    const redirect =
      typeof route.query.redirect === "string" && route.query.redirect
        ? route.query.redirect
        : "/projects";

    await router.replace(redirect);
  } catch (error: any) {
    errorMessage.value =
      error?.response?.data?.detail ||
      error?.message ||
      "登录失败，请检查用户名和密码。";
  }
}
</script>

<template>
  <section class="login-page">
    <div class="auth-panel panel">
      <div>
        <p class="eyebrow">Welcome Back</p>
        <h2>登录 Lab Notebook</h2>
        <p class="muted">登录后即可进入项目、模板与实验记录工作区。</p>
      </div>

      <form class="stack" @submit.prevent="handleSubmit">
        <label class="label">
          <span>用户名</span>
          <input
            v-model="form.username"
            type="text"
            autocomplete="username"
            placeholder="请输入用户名"
            required
          />
        </label>

        <label class="label">
          <span>密码</span>
          <input
            v-model="form.password"
            type="password"
            autocomplete="current-password"
            placeholder="请输入密码"
            required
          />
        </label>

        <p v-if="errorMessage" class="error-text">
          {{ errorMessage }}
        </p>

        <button class="button" type="submit" :disabled="authStore.loading">
          {{ authStore.loading ? "登录中..." : "登录" }}
        </button>
      </form>
    </div>
  </section>
</template>
