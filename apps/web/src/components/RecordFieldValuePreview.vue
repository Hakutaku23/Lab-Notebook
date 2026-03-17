<script setup lang="ts">
import { computed } from "vue";

import type { TemplateField } from "../types/api";
import {
  buildSelectOptions,
  coerceChemicalEquationValue,
  coerceReactionProcessSteps,
  formatFieldValue,
} from "../utils/templateFields";

const props = defineProps<{
  field: TemplateField;
  value: unknown;
}>();

const selectLabel = computed(() => {
  const options = buildSelectOptions(props.field.options);
  const matched = options.find((item) => item.value === String(props.value ?? ""));
  return matched?.label ?? formatFieldValue(props.field, props.value);
});

const equationValue = computed(() => coerceChemicalEquationValue(props.value));
const reactionSteps = computed(() => coerceReactionProcessSteps(props.value));

const isStructuredValue = computed(
  () => typeof props.value === "object" && props.value !== null,
);

function formattedValue() {
  return formatFieldValue(props.field, props.value);
}
</script>

<template>
  <div v-if="field.field_type === 'chemical_equation'" class="preview-stack">
    <div v-if="equationValue.equation" class="preview-item">
      <strong>方程式：</strong>
      <pre class="preview-pre">{{ equationValue.equation }}</pre>
    </div>
    <div v-if="equationValue.conditions" class="preview-item">
      <strong>条件：</strong>
      <span>{{ equationValue.conditions }}</span>
    </div>
    <div v-if="equationValue.notes" class="preview-item">
      <strong>备注：</strong>
      <span>{{ equationValue.notes }}</span>
    </div>
    <span v-if="!equationValue.equation && !equationValue.conditions && !equationValue.notes">无</span>
  </div>

  <div v-else-if="field.field_type === 'reaction_process'" class="preview-stack">
    <span v-if="reactionSteps.length === 0">无</span>
    <div v-for="(step, index) in reactionSteps" :key="`${field.id}-${index}`" class="preview-card">
      <div class="preview-title">步骤 {{ index + 1 }}{{ step.title ? `：${step.title}` : "" }}</div>
      <div v-if="step.description" class="preview-item">
        <strong>描述：</strong>
        <span>{{ step.description }}</span>
      </div>
      <div v-if="step.conditions" class="preview-item">
        <strong>条件：</strong>
        <span>{{ step.conditions }}</span>
      </div>
      <div v-if="step.observation" class="preview-item">
        <strong>现象：</strong>
        <span>{{ step.observation }}</span>
      </div>
    </div>
  </div>

  <span v-else-if="field.field_type === 'checkbox'">{{ formattedValue() }}</span>
  <span v-else-if="field.field_type === 'select'">{{ selectLabel }}</span>
  <pre v-else-if="isStructuredValue" class="preview-pre">{{ formattedValue() }}</pre>
  <pre v-else class="preview-pre">{{ formattedValue() }}</pre>
</template>

<style scoped>
.preview-stack {
  display: grid;
  gap: 10px;
}

.preview-card {
  border: 1px solid #d7dbe7;
  border-radius: 12px;
  padding: 12px;
  background: #fafbfe;
  display: grid;
  gap: 8px;
}

.preview-title {
  font-weight: 600;
}

.preview-item {
  display: grid;
  gap: 4px;
}

.preview-pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
}
</style>
