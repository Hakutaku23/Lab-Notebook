<script setup lang="ts">
import { computed } from "vue";

import ChemicalStructurePreview from "./ChemicalStructurePreview.vue";
import type { TemplateField } from "../types/api";
import { toPrettyJson } from "../utils/templateRuntime";

interface Props {
  field: TemplateField;
  value: unknown;
}

const props = defineProps<Props>();

const normalizedText = computed(() => {
  if (props.value === null || props.value === undefined || props.value === "") return "无";
  if (typeof props.value === "string") return props.value;
  return toPrettyJson(props.value);
});

const chemicalValue = computed(() => {
  if (typeof props.value === "string") {
    const trimmed = props.value.trim();
    if (!trimmed) return null;
    return {
      kind: "molecule",
      smiles: "",
      molfile: "",
      rxnfile: "",
      ket: "",
      svg: "",
      plain_text: trimmed,
    };
  }

  if (!props.value || typeof props.value !== "object") return null;
  return props.value as {
    kind?: string;
    smiles?: string;
    molfile?: string;
    rxnfile?: string;
    ket?: string;
    svg?: string;
    plain_text?: string;
  };
});

const chemicalKindLabel = computed(() => {
  if (chemicalValue.value?.kind === "reaction") return "反应";
  if (chemicalValue.value?.kind === "molecule") return "分子";
  return "结构";
});

const chemicalPreviewSource = computed(() => {
  const value = chemicalValue.value;
  if (!value) return "";

  if (value.rxnfile?.trim()) return value.rxnfile.trim();
  if (value.molfile?.trim()) return value.molfile.trim();
  if (value.ket?.trim()) return value.ket.trim();

  const plainText = value.plain_text?.trim() || "";
  if (plainText.includes("M  END") || plainText.startsWith("$RXN") || plainText.startsWith("{")) {
    return plainText;
  }

  return "";
});

const reactionSteps = computed(() => {
  if (!Array.isArray(props.value)) return [];
  return props.value as Array<Record<string, string>>;
});
</script>

<template>
  <div v-if="field.field_type === 'chemical_equation'">
    <div v-if="chemicalValue?.svg" class="chemical-preview" v-html="chemicalValue.svg" />
    <ChemicalStructurePreview
      v-else-if="chemicalPreviewSource"
      :structure="chemicalPreviewSource"
    />
    <div class="field-display-grid">
      <div v-if="chemicalValue?.smiles"><strong>SMILES：</strong>{{ chemicalValue.smiles }}</div>
      <div v-if="chemicalValue?.kind"><strong>类型：</strong>{{ chemicalKindLabel }}</div>
      <div v-if="chemicalValue?.rxnfile"><strong>RXN：</strong>已保存</div>
      <div v-if="chemicalValue?.molfile"><strong>Molfile：</strong>已保存</div>
    </div>
    <pre
      v-if="chemicalValue?.plain_text && !chemicalValue?.svg && !chemicalPreviewSource"
      class="detail-value"
    >{{ chemicalValue.plain_text }}</pre>
    <p v-else-if="!chemicalValue" class="muted">无</p>
  </div>

  <div v-else-if="field.field_type === 'reaction_process'">
    <div v-if="reactionSteps.length > 0" class="reaction-list">
      <div v-for="(step, index) in reactionSteps" :key="index" class="reaction-list__item">
        <strong>步骤 {{ index + 1 }}：{{ step.title || "未命名步骤" }}</strong>
        <div v-if="step.operation"><span class="muted">操作：</span>{{ step.operation }}</div>
        <div v-if="step.reagent"><span class="muted">试剂：</span>{{ step.reagent }}</div>
        <div v-if="step.condition"><span class="muted">条件：</span>{{ step.condition }}</div>
        <div v-if="step.observation"><span class="muted">现象：</span>{{ step.observation }}</div>
        <div v-if="step.note"><span class="muted">备注：</span>{{ step.note }}</div>
      </div>
    </div>
    <pre v-else class="detail-value">{{ normalizedText }}</pre>
  </div>

  <div v-else-if="field.field_type === 'checkbox'">
    <span>{{ value ? "是" : "否" }}</span>
  </div>

  <pre v-else class="detail-value">{{ normalizedText }}</pre>
</template>

<style scoped>
.chemical-preview {
  overflow-x: auto;
}

.chemical-preview :deep(svg) {
  max-width: 100%;
  height: auto;
}

.field-display-grid {
  display: grid;
  gap: 6px;
  margin-top: 10px;
}

.reaction-list {
  display: grid;
  gap: 10px;
}

.reaction-list__item {
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 12px;
  padding: 12px;
  background: rgba(248, 250, 252, 0.7);
}
</style>
