<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink, useRoute } from "vue-router";

import AttachmentManager from "../components/AttachmentManager.vue";
import AuditLogPanel from "../components/AuditLogPanel.vue";
import RecordFieldValuePreview from "../components/RecordFieldValuePreview.vue";
import RecordWorkflowPanel from "../components/RecordWorkflowPanel.vue";
import RecordVersionsPanel from "../components/RecordVersionsPanel.vue";
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
  record.value?.values.forEach((item) => {
    map[item.field_id] = item;
  });
  return map;
});

async function loadRecord() {
  const recordId = String(route.params.id || "");
  if (!recordId) {
    error.value = "缺少记录 ID。";
    return;
  }

  loading.value = true;
  error.value = "";

  try {
    record.value = await fetchRecordDetail(recordId);
    template.value = await fetchTemplateDetail(record.value.template_id);
  } catch (err) {
    console.error(err);
    error.value = "实验记录详情加载失败。";
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
      <section class="card">
        <div class="row-between">
          <div>
            <h2>{{ record.title }}</h2>
            <p class="muted">项目：{{ record.project_name || record.project_id }}</p>
            <p class="muted">模板：{{ record.template_name || record.template_id }}</p>
            <p class="muted">状态：{{ getRecordStatusLabel(record.status) }}</p>
          </div>

          <div class="actions">
            <RouterLink class="button secondary" to="/records">返回列表</RouterLink>
            <RouterLink class="button secondary" :to="`/records/${record.id}/edit`">
              编辑记录
            </RouterLink>
          </div>
        </div>

        <p><strong>摘要：</strong>{{ record.summary || "暂无摘要" }}</p>
      </section>

      <RecordWorkflowPanel :record="record" @changed="loadRecord" />
      <section v-for="section in template.sections" :key="section.id" class="card">
        <h3>{{ section.title }}</h3>
        <p v-if="section.description" class="muted">{{ section.description }}</p>

        <div v-for="field in section.fields" :key="field.id" class="detail-item">
          <div class="detail-label">{{ field.label }}</div>
          <div class="detail-value-box">
            <RecordFieldValuePreview :field="field" :value="valueMap[field.id]?.value_json" />
          </div>
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
.detail-value-box {
  border: 1px solid #d7dbe7;
  border-radius: 12px;
  padding: 12px;
  background: #fafbfe;
}
</style>
