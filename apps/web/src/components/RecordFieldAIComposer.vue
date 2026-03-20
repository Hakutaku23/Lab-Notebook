<script setup lang="ts">
import { computed, ref } from "vue";

import { generateLLMContent } from "../api/llm";
import { useAIStore } from "../stores/ai";
import type { TemplateField } from "../types/api";

const props = defineProps<{
  field: TemplateField;
  fieldValue: unknown;
  context: Record<string, unknown>;
  disabled?: boolean;
}>();

const emit = defineEmits<{
  apply: [value: unknown];
}>();

const aiStore = useAIStore();

const expanded = ref(false);
const instruction = ref("");
const resultText = ref("");
const error = ref("");
const successText = ref("");
const loading = ref(false);

const isConfigured = computed(() => {
  if (aiStore.config.mode === "api_key") {
    return aiStore.hasApiKeyConfig;
  }
  return aiStore.activeStatus?.configured ?? true;
});

const displayValue = computed(() => {
  if (typeof props.fieldValue === "string") {
    return props.fieldValue;
  }
  if (props.fieldValue === null || props.fieldValue === undefined) {
    return "";
  }
  try {
    return JSON.stringify(props.fieldValue, null, 2);
  } catch {
    return String(props.fieldValue);
  }
});

function normalizeGeneratedValue(value: string): unknown {
  const trimmed = value.trim();
  if (!trimmed) {
    return "";
  }

  if (["json", "table", "file"].includes(props.field.field_type)) {
    return JSON.parse(trimmed);
  }

  if (props.field.field_type === "checkbox") {
    return ["true", "1", "yes", "是"].includes(trimmed.toLowerCase());
  }

  return trimmed;
}

async function generateSuggestion() {
  loading.value = true;
  error.value = "";
  successText.value = "";

  try {
    const result = await generateLLMContent({
      task: "record_field",
      prompt:
        instruction.value.trim() ||
        `请为字段“${props.field.label}”生成可直接填写的建议内容，并确保结果适合当前字段类型。`,
      context: props.context,
      config: aiStore.getRuntimeConfig(),
    });

    resultText.value = result.content.trim();
    successText.value = "AI 已生成字段建议，可选择覆盖当前字段内容。";
  } catch (err: any) {
    console.error(err);
    error.value = err?.response?.data?.detail || err?.message || "字段 AI 生成失败，请检查模型配置。";
  } finally {
    loading.value = false;
  }
}

function applyResult() {
  try {
    emit("apply", normalizeGeneratedValue(resultText.value));
    successText.value = "AI 建议已写回当前字段。";
  } catch (err: any) {
    console.error(err);
    error.value = err?.message || "AI 结果无法写回当前字段，请检查返回格式。";
  }
}
</script>

<template>
  <div class="field-ai-composer" :class="{ 'field-ai-composer--disabled': disabled }">
    <div class="actions field-ai-composer__toolbar">
      <button class="button secondary field-ai-composer__toggle" type="button" :disabled="disabled" @click="expanded = !expanded">
        {{ expanded ? "收起字段 AI" : "字段 AI 辅助" }}
      </button>
      <span class="muted field-ai-composer__value-tip">当前值：{{ displayValue || "空" }}</span>
    </div>

    <div v-if="expanded" class="field-ai-composer__panel">
      <div class="form-item">
        <label class="label">字段生成要求</label>
        <textarea
          v-model="instruction"
          class="textarea"
          rows="3"
          :placeholder="`例如：请帮我补全 ${field.label}，强调实验事实、数量单位与异常说明。`"
          :disabled="disabled"
        />
      </div>

      <div class="actions">
        <button class="button" type="button" :disabled="loading || disabled || !isConfigured" @click="generateSuggestion">
          {{ loading ? "生成中..." : "生成字段建议" }}
        </button>
        <button class="button secondary" type="button" :disabled="!resultText || disabled" @click="applyResult">
          写回字段
        </button>
      </div>

      <p v-if="!isConfigured" class="muted">当前模式尚未配置完成，请先在 AI 设置中补齐模型信息。</p>
      <p v-if="successText" class="muted">{{ successText }}</p>
      <p v-if="error" class="error-text">{{ error }}</p>

      <div v-if="resultText" class="form-item">
        <label class="label">字段 AI 建议</label>
        <textarea class="textarea ai-result-area" :value="resultText" rows="6" readonly />
      </div>
    </div>
  </div>
</template>

<style scoped>
.field-ai-composer {
  display: grid;
  gap: 10px;
}

.field-ai-composer--disabled {
  opacity: 0.72;
}

.field-ai-composer__toolbar {
  justify-content: space-between;
  align-items: center;
}

.field-ai-composer__toggle {
  white-space: nowrap;
}

.field-ai-composer__value-tip {
  font-size: 0.86rem;
}

.field-ai-composer__panel {
  display: grid;
  gap: 12px;
  padding: 14px;
  border: 1px dashed var(--border);
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.02);
}
</style>
