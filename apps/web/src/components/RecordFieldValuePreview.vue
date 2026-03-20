<script setup lang="ts">
import { computed } from "vue";

import ChemicalStructurePreview from "./ChemicalStructurePreview.vue";
import type { TemplateField } from "../types/api";
import {
  buildSelectOptions,
  coerceChemicalEquationValue,
  coerceReactionProcessSteps,
  formatFieldValue,
} from "../utils/templateFields";
import { getChemicalEquationPreviewSource } from "../utils/templateRuntime";

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
const equationPreviewSource = computed(() => getChemicalEquationPreviewSource(props.value));
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
    <ChemicalStructurePreview v-if="equationPreviewSource" :structure="equationPreviewSource" />
    <div v-if="equationValue.plain_text" class="preview-item">
      <strong>内容：</strong>
      <pre class="preview-pre">{{ equationValue.plain_text }}</pre>
    </div>
    <div v-if="equationValue.smiles" class="preview-item">
      <strong>SMILES：</strong>
      <span>{{ equationValue.smiles }}</span>
    </div>
    <span v-if="!equationPreviewSource && !equationValue.plain_text && !equationValue.smiles">无</span>
  </div>

  <div v-else-if="field.field_type === 'reaction_process'" class="preview-stack">
    <span v-if="reactionSteps.length === 0">无</span>
    <div v-for="(step, index) in reactionSteps" :key="`${field.id}-${index}`" class="preview-card">
      <div class="preview-title">步骤 {{ index + 1 }}{{ step.title ? `：${step.title}` : "" }}</div>
      <div v-if="step.operation" class="preview-item">
        <strong>操作：</strong>
        <span>{{ step.operation }}</span>
      </div>
      <div v-if="step.reagent" class="preview-item">
        <strong>试剂：</strong>
        <span>{{ step.reagent }}</span>
      </div>
      <div v-if="step.condition" class="preview-item">
        <strong>条件：</strong>
        <span>{{ step.condition }}</span>
      </div>
      <div v-if="step.observation" class="preview-item">
        <strong>现象：</strong>
        <span>{{ step.observation }}</span>
      </div>
      <div v-if="step.note" class="preview-item">
        <strong>备注：</strong>
        <span>{{ step.note }}</span>
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
