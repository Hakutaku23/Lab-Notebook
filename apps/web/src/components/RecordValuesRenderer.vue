<script setup lang="ts">
import { computed } from "vue";

import type { ExperimentTemplateDetail, RecordFieldValueItem, TemplateField } from "../types/api";
import type { ChemicalEquationValue, ReactionProcessStep } from "../utils/templateFieldRuntime";

const props = defineProps<{
  template: ExperimentTemplateDetail;
  values: RecordFieldValueItem[];
}>();

const valueMap = computed<Record<string, RecordFieldValueItem>>(() => {
  const map: Record<string, RecordFieldValueItem> = {};
  props.values.forEach((item) => {
    map[item.field_id] = item;
  });
  return map;
});

function rawValue(field: TemplateField): unknown {
  return valueMap.value[field.id]?.value_json;
}

function formatDefault(value: unknown): string {
  if (value === null || value === undefined || value === "") return "无";
  if (typeof value === "string") return value;
  if (typeof value === "boolean") return value ? "是" : "否";
  return JSON.stringify(value, null, 2);
}

function equationText(field: TemplateField): string {
  const value = rawValue(field);
  if (typeof value === "string") return value;
  if (!value || typeof value !== "object" || Array.isArray(value)) return "无";
  const equation = value as ChemicalEquationValue;
  return (
    equation.equation_text ||
    `${(equation.reactants ?? []).join(" + ")} ${equation.arrow ?? "→"} ${(equation.products ?? []).join(" + ")}`.trim() ||
    "无"
  );
}

function equationConditions(field: TemplateField): string {
  const value = rawValue(field);
  if (!value || typeof value !== "object" || Array.isArray(value)) return "";
  return String((value as ChemicalEquationValue).conditions ?? "").trim();
}

function processSteps(field: TemplateField): ReactionProcessStep[] {
  const value = rawValue(field);
  return Array.isArray(value) ? (value as ReactionProcessStep[]) : [];
}
</script>

<template>
  <div class="record-values-renderer">
    <section v-for="section in template.sections" :key="section.id" class="card">
      <h3>{{ section.title }}</h3>
      <p v-if="section.description" class="muted">{{ section.description }}</p>

      <div v-for="field in section.fields" :key="field.id" class="detail-item">
        <div class="detail-label">{{ field.label }}</div>

        <template v-if="field.field_type === 'chemical_equation'">
          <div class="detail-rich-value">
            <div class="equation-box">{{ equationText(field) }}</div>
            <div v-if="equationConditions(field)" class="muted">条件：{{ equationConditions(field) }}</div>
          </div>
        </template>

        <template v-else-if="field.field_type === 'reaction_process'">
          <div class="detail-rich-value">
            <div v-if="processSteps(field).length === 0" class="muted">无</div>
            <div v-for="(step, index) in processSteps(field)" :key="`${field.id}-${index}`" class="process-step">
              <strong>步骤 {{ index + 1 }}{{ step.title ? `：${step.title}` : '' }}</strong>
              <p v-if="step.operation"><strong>操作：</strong>{{ step.operation }}</p>
              <p v-if="step.condition"><strong>条件：</strong>{{ step.condition }}</p>
              <p v-if="step.observation"><strong>现象：</strong>{{ step.observation }}</p>
              <p v-if="step.expected_result"><strong>预期：</strong>{{ step.expected_result }}</p>
            </div>
          </div>
        </template>

        <template v-else>
          <pre class="detail-value">{{ formatDefault(rawValue(field)) }}</pre>
        </template>
      </div>
    </section>
  </div>
</template>

<style scoped>
.record-values-renderer {
  display: grid;
  gap: 16px;
}

.detail-rich-value {
  display: grid;
  gap: 8px;
}

.equation-box,
.process-step {
  border: 1px solid var(--color-border, #d9dce3);
  border-radius: 10px;
  padding: 12px;
  background: rgba(120, 130, 160, 0.04);
}

.equation-box {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.process-step {
  display: grid;
  gap: 4px;
}

.process-step p {
  margin: 0;
}
</style>
