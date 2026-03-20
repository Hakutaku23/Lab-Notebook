<script setup lang="ts">
import { computed, ref } from "vue";

import { generateLLMContent } from "../api/llm";
import { useAIStore } from "../stores/ai";

const props = withDefaults(
  defineProps<{
    context: Record<string, unknown>;
    editable?: boolean;
  }>(),
  {
    editable: true,
  },
);

const aiStore = useAIStore();

const loading = ref(false);
const error = ref("");
const resultText = ref("");
const successText = ref("");
const customInstruction = ref("");

const isConfigured = computed(() => {
  if (aiStore.config.mode === "api_key") {
    return aiStore.hasApiKeyConfig;
  }
  return aiStore.activeStatus?.configured ?? true;
});

async function runQualityCheck(mode: "completeness" | "risk" | "consistency") {
  loading.value = true;
  error.value = "";
  successText.value = "";

  const defaultPromptMap = {
    completeness: "请从记录完整性角度检查当前实验记录，列出缺失信息、建议补充项，并按优先级排序。",
    risk: "请从实验风险和审核角度检查当前记录，指出需要进一步复核的异常、风险点和待确认事项。",
    consistency: "请检查当前记录标题、摘要与字段内容的一致性，指出可能冲突、含糊或单位不统一的地方。",
  } as const;

  try {
    const result = await generateLLMContent({
      task: "record_quality",
      prompt: customInstruction.value.trim() || defaultPromptMap[mode],
      context: {
        ...props.context,
        review_mode: mode,
        editable: props.editable,
      },
      config: aiStore.getRuntimeConfig(),
    });

    resultText.value = result.content.trim();
    successText.value = props.editable ? "AI 已生成当前记录的质检建议。" : "AI 已生成只读质检建议。";
  } catch (err: any) {
    console.error(err);
    error.value = err?.response?.data?.detail || err?.message || "记录质检失败，请检查模型配置。";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section class="card stack">
    <div class="section-header">
      <div>
        <h3>AI 记录质检</h3>
        <p class="muted">针对完整性、风险点与一致性进行审阅，适合在提交审核前做一次快速自检。</p>
      </div>
      <span class="badge">{{ editable ? "可编辑记录" : "只读记录" }}</span>
    </div>

    <div class="form-item">
      <label class="label">补充要求</label>
      <textarea
        v-model="customInstruction"
        class="textarea"
        rows="3"
        placeholder="例如：优先检查必填实验条件、异常现象、数量单位与安全说明。留空时使用内置质检提示。"
      />
    </div>

    <div class="actions actions-wrap">
      <button class="button" type="button" :disabled="loading || !isConfigured" @click="runQualityCheck('completeness')">
        {{ loading ? "检查中..." : "完整性检查" }}
      </button>
      <button class="button secondary" type="button" :disabled="loading || !isConfigured" @click="runQualityCheck('risk')">
        风险点检查
      </button>
      <button class="button secondary" type="button" :disabled="loading || !isConfigured" @click="runQualityCheck('consistency')">
        一致性检查
      </button>
    </div>

    <p v-if="!isConfigured" class="muted">当前模式尚未配置完成，请先在 AI 设置中补齐模型信息。</p>
    <p v-if="successText" class="muted">{{ successText }}</p>
    <p v-if="error" class="error-text">{{ error }}</p>

    <div v-if="resultText" class="form-item">
      <label class="label">质检结果</label>
      <textarea class="textarea ai-result-area" :value="resultText" rows="10" readonly />
    </div>
  </section>
</template>

<style scoped>
.actions-wrap {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
</style>
