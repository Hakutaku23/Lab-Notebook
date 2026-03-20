<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { generateLLMContent } from "../api/llm";
import { useAIStore } from "../stores/ai";

const props = withDefaults(
  defineProps<{
    title?: string;
    description?: string;
    task?: string;
    context?: Record<string, unknown>;
    placeholder?: string;
    submitText?: string;
    initialPrompt?: string;
    resultLabel?: string;
  }>(),
  {
    title: "AI 助手",
    description: "输入问题后，AI 会结合当前页面上下文给出建议。",
    task: "assistant",
    context: () => ({}),
    placeholder: "例如：请帮我检查当前模板是否适合有机合成实验，并给出补充字段建议。",
    submitText: "发送给 AI",
    initialPrompt: "",
    resultLabel: "AI 回复",
  },
);

const emit = defineEmits<{
  generated: [content: string];
}>();

const aiStore = useAIStore();

const prompt = ref(props.initialPrompt);
const loading = ref(false);
const error = ref("");
const resultText = ref("");

const isConfigured = computed(() => {
  if (aiStore.config.mode === "api_key") {
    return aiStore.hasApiKeyConfig;
  }
  return aiStore.activeStatus?.configured ?? true;
});

watch(
  () => props.initialPrompt,
  (value) => {
    prompt.value = value;
  },
);

async function sendPrompt() {
  if (!prompt.value.trim()) {
    error.value = "请先输入你想让 AI 处理的内容。";
    return;
  }

  loading.value = true;
  error.value = "";

  try {
    const result = await generateLLMContent({
      task: props.task,
      prompt: prompt.value.trim(),
      context: props.context,
      config: aiStore.getRuntimeConfig(),
    });
    resultText.value = result.content.trim();
    emit("generated", resultText.value);
  } catch (err: any) {
    console.error(err);
    error.value = err?.response?.data?.detail || err?.message || "AI 生成失败，请检查模型配置。";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section class="card stack">
    <div class="section-header">
      <div>
        <h3>{{ title }}</h3>
        <p class="muted">{{ description }}</p>
      </div>
      <span class="badge">{{ aiStore.config.mode === "api_key" ? "API key" : "本地模型" }}</span>
    </div>

    <div class="form-item">
      <label class="label">提问内容</label>
      <textarea v-model="prompt" class="textarea" rows="5" :placeholder="placeholder" />
    </div>

    <div class="actions">
      <button class="button" type="button" :disabled="loading || !isConfigured" @click="sendPrompt">
        {{ loading ? "生成中..." : submitText }}
      </button>
    </div>

    <p v-if="!isConfigured" class="muted">当前模式尚未配置完成，请先在上方填写模型地址与模型名称。</p>
    <p v-if="error" class="error-text">{{ error }}</p>

    <div v-if="resultText" class="form-item">
      <label class="label">{{ resultLabel }}</label>
      <textarea class="textarea ai-result-area" :value="resultText" rows="8" readonly />
    </div>
  </section>
</template>
