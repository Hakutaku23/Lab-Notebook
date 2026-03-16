<script setup lang="ts">
import type { ExperimentTemplateDetail, TemplateField } from "../types/api";

const props = defineProps<{
  template: ExperimentTemplateDetail | null;
  modelValue: Record<string, unknown>;
}>();

const emit = defineEmits<{
  "update:modelValue": [Record<string, unknown>];
}>();

function updateField(fieldId: string, value: unknown) {
  emit("update:modelValue", {
    ...props.modelValue,
    [fieldId]: value,
  });
}

function onTextInput(fieldId: string, event: Event) {
  const target = event.target as HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement;
  updateField(fieldId, target.value);
}

function onNumberInput(fieldId: string, event: Event) {
  const target = event.target as HTMLInputElement;
  updateField(fieldId, target.value === "" ? "" : Number(target.value));
}

function onCheckboxChange(fieldId: string, event: Event) {
  const target = event.target as HTMLInputElement;
  updateField(fieldId, target.checked);
}

function fieldTextValue(field: TemplateField): string {
  const value = props.modelValue[field.id];
  if (value === null || value === undefined) {
    return "";
  }
  if (typeof value === "string") {
    return value;
  }
  return JSON.stringify(value, null, 2);
}

function fieldNumberValue(field: TemplateField): number | string {
  const value = props.modelValue[field.id];
  if (typeof value === "number") {
    return value;
  }
  return "";
}

function fieldBooleanValue(field: TemplateField): boolean {
  return Boolean(props.modelValue[field.id]);
}

function resolveSelectOptions(field: TemplateField): Array<{ label: string; value: string }> {
  const raw = field.options?.choices;
  if (!Array.isArray(raw)) {
    return [];
  }

  return raw.map((item) => {
    if (typeof item === "object" && item && "label" in item && "value" in item) {
      return {
        label: String((item as { label: unknown }).label),
        value: String((item as { value: unknown }).value),
      };
    }
    return {
      label: String(item),
      value: String(item),
    };
  });
}
</script>

<template>
  <div v-if="template" class="template-form">
    <section
      v-for="section in template.sections"
      :key="section.id"
      class="card"
    >
      <h3>{{ section.title }}</h3>
      <p v-if="section.description" class="muted">{{ section.description }}</p>

      <div
        v-for="field in section.fields"
        :key="field.id"
        class="form-item"
      >
        <label class="label">
          {{ field.label }}
          <span v-if="field.required" class="required">*</span>
        </label>

        <input
          v-if="field.field_type === 'text'"
          class="input"
          type="text"
          :placeholder="field.placeholder ?? ''"
          :value="fieldTextValue(field)"
          @input="onTextInput(field.id, $event)"
        />

        <input
          v-else-if="field.field_type === 'date'"
          class="input"
          type="date"
          :value="fieldTextValue(field)"
          @input="onTextInput(field.id, $event)"
        />

        <input
          v-else-if="field.field_type === 'number'"
          class="input"
          type="number"
          :value="fieldNumberValue(field)"
          @input="onNumberInput(field.id, $event)"
        />

        <select
          v-else-if="field.field_type === 'select'"
          class="input"
          :value="fieldTextValue(field)"
          @change="onTextInput(field.id, $event)"
        >
          <option value="">请选择</option>
          <option
            v-for="opt in resolveSelectOptions(field)"
            :key="opt.value"
            :value="opt.value"
          >
            {{ opt.label }}
          </option>
        </select>

        <label
          v-else-if="field.field_type === 'checkbox'"
          style="display:flex; gap:8px; align-items:center;"
        >
          <input
            type="checkbox"
            :checked="fieldBooleanValue(field)"
            @change="onCheckboxChange(field.id, $event)"
          />
          <span>勾选</span>
        </label>

        <textarea
          v-else-if="field.field_type === 'textarea' || field.field_type === 'richtext' || field.field_type === 'json'"
          class="textarea"
          rows="5"
          :placeholder="field.placeholder ?? ''"
          :value="fieldTextValue(field)"
          @input="onTextInput(field.id, $event)"
        />

        <textarea
          v-else-if="field.field_type === 'table'"
          class="textarea"
          rows="6"
          placeholder="可填写 JSON / CSV / Markdown 表格。"
          :value="fieldTextValue(field)"
          @input="onTextInput(field.id, $event)"
        />

        <textarea
          v-else-if="field.field_type === 'file'"
          class="textarea"
          rows="3"
          placeholder="这里可记录附件说明；真实上传请在记录编辑页附件区完成。"
          :value="fieldTextValue(field)"
          @input="onTextInput(field.id, $event)"
        />

        <textarea
          v-else
          class="textarea"
          rows="4"
          :placeholder="field.placeholder ?? ''"
          :value="fieldTextValue(field)"
          @input="onTextInput(field.id, $event)"
        />

        <p v-if="field.help_text" class="help-text">{{ field.help_text }}</p>
      </div>
    </section>
  </div>
</template>