<script setup lang="ts">
import { computed, onMounted, watch } from "vue";
import { RouterLink, RouterView, useRouter } from "vue-router";

import GlobalAIAssistantDrawer from "./components/GlobalAIAssistantDrawer.vue";
import { useAIStore } from "./stores/ai";
import { useAuthStore } from "./stores/auth";
import { getUserRoleLabel } from "./utils/user-role";

const router = useRouter();
const authStore = useAuthStore();
const aiStore = useAIStore();

const isAuthenticated = computed(() => authStore.isAuthenticated);
const sidebarLLMStatus = computed(() => aiStore.activeStatus || aiStore.defaultStatus);
const sidebarLLMMessage = computed(() => {
  if (aiStore.error) {
    return aiStore.error;
  }
  return sidebarLLMStatus.value?.message || "尚未读取 AI 服务状态。";
});

async function hydrateSidebar() {
  if (!authStore.token) {
    return;
  }
  await aiStore.refreshDefaultStatus();
}

async function signOut() {
  authStore.logout();
  aiStore.closeAssistant();
  await router.push({ name: "login" });
}

function openGlobalAssistant() {
  aiStore.openAssistant();
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
        <p class="eyebrow">实验工作台</p>
        <h1>实验记录系统</h1>
        <p class="muted">围绕项目、模板、记录、附件、审计流程与 AI 辅助能力组织实验协作。</p>
      </div>

      <nav class="nav-links">
        <RouterLink to="/projects">项目</RouterLink>
        <RouterLink to="/records">实验记录</RouterLink>
        <RouterLink to="/templates">模板</RouterLink>
        <RouterLink to="/settings">用户设置</RouterLink>
        <RouterLink v-if="authStore.isAdmin" to="/audit-logs">审计日志</RouterLink>
      </nav>

      <div class="sidebar-card sidebar-user-card">
        <div>
          <strong>{{ authStore.displayName }}</strong>
          <div class="muted">{{ getUserRoleLabel(authStore.currentUser?.role) }}</div>
          <div class="muted">{{ authStore.currentUser?.email || "未填写邮箱" }}</div>
        </div>
        <div class="actions sidebar-user-actions">
          <RouterLink class="button secondary" to="/settings">用户设置</RouterLink>
          <button class="button secondary sidebar-signout" type="button" @click="signOut">
            退出登录
          </button>
        </div>
      </div>

      <div class="sidebar-card">
        <strong>AI 服务</strong>
        <div>{{ sidebarLLMStatus?.provider || "local" }}</div>
        <div class="muted">
          {{ aiStore.config.mode === "api_key" ? "当前使用：API key 模式" : "当前使用：本地模型模式" }}
        </div>
        <div class="muted">{{ sidebarLLMMessage }}</div>
        <div class="actions sidebar-ai-actions">
          <RouterLink class="button secondary" to="/settings">配置 AI</RouterLink>
          <button class="button secondary" type="button" @click="openGlobalAssistant">打开 AI 助手</button>
        </div>
      </div>
    </aside>

    <main class="main-content">
      <div class="main-container">
        <RouterView />
      </div>
    </main>

    <button v-if="isAuthenticated" class="ai-fab" type="button" @click="openGlobalAssistant">
      AI 助手
    </button>

    <GlobalAIAssistantDrawer v-if="isAuthenticated" />
  </div>
</template>
