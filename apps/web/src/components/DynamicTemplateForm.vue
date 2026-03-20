<script setup lang="ts">
import { computed } from "vue";

import type { ExperimentTemplateDetail, TemplateField } from "../types/api";
import KetcherField from "./KetcherField.vue";
import ReactionProcessField from "./ReactionProcessField.vue";
import { getFieldDefaultValue, toPrettyJson } from "../utils/templateRuntime";

interface Props {
  modelValue: Record<string, unknown>;
  template: ExperimentTemplateDetail | null;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  (event: "update:modelValue", value: Record<string, unknown>): void;
}>();

const sections = computed(() => props.template?.sections ?? []);

function updateFieldValue(fieldId: string, value: unknown) {
  emit("update:modelValue", {
    ...props.modelValue,
    [fieldId]: value,
  });
}

function fieldValue(field: TemplateField): unknown {
  return props.modelValue[field.id] ?? getFieldDefaultValue(field);
}

function optionsForField(field: TemplateField): Array<{ label: string; value: string }> {
  const source = field.options as any;
  if (!source) return [];

  if (Array.isArray(source)) {
    return source.map((item) => {
      if (typeof item === "string") return { label: item, value: item };
      return {
        label: String(item.label ?? item.name ?? item.value ?? "选项"),
        value: String(item.value ?? item.key ?? item.label ?? item.name ?? ""),
      };
    });
  }

  if (Array.isArray(source.items)) {
    return source.items.map((item: any) => ({
      label: String(item.label ?? item.name ?? item.value ?? "选项"),
      value: String(item.value ?? item.key ?? item.label ?? item.name ?? ""),
    }));
  }

  if (typeof source === "object") {
    return Object.entries(source).map(([value, label]) => ({
      label: String(label),
      value,
    }));
  }

  return [];
}

function placeholderForField(field: TemplateField): string {
  return field.placeholder || `请输入 ${field.label}`;
}
</script>

<template>
  <div class="dynamic-template-form">
    <section v-for="section in sections" :key="section.id" class="card dynamic-template-form__section">
      <div class="section-header">
        <div>
          <h3>{{ section.title }}</h3>
          <p v-if="section.description" class="muted">{{ section.description }}</p>
        </div>
      </div>

      <div v-for="field in section.fields" :key="field.id" class="form-item">
        <label class="label">
          {{ field.label }}
          <span v-if="field.required" style="color: #dc2626;">*</span>
        </label>

        <p v-if="field.help_text" class="muted" style="margin-bottom: 8px;">{{ field.help_text }}</p>

        <input
          v-if="field.field_type === 'text' || field.field_type === 'richtext'"
          class="input"
          type="text"
          :value="String(fieldValue(field) ?? '')"
          :placeholder="placeholderForField(field)"
          @input="updateFieldValue(field.id, ($event.target as HTMLInputElement).value)"
        />

        <textarea
          v-else-if="field.field_type === 'textarea'"
          class="textarea"
          rows="4"
          :value="String(fieldValue(field) ?? '')"
          :placeholder="placeholderForField(field)"
          @input="updateFieldValue(field.id, ($event.target as HTMLTextAreaElement).value)"
        />

        <input
          v-else-if="field.field_type === 'number'"
          class="input"
          type="number"
          :value="String(fieldValue(field) ?? '')"
          :placeholder="placeholderForField(field)"
          @input="updateFieldValue(field.id, ($event.target as HTMLInputElement).value)"
        />

        <input
          v-else-if="field.field_type === 'date'"
          class="input"
          type="date"
          :value="String(fieldValue(field) ?? '')"
          @input="updateFieldValue(field.id, ($event.target as HTMLInputElement).value)"
        />

        <select
          v-else-if="field.field_type === 'select'"
          class="input"
          :value="String(fieldValue(field) ?? '')"
          @change="updateFieldValue(field.id, ($event.target as HTMLSelectElement).value)"
        >
          <option value="">请选择</option>
          <option v-for="option in optionsForField(field)" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>

        <label v-else-if="field.field_type === 'checkbox'" class="label" style="display: flex; gap: 8px; align-items: center;">
          <input
            type="checkbox"
            :checked="Boolean(fieldValue(field))"
            @change="updateFieldValue(field.id, ($event.target as HTMLInputElement).checked)"
          />
          选中
        </label>

        <ReactionProcessField
          v-else-if="field.field_type === 'reaction_process'"
          :model-value="fieldValue(field) as any"
          @update:model-value="updateFieldValue(field.id, $event)"
        />

        <KetcherField
          v-else-if="field.field_type === 'chemical_equation'"
          :model-value="fieldValue(field) as any"
          :label="field.label"
          :help-text="field.help_text"
          @update:model-value="updateFieldValue(field.id, $event)"
        />

        <textarea
          v-else-if="field.field_type === 'json' || field.field_type === 'table' || field.field_type === 'file'"
          class="textarea"
          rows="8"
          :value="toPrettyJson(fieldValue(field))"
          :placeholder="field.field_type === 'file' ? '请输入文件元数据 JSON 数组' : '请输入 JSON 内容'"
          @input="updateFieldValue(field.id, ($event.target as HTMLTextAreaElement).value)"
        />

        <input
          v-else
          class="input"
          type="text"
          :value="String(fieldValue(field) ?? '')"
          :placeholder="placeholderForField(field)"
          @input="updateFieldValue(field.id, ($event.target as HTMLInputElement).value)"
        />
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

.dynamic-template-form__section {
  display: grid;
  gap: 14px;
}
</style>
