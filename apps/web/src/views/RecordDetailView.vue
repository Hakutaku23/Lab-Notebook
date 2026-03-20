<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink, useRoute } from "vue-router";

import AttachmentManager from "../components/AttachmentManager.vue";
import AuditLogPanel from "../components/AuditLogPanel.vue";
import RecordFieldDisplay from "../components/RecordFieldDisplay.vue";
import RecordVersionsPanel from "../components/RecordVersionsPanel.vue";
import RecordWorkflowPanel from "../components/RecordWorkflowPanel.vue";
import { fetchRecordDetail } from "../api/records";
import { fetchTemplateDetail } from "../api/templates";
import type {
  ExperimentRecordDetail,
  ExperimentTemplateDetail,
  RecordFieldValueItem,
} from "../types/api";
import { getRecordStatusLabel } from "../utils/record-status";

const route = useRoute();

const loading = ref(false);
const error = ref("");
const record = ref<ExperimentRecordDetail | null>(null);
const template = ref<ExperimentTemplateDetail | null>(null);

const valueMap = computed<Record<string, RecordFieldValueItem>>(() => {
  const map: Record<string, RecordFieldValueItem> = {};
  for (const item of record.value?.values ?? []) {
    map[item.field_id] = item;
  }
  return map;
});

async function loadRecord() {
  const recordId = String(route.params.id || "");
  if (!recordId) return;

  loading.value = true;
  error.value = "";

  try {
    const recordData = await fetchRecordDetail(recordId);
    const templateData = await fetchTemplateDetail(recordData.template_id);
    record.value = recordData;
    template.value = templateData;
  } catch (err) {
    console.error(err);
    error.value = "记录详情加载失败。";
  } finally {
    loading.value = false;
  }
}

onMounted(loadRecord);
</script>

<template>
  <div class="page">
    <section v-if="loading" class="card">
      <p class="muted">正在加载记录详情...</p>
    </section>

    <section v-else-if="error" class="card">
      <p class="error-text">{{ error }}</p>
    </section>

    <template v-else-if="record && template">
      <section class="page-hero">
        <div>
          <p class="eyebrow">记录详情</p>
          <h2>{{ record.title }}</h2>
          <p class="muted">
            项目：{{ record.project_name || record.project_id }}
            · 模板：{{ record.template_name || record.template_id }}
            · 状态：{{ getRecordStatusLabel(record.status) }}
          </p>
        </div>
        <div class="row-between" style="gap: 12px; flex-wrap: wrap; align-items: center;">
          <RouterLink class="button secondary" to="/records">返回列表</RouterLink>
          <RouterLink class="button" :to="`/records/${record.id}/edit`">编辑记录</RouterLink>
        </div>
      </section>

      <section class="card">
        <div class="section-header">
          <div>
            <h3>摘要</h3>
            <p class="muted">{{ record.summary || "暂无摘要" }}</p>
          </div>
        </div>
      </section>

      <RecordWorkflowPanel :record="record" @changed="loadRecord" />

      <section v-for="section in template.sections" :key="section.id" class="card detail-section">
        <div class="section-header">
          <div>
            <h3>{{ section.title }}</h3>
            <p v-if="section.description" class="muted">{{ section.description }}</p>
          </div>
        </div>

        <div v-for="field in section.fields" :key="field.id" class="detail-item">
          <label class="label">{{ field.label }}</label>
          <RecordFieldDisplay :field="field" :value="valueMap[field.id]?.value_json" />
        </div>
      </section>

      <AttachmentManager :record-id="record.id" @changed="loadRecord" />
      <RecordVersionsPanel :record-id="record.id" @restored="loadRecord" />
      <AuditLogPanel
        title="当前记录审计日志"
        :initial-resource-type="'record'"
        :initial-resource-id="record.id"
      />
    </template>
  </div>
</template>

<style scoped>
.detail-section {
  display: grid;
  gap: 16px;
}

.detail-item {
  display: grid;
  gap: 8px;
}
</style>
