<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink, RouterView, useRouter } from "vue-router";

import { fetchLLMStatus } from "./api/llm";
import { useAuthStore } from "./stores/auth";
import type { LLMStatus } from "./types/api";

const router = useRouter();
const authStore = useAuthStore();

const llmStatus = ref<LLMStatus | null>(null);
const llmError = ref("");

const isAuthenticated = computed(() => authStore.isAuthenticated);

async function hydrateSidebar() {
  if (!authStore.token) {
    llmStatus.value = null;
    llmError.value = "";
    return;
  }

  try {
    llmStatus.value = await fetchLLMStatus();
    llmError.value = "";
  } catch (error) {
    console.error(error);
    llmStatus.value = null;
    llmError.value = "LLM 状态读取失败，请检查后端配置。";
  }
}

async function signOut() {
  authStore.logout();
  llmStatus.value = null;
  llmError.value = "";
  await router.push({ name: "login" });
}

watch(
  () => authStore.token,
  () => {
    void hydrateSidebar();
  },
);

onMounted(() => {
  void hydrateSidebar();
});
</script>

<template>
  <div class="shell" :class="{ 'shell--guest': !isAuthenticated }">
    <aside v-if="isAuthenticated" class="sidebar">
      <div class="sidebar-brand">
        <p class="eyebrow">Laboratory Workspace</p>
        <h1>Lab Notebook</h1>
        <p class="muted">面向实验项目、模板和记录协作的工作台。</p>
      </div>

      <nav class="nav-links">
        <RouterLink to="/projects">项目</RouterLink>
        <RouterLink to="/records">实验记录</RouterLink>
        <RouterLink to="/templates">模板</RouterLink>
        <RouterLink v-if="authStore.isAdmin" to="/audit-logs">审计日志</RouterLink>
      </nav>

      <div class="sidebar-card">
        <strong>{{ authStore.displayName }}</strong>
        <div class="muted">{{ authStore.currentUser?.role || "member" }}</div>
        <button class="button secondary sidebar-signout" type="button" @click="signOut">
          退出登录
        </button>
      </div>

      <div class="sidebar-card" v-if="llmStatus">
        <strong>LLM 服务</strong>
        <div>{{ llmStatus.provider }}</div>
        <div class="muted">{{ llmStatus.message }}</div>
      </div>

      <div class="sidebar-card" v-else-if="llmError">
        <strong>LLM 服务</strong>
        <div class="muted">{{ llmError }}</div>
      </div>
    </aside>

    <main class="main-content">
      <div class="main-container">
        <RouterView />
      </div>
    </main>
  </div>
</template>
