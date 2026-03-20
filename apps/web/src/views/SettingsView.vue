<script setup lang="ts">
import { onMounted } from "vue";

import AISettingsPanel from "../components/AISettingsPanel.vue";
import { useAIStore } from "../stores/ai";

const aiStore = useAIStore();

onMounted(() => {
  void aiStore.refreshDefaultStatus();
});
</script>

<template>
  <div class="page">
    <section class="page-hero">
      <div>
        <p class="eyebrow">用户设置</p>
        <h2>个人设置与 AI 配置</h2>
        <p class="muted">在这里统一管理 AI 模型来源、API key 和连通性检测，不再打断业务页面。</p>
      </div>
    </section>

    <AISettingsPanel
      title="AI 模型设置"
      description="默认优先使用本地模型；当你切换到 API key 模式时，需要在此页面手动填写模型服务地址、模型名称和 API key。"
    />
  </div>
</template>
