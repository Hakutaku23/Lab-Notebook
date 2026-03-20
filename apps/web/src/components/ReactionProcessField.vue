<script setup lang="ts">
import { computed } from "vue";

import type { ReactionProcessStep } from "../utils/templateRuntime";

interface Props {
  modelValue: ReactionProcessStep[] | string | null | undefined;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  (event: "update:modelValue", value: ReactionProcessStep[]): void;
}>();

const steps = computed<ReactionProcessStep[]>(() => {
  if (Array.isArray(props.modelValue)) return props.modelValue;
  if (typeof props.modelValue === "string" && props.modelValue.trim()) {
    return props.modelValue
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => ({ title: line }));
  }
  return [];
});

function updateSteps(nextSteps: ReactionProcessStep[]) {
  emit(
    "update:modelValue",
    nextSteps.map((step) => ({
      title: step.title || "",
      operation: step.operation || "",
      reagent: step.reagent || "",
      condition: step.condition || "",
      observation: step.observation || "",
      note: step.note || "",
    })),
  );
}

function addStep() {
  updateSteps([
    ...steps.value,
    {
      title: `步骤 ${steps.value.length + 1}`,
      operation: "",
      reagent: "",
      condition: "",
      observation: "",
      note: "",
    },
  ]);
}

function removeStep(index: number) {
  updateSteps(steps.value.filter((_, currentIndex) => currentIndex !== index));
}

function updateStep(index: number, key: keyof ReactionProcessStep, value: string) {
  const nextSteps = steps.value.map((step, currentIndex) =>
    currentIndex === index ? { ...step, [key]: value } : step,
  );
  updateSteps(nextSteps);
}
</script>

<template>
  <div class="reaction-process-field">
    <div class="row-between" style="align-items: center; gap: 12px;">
      <div>
        <strong>反应过程记录</strong>
        <p class="muted" style="margin-top: 6px;">按步骤记录操作、试剂、条件与现象。</p>
      </div>
      <button class="button secondary" type="button" @click="addStep">新增步骤</button>
    </div>

    <div v-if="steps.length === 0" class="card" style="padding: 14px;">
      <p class="muted">当前没有步骤，点击“新增步骤”开始填写。</p>
    </div>

    <div v-for="(step, index) in steps" :key="`${index}-${step.title}`" class="card reaction-process-field__step">
      <div class="row-between" style="align-items: center; gap: 12px;">
        <strong>步骤 {{ index + 1 }}</strong>
        <button class="button secondary" type="button" @click="removeStep(index)">删除</button>
      </div>

      <div class="form-item">
        <label class="label">步骤标题</label>
        <input
          :value="step.title"
          class="input"
          type="text"
          @input="updateStep(index, 'title', ($event.target as HTMLInputElement).value)"
        />
      </div>

      <div class="grid-two">
        <div class="form-item">
          <label class="label">操作</label>
          <input
            :value="step.operation"
            class="input"
            type="text"
            @input="updateStep(index, 'operation', ($event.target as HTMLInputElement).value)"
          />
        </div>

        <div class="form-item">
          <label class="label">试剂/材料</label>
          <input
            :value="step.reagent"
            class="input"
            type="text"
            @input="updateStep(index, 'reagent', ($event.target as HTMLInputElement).value)"
          />
        </div>
      </div>

      <div class="grid-two">
        <div class="form-item">
          <label class="label">反应条件</label>
          <input
            :value="step.condition"
            class="input"
            type="text"
            @input="updateStep(index, 'condition', ($event.target as HTMLInputElement).value)"
          />
        </div>

        <div class="form-item">
          <label class="label">现象/结果</label>
          <input
            :value="step.observation"
            class="input"
            type="text"
            @input="updateStep(index, 'observation', ($event.target as HTMLInputElement).value)"
          />
        </div>
      </div>

      <div class="form-item">
        <label class="label">备注</label>
        <textarea
          class="textarea"
          rows="3"
          :value="step.note"
          @input="updateStep(index, 'note', ($event.target as HTMLTextAreaElement).value)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.reaction-process-field {
  display: grid;
  gap: 12px;
}

.reaction-process-field__step {
  display: grid;
  gap: 12px;
}

.grid-two {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 900px) {
  .grid-two {
    grid-template-columns: 1fr;
  }
}
</style>
