<script setup lang="ts">
import { computed, ref } from "vue";

import { generateLLMContent } from "../api/llm";
import { useAIStore } from "../stores/ai";

const props = withDefaults(
  defineProps<{
    summary: string;
    context: Record<string, unknown>;
    editable?: boolean;
  }>(),
  {
    editable: true,
  },
);

const emit = defineEmits<{
  "update:summary": [value: string];
}>();

const aiStore = useAIStore();

const instruction = ref("");
const resultText = ref("");
const loading = ref(false);
const error = ref("");
const successText = ref("");

const isConfigured = computed(() => {
  if (aiStore.config.mode === "api_key") {
    return aiStore.hasApiKeyConfig;
  }
  return aiStore.activeStatus?.configured ?? true;
});

async function runTask(task: "record_summary" | "record_polish") {
  if (task === "record_polish" && !props.summary.trim()) {
    error.value = "当前还没有摘要内容，无法直接润色。";
    return;
  }

  loading.value = true;
  error.value = "";
  successText.value = "";

  try {
    const prompt =
      task === "record_summary"
        ? instruction.value.trim() || "请根据当前实验记录内容，生成一段适合直接保存的中文摘要。"
        : instruction.value.trim() || "请润色当前实验摘要，保持事实不变，语言更准确清晰。";

    const result = await generateLLMContent({
      task,
      prompt,
      context: {
        ...props.context,
        current_summary: props.summary,
      },
      config: aiStore.getRuntimeConfig(),
    });

    resultText.value = result.content.trim();
    successText.value = props.editable
      ? task === "record_summary"
        ? "AI 已生成摘要建议，可选择覆盖或追加到当前摘要。"
        : "AI 已生成润色建议，可选择覆盖或追加到当前摘要。"
      : task === "record_summary"
        ? "AI 已生成摘要建议。"
        : "AI 已生成润色建议。";
  } catch (err: any) {
    console.error(err);
    error.value = err?.response?.data?.detail || err?.message || "AI 摘要处理失败，请检查模型配置。";
  } finally {
    loading.value = false;
  }
}
function replaceSummary() {
  if (!props.editable || !resultText.value) return;
  emit("update:summary", resultText.value);
  successText.value = "AI 结果已覆盖当前摘要。";
}

function appendSummary() {
  if (!props.editable || !resultText.value) return;
  const nextValue = props.summary.trim()
    ? `${props.summary.trim()}

${resultText.value}`
    : resultText.value;
  emit("update:summary", nextValue);
  successText.value = "AI 结果已追加到当前摘要。";
}
</script>

<template>
  <section class="card stack">
    <div class="section-header">
      <div>
        <h3>AI 摘要助手</h3>
        <p class="muted">支持根据当前记录内容自动生成摘要，或对已有摘要进行润色。</p>
      </div>
      <span class="badge">{{ aiStore.config.mode === "api_key" ? "API key" : "本地模型" }}</span>
    </div>

    <div class="form-item">
      <label class="label">补充要求</label>
      <textarea
        v-model="instruction"
        class="textarea"
        rows="4"
        placeholder="例如：强调实验结论、异常现象和后续待验证点。留空时会使用默认提示词。"
      />
    </div>

    <div class="actions">
      <button class="button" type="button" :disabled="loading || !isConfigured" @click="runTask('record_summary')">
        {{ loading ? "处理中..." : "AI 生成摘要" }}
      </button>
      <button class="button secondary" type="button" :disabled="loading || !isConfigured" @click="runTask('record_polish')">
        AI 润色摘要
      </button>
    </div>

    <p v-if="!isConfigured" class="muted">当前模式尚未配置完成，请先在 AI 设置中补齐模型信息。</p>
    <p v-if="successText" class="muted">{{ successText }}</p>
    <p v-if="error" class="error-text">{{ error }}</p>

    <div v-if="resultText" class="form-item">
      <label class="label">{{ editable ? "最近一次 AI 结果" : "摘要建议" }}</label>
      <textarea class="textarea ai-result-area" :value="resultText" rows="7" readonly />
      <div v-if="editable" class="actions">
        <button class="button secondary" type="button" @click="replaceSummary">覆盖摘要</button>
        <button class="button secondary" type="button" @click="appendSummary">追加到摘要</button>
      </div>
    </div>
  </section>
</template>
