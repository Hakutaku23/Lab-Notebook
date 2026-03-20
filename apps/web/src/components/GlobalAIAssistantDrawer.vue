<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { generateLLMContent } from "../api/llm";
import { useAIStore } from "../stores/ai";

const aiStore = useAIStore();

const prompt = ref("");
const resultText = ref("");
const error = ref("");
const loading = ref(false);

const visible = computed(() => aiStore.assistantOpen);
const statusText = computed(() => aiStore.activeStatus?.message || aiStore.error || "尚未检测当前 AI 配置。");
const isConfigured = computed(() => {
  if (aiStore.config.mode === "api_key") {
    return aiStore.hasApiKeyConfig;
  }
  return aiStore.activeStatus?.configured ?? true;
});

watch(
  () => aiStore.assistantOpen,
  (open) => {
    if (open) {
      prompt.value = aiStore.assistantPrompt || "";
      error.value = "";
    }
  },
);

async function submitPrompt() {
  if (!prompt.value.trim()) {
    error.value = "请先输入你想让 AI 处理的问题。";
    return;
  }

  loading.value = true;
  error.value = "";

  try {
    const result = await generateLLMContent({
      task: aiStore.assistantState.task,
      prompt: prompt.value.trim(),
      context: aiStore.assistantState.context,
      config: aiStore.getRuntimeConfig(),
    });
    resultText.value = result.content.trim();
  } catch (err: any) {
    console.error(err);
    error.value = err?.response?.data?.detail || err?.message || "AI 对话失败，请检查配置。";
  } finally {
    loading.value = false;
  }
}

function closeDrawer() {
  aiStore.closeAssistant();
}
</script>

<template>
  <teleport to="body">
    <div v-if="visible" class="ai-drawer-backdrop" @click="closeDrawer" />
    <aside v-if="visible" class="ai-drawer" aria-label="AI 助手面板">
      <div class="ai-drawer__header">
        <div>
          <p class="eyebrow">AI 助手</p>
          <h3>{{ aiStore.assistantState.title }}</h3>
          <p class="muted">{{ aiStore.assistantState.description }}</p>
        </div>
        <button class="button secondary" type="button" @click="closeDrawer">关闭</button>
      </div>

      <div class="ai-drawer__body">
        <div class="status-display">
          <strong>当前模型</strong>
          <p class="muted">
            {{ aiStore.config.mode === "api_key" ? "API key 模式" : "本地模型模式" }}
          </p>
          <p class="muted">{{ statusText }}</p>
        </div>

        <div class="form-item">
          <label class="label">对话内容</label>
          <textarea
            v-model="prompt"
            class="textarea"
            rows="8"
            :placeholder="aiStore.assistantState.placeholder"
          />
        </div>

        <div class="actions">
          <button class="button" type="button" :disabled="loading || !isConfigured" @click="submitPrompt">
            {{ loading ? "生成中..." : "发送给 AI" }}
          </button>
        </div>

        <p v-if="!isConfigured" class="muted">当前 AI 尚未配置完成，请先到用户设置中完成模型配置。</p>
        <p v-if="error" class="error-text">{{ error }}</p>

        <div v-if="resultText" class="form-item">
          <label class="label">AI 回复</label>
          <textarea class="textarea ai-result-area" :value="resultText" rows="14" readonly />
        </div>
      </div>
    </aside>
  </teleport>
</template>
