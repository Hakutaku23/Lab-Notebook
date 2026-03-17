<script setup lang="ts">
import { computed } from "vue";

import type { ExperimentTemplateDetail, TemplateField } from "../types/api";
import {
  asTextAreaValue,
  buildSelectOptions,
  coerceChemicalEquationValue,
  coerceReactionProcessSteps,
  emptyReactionProcessStep,
  FIELD_TYPE_REGISTRY,
} from "../utils/templateFields";

const props = defineProps<{
  modelValue: Record<string, unknown>;
  template?: ExperimentTemplateDetail | null;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: Record<string, unknown>): void;
}>();

const sections = computed(() => props.template?.sections ?? []);

function updateField(fieldId: string, value: unknown) {
  emit("update:modelValue", {
    ...(props.modelValue ?? {}),
    [fieldId]: value,
  });
}

function rawFieldValue(fieldId: string): unknown {
  return props.modelValue?.[fieldId];
}

function textFieldValue(fieldId: string): string {
  return asTextAreaValue(rawFieldValue(fieldId));
}

function numberFieldValue(fieldId: string): string | number {
  const value = rawFieldValue(fieldId);
  if (typeof value === "number") return value;
  return typeof value === "string" ? value : "";
}

function checkboxFieldValue(fieldId: string): boolean {
  return Boolean(rawFieldValue(fieldId));
}

function chemicalEquationValue(fieldId: string) {
  return coerceChemicalEquationValue(rawFieldValue(fieldId));
}

function reactionSteps(fieldId: string) {
  return coerceReactionProcessSteps(rawFieldValue(fieldId));
}

function updateChemicalEquation(fieldId: string, key: "equation" | "conditions" | "notes", value: string) {
  const next = {
    ...chemicalEquationValue(fieldId),
    [key]: value,
  };
  updateField(fieldId, next);
}

function addReactionStep(fieldId: string) {
  const next = [...reactionSteps(fieldId), emptyReactionProcessStep()];
  updateField(fieldId, next);
}

function removeReactionStep(fieldId: string, index: number) {
  const next = reactionSteps(fieldId).filter((_, stepIndex) => stepIndex !== index);
  updateField(fieldId, next);
}

function updateReactionStep(
  fieldId: string,
  index: number,
  key: "title" | "description" | "conditions" | "observation",
  value: string,
) {
  const next = reactionSteps(fieldId).map((step, stepIndex) =>
    stepIndex === index ? { ...step, [key]: value } : step,
  );
  updateField(fieldId, next);
}

function fieldTypeLabel(field: TemplateField): string {
  return FIELD_TYPE_REGISTRY[field.field_type]?.label ?? field.field_type;
}

function fieldOptions(field: TemplateField) {
  return buildSelectOptions(field.options);
}
</script>

<template>
  <div v-if="template" class="dynamic-template-form">
    <section v-for="section in sections" :key="section.id" class="card template-section-card">
      <div class="row-between" style="align-items: flex-start; gap: 12px;">
        <div>
          <h3>{{ section.title }}</h3>
          <p v-if="section.description" class="muted">{{ section.description }}</p>
        </div>
      </div>

      <div v-for="field in section.fields" :key="field.id" class="form-item template-field-item">
        <div class="field-head">
          <label class="label">
            {{ field.label }}
            <span v-if="field.required" class="required-mark">*</span>
          </label>
          <span class="field-type-pill">{{ fieldTypeLabel(field) }}</span>
        </div>

        <input
          v-if="field.field_type === 'text'"
          class="input"
          type="text"
          :placeholder="field.placeholder ?? ''"
          :value="textFieldValue(field.id)"
          @input="updateField(field.id, ($event.target as HTMLInputElement).value)"
        />

        <input
          v-else-if="field.field_type === 'date'"
          class="input"
          type="date"
          :value="textFieldValue(field.id)"
          @input="updateField(field.id, ($event.target as HTMLInputElement).value)"
        />

        <input
          v-else-if="field.field_type === 'number'"
          class="input"
          type="number"
          :placeholder="field.placeholder ?? ''"
          :value="numberFieldValue(field.id)"
          @input="updateField(field.id, ($event.target as HTMLInputElement).value)"
        />

        <select
          v-else-if="field.field_type === 'select'"
          class="input"
          :value="String(rawFieldValue(field.id) ?? '')"
          @change="updateField(field.id, ($event.target as HTMLSelectElement).value)"
        >
          <option value="">请选择</option>
          <option v-for="option in fieldOptions(field)" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>

        <label v-else-if="field.field_type === 'checkbox'" class="checkbox-row">
          <input
            type="checkbox"
            :checked="checkboxFieldValue(field.id)"
            @change="updateField(field.id, ($event.target as HTMLInputElement).checked)"
          />
          <span>勾选</span>
        </label>

        <div v-else-if="field.field_type === 'chemical_equation'" class="chemistry-block">
          <textarea
            class="textarea"
            rows="3"
            :placeholder="field.placeholder ?? '例如：CH3COOH + NaOH -> CH3COONa + H2O'"
            :value="chemicalEquationValue(field.id).equation"
            @input="updateChemicalEquation(field.id, 'equation', ($event.target as HTMLTextAreaElement).value)"
          />
          <input
            class="input"
            type="text"
            placeholder="反应条件，例如温度、催化剂、pH 或压力"
            :value="chemicalEquationValue(field.id).conditions"
            @input="updateChemicalEquation(field.id, 'conditions', ($event.target as HTMLInputElement).value)"
          />
          <textarea
            class="textarea"
            rows="2"
            placeholder="补充说明，例如副反应、配平备注或记录方式"
            :value="chemicalEquationValue(field.id).notes"
            @input="updateChemicalEquation(field.id, 'notes', ($event.target as HTMLTextAreaElement).value)"
          />
        </div>

        <div v-else-if="field.field_type === 'reaction_process'" class="chemistry-block">
          <div v-if="reactionSteps(field.id).length === 0" class="muted">暂无步骤，请添加。</div>
          <div v-for="(step, index) in reactionSteps(field.id)" :key="`${field.id}-${index}`" class="step-card">
            <div class="row-between" style="gap: 12px; align-items: center;">
              <strong>步骤 {{ index + 1 }}</strong>
              <button class="button secondary small-button" type="button" @click="removeReactionStep(field.id, index)">
                删除步骤
              </button>
            </div>
            <input
              class="input"
              type="text"
              placeholder="步骤标题，例如投料、升温、滴加、老化、洗涤"
              :value="step.title"
              @input="updateReactionStep(field.id, index, 'title', ($event.target as HTMLInputElement).value)"
            />
            <textarea
              class="textarea"
              rows="3"
              placeholder="操作描述"
              :value="step.description"
              @input="updateReactionStep(field.id, index, 'description', ($event.target as HTMLTextAreaElement).value)"
            />
            <input
              class="input"
              type="text"
              placeholder="条件，例如 80°C / 30 min / N2 气氛"
              :value="step.conditions"
              @input="updateReactionStep(field.id, index, 'conditions', ($event.target as HTMLInputElement).value)"
            />
            <textarea
              class="textarea"
              rows="2"
              placeholder="现象或预期观察"
              :value="step.observation"
              @input="updateReactionStep(field.id, index, 'observation', ($event.target as HTMLTextAreaElement).value)"
            />
          </div>
          <button class="button secondary small-button" type="button" @click="addReactionStep(field.id)">
            添加步骤
          </button>
        </div>

        <textarea
          v-else-if="field.field_type === 'textarea' || field.field_type === 'richtext'"
          class="textarea"
          rows="4"
          :placeholder="field.placeholder ?? ''"
          :value="textFieldValue(field.id)"
          @input="updateField(field.id, ($event.target as HTMLTextAreaElement).value)"
        />

        <textarea
          v-else-if="field.field_type === 'json' || field.field_type === 'table' || field.field_type === 'file'"
          class="textarea"
          rows="6"
          :placeholder="field.placeholder ?? '可填写纯文本，或输入 JSON 结构。'"
          :value="textFieldValue(field.id)"
          @input="updateField(field.id, ($event.target as HTMLTextAreaElement).value)"
        />

        <textarea
          v-else
          class="textarea"
          rows="4"
          :placeholder="field.placeholder ?? ''"
          :value="textFieldValue(field.id)"
          @input="updateField(field.id, ($event.target as HTMLTextAreaElement).value)"
        />

        <p v-if="field.help_text" class="help-text">{{ field.help_text }}</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.dynamic-template-form {
  display: grid;
  gap: 16px;
  margin-top: 16px;
}

.template-section-card {
  margin: 0;
}

.template-field-item {
  margin-top: 14px;
}

.field-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.required-mark {
  color: #d14343;
}

.field-type-pill {
  border: 1px solid #d7dbe7;
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 12px;
  color: #5b6475;
  white-space: nowrap;
}

.checkbox-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.chemistry-block {
  display: grid;
  gap: 10px;
}

.step-card {
  border: 1px solid #d7dbe7;
  border-radius: 12px;
  padding: 12px;
  display: grid;
  gap: 10px;
  background: #fafbfe;
}

.small-button {
  padding: 6px 10px;
  font-size: 13px;
}
</style>
