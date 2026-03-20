<script setup lang="ts">
import { computed, onMounted } from "vue";

import { useAIStore } from "../stores/ai";

withDefaults(
  defineProps<{
    title?: string;
    description?: string;
  }>(),
  {
    title: "AI 设置",
    description: "默认优先使用本地模型；如需外部服务，可切换到 API key 模式并在当前浏览器中保存配置。",
  },
);

const aiStore = useAIStore();

const statusText = computed(() => {
  if (aiStore.error) {
    return aiStore.error;
  }
  return aiStore.activeStatus?.message || "尚未检测当前 AI 配置。";
});

async function checkCurrentConfig() {
  try {
    await aiStore.validateCurrentConfig();
  } catch (error) {
    console.error(error);
  }
}

onMounted(() => {
  if (!aiStore.defaultStatus) {
    void aiStore.refreshDefaultStatus();
  }
});
</script>

<template>
  <section class="card stack">
    <div class="section-header">
      <div>
        <h3>{{ title }}</h3>
        <p class="muted">{{ description }}</p>
      </div>
      <span class="badge">
        {{ aiStore.config.mode === "api_key" ? "API key 模式" : "本地模型模式" }}
      </span>
    </div>

    <div class="grid-2">
      <div class="form-item">
        <label class="label">模型来源</label>
        <select v-model="aiStore.config.mode" class="input">
          <option value="local">本地模型（默认）</option>
          <option value="api_key">API key</option>
        </select>
      </div>

      <div class="form-item">
        <label class="label">模型名称</label>
        <input
          v-model="aiStore.config.model"
          class="input"
          type="text"
          :placeholder="aiStore.config.mode === 'api_key' ? '例如：gpt-4o-mini' : '例如：qwen2.5:14b-instruct'"
        />
      </div>
    </div>

    <div class="form-item">
      <label class="label">模型服务地址</label>
      <input
        v-model="aiStore.config.base_url"
        class="input"
        type="text"
        :placeholder="aiStore.config.mode === 'api_key' ? '例如：https://api.openai.com/v1' : '例如：http://127.0.0.1:11434/v1'"
      />
    </div>

    <div v-if="aiStore.config.mode === 'api_key'" class="form-item">
      <label class="label">API key</label>
      <input
        v-model="aiStore.config.api_key"
        class="input"
        type="password"
        placeholder="在这里填写你自己的 API key"
      />
    </div>

    <div class="status-display">
      <strong>当前状态</strong>
      <p class="muted">{{ statusText }}</p>
      <p class="muted">提示：这套设置仅保存在当前浏览器中，切换设备后需要重新填写。</p>
      <p v-if="aiStore.config.mode === 'local'" class="muted">
        测试环境暂时没有可用的本地模型设备时，可以先保留为空，待后续在支持设备上再验证。
      </p>
    </div>

    <div class="actions">
      <button
        class="button secondary"
        type="button"
        :disabled="aiStore.loadingDefaultStatus || aiStore.checkingConfig"
        @click="checkCurrentConfig"
      >
        {{ aiStore.loadingDefaultStatus || aiStore.checkingConfig ? "检测中..." : "检测当前配置" }}
      </button>
    </div>
  </section>
</template>
