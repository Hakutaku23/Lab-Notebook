<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAuthStore } from "../stores/auth";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const mode = ref<"login" | "register">("login");
const errorMessage = ref("");

const loginForm = reactive({
  username: "",
  password: "",
});

const registerForm = reactive({
  username: "",
  email: "",
  full_name: "",
  password: "",
  confirm_password: "",
});

const submitText = computed(() => {
  if (authStore.loading) {
    return mode.value === "login" ? "登录中..." : "注册中...";
  }
  return mode.value === "login" ? "登录" : "注册并进入系统";
});

function switchMode(nextMode: "login" | "register") {
  mode.value = nextMode;
  errorMessage.value = "";
}

function resolveRedirect() {
  return typeof route.query.redirect === "string" && route.query.redirect
    ? route.query.redirect
    : "/projects";
}

async function handleSubmit() {
  errorMessage.value = "";

  try {
    if (mode.value === "login") {
      await authStore.login({
        username: loginForm.username.trim(),
        password: loginForm.password,
      });
    } else {
      if (registerForm.password !== registerForm.confirm_password) {
        errorMessage.value = "两次输入的密码不一致，请重新确认。";
        return;
      }

      await authStore.register({
        username: registerForm.username.trim(),
        email: registerForm.email.trim(),
        full_name: registerForm.full_name.trim() || null,
        password: registerForm.password,
      });
    }

    await router.replace(resolveRedirect());
  } catch (error: any) {
    errorMessage.value =
      error?.response?.data?.detail ||
      error?.message ||
      (mode.value === "login" ? "登录失败，请检查用户名和密码。" : "注册失败，请检查输入信息。");
  }
}
</script>

<template>
  <section class="login-page">
    <div class="auth-panel panel">
      <div class="stack-gap">
        <div>
          <p class="eyebrow">欢迎使用</p>
          <h2>{{ mode === "login" ? "登录实验记录系统" : "注册实验记录系统" }}</h2>
          <p class="muted">
            {{
              mode === "login"
                ? "登录后即可进入项目、模板与实验记录工作区。"
                : "注册完成后会自动登录，并进入项目工作台。"
            }}
          </p>
        </div>

        <div class="auth-switch" role="tablist" aria-label="认证方式切换">
          <button
            class="button"
            type="button"
            :class="{ secondary: mode !== 'login' }"
            @click="switchMode('login')"
          >
            登录
          </button>
          <button
            class="button"
            type="button"
            :class="{ secondary: mode !== 'register' }"
            @click="switchMode('register')"
          >
            注册
          </button>
        </div>
      </div>

      <form class="stack" @submit.prevent="handleSubmit">
        <template v-if="mode === 'login'">
          <label class="label">
            <span>用户名</span>
            <input
              v-model="loginForm.username"
              type="text"
              autocomplete="username"
              placeholder="请输入用户名"
              required
            />
          </label>

          <label class="label">
            <span>密码</span>
            <input
              v-model="loginForm.password"
              type="password"
              autocomplete="current-password"
              placeholder="请输入密码"
              required
            />
          </label>
        </template>

        <template v-else>
          <label class="label">
            <span>用户名</span>
            <input
              v-model="registerForm.username"
              type="text"
              autocomplete="username"
              placeholder="请输入用户名"
              required
            />
          </label>

          <label class="label">
            <span>邮箱</span>
            <input
              v-model="registerForm.email"
              type="email"
              autocomplete="email"
              placeholder="请输入邮箱地址"
              required
            />
          </label>

          <label class="label">
            <span>姓名或昵称</span>
            <input
              v-model="registerForm.full_name"
              type="text"
              autocomplete="name"
              placeholder="可选，用于页面展示"
            />
          </label>

          <label class="label">
            <span>密码</span>
            <input
              v-model="registerForm.password"
              type="password"
              autocomplete="new-password"
              placeholder="请设置至少 6 位密码"
              required
            />
          </label>

          <label class="label">
            <span>确认密码</span>
            <input
              v-model="registerForm.confirm_password"
              type="password"
              autocomplete="new-password"
              placeholder="请再次输入密码"
              required
            />
          </label>
        </template>

        <p v-if="errorMessage" class="error-text">
          {{ errorMessage }}
        </p>

        <button class="button" type="submit" :disabled="authStore.loading">
          {{ submitText }}
        </button>
      </form>
    </div>
  </section>
</template>
