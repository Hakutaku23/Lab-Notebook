<script setup lang="ts">
import { computed } from "vue";

import RecordFieldDisplay from "./RecordFieldDisplay.vue";
import type { ExperimentTemplateDetail, RecordFieldValueItem } from "../types/api";

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
</script>

<template>
  <div class="record-values-renderer">
    <section v-for="section in template.sections" :key="section.id" class="card">
      <h3>{{ section.title }}</h3>
      <p v-if="section.description" class="muted">{{ section.description }}</p>

      <div v-for="field in section.fields" :key="field.id" class="detail-item">
        <div class="detail-label">{{ field.label }}</div>
        <RecordFieldDisplay :field="field" :value="valueMap[field.id]?.value_json" />
      </div>
    </section>
  </div>
</template>

<style scoped>
.record-values-renderer {
  display: grid;
  gap: 16px;
}
</style>
