<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watchEffect } from "vue";
import { RouterLink, useRoute } from "vue-router";

import AttachmentManager from "../components/AttachmentManager.vue";
import AuditLogPanel from "../components/AuditLogPanel.vue";
import RecordFieldDisplay from "../components/RecordFieldDisplay.vue";
import RecordAISummaryPanel from "../components/RecordAISummaryPanel.vue";
import RecordAIQualityPanel from "../components/RecordAIQualityPanel.vue";
import RecordVersionsPanel from "../components/RecordVersionsPanel.vue";
import RecordWorkflowPanel from "../components/RecordWorkflowPanel.vue";
import { fetchRecordDetail } from "../api/records";
import { fetchTemplateDetail } from "../api/templates";
import { useAIStore } from "../stores/ai";
import type {
  ExperimentRecordDetail,
  ExperimentTemplateDetail,
  RecordFieldValueItem,
} from "../types/api";
import { buildRecordQualityContext, buildRecordSectionsContext } from "../utils/recordAI";
import { getRecordStatusLabel } from "../utils/record-status";
import { mapRecordValues } from "../utils/templateRuntime";

const route = useRoute();
const aiStore = useAIStore();

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

const recordFieldValues = computed(() => mapRecordValues(record.value?.values || []));
const isEditable = computed(() => record.value?.status === "draft");

const aiContext = ref<Record<string, unknown>>({});
watchEffect(() => {
  aiContext.value = {
    page: "record-detail",
    record_id: record.value?.id || "",
    title: record.value?.title || "",
    status: record.value?.status || "",
    summary: record.value?.summary || "",
    project_name: record.value?.project_name || record.value?.project_id || "",
    template_name: template.value?.name || "",
    template_key: template.value?.key || "",
    sections: buildRecordSectionsContext(template.value, recordFieldValues.value),
  };

  aiStore.setAssistantContext({
    title: "记录 AI 助手",
    description: "围绕当前实验记录提问，例如提炼风险点、总结异常现象或给出审核前说明。",
    placeholder: "例如：请结合当前记录，列出 3 个需要进一步复核的风险点。",
    task: "assistant",
    context: aiContext.value,
  });
});

onBeforeUnmount(() => {
  aiStore.resetAssistantContext();
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

function openAssistant() {
  aiStore.openAssistant({
    prompt: "请结合当前记录详情，帮我做一次审核前质检，指出风险点、缺失说明和建议的审核意见。",
  });
}

function printRecord() {
  if (typeof window !== "undefined") {
    window.print();
  }
}

onMounted(loadRecord);
</script>

<template>
  <div class="page record-detail-page">
    <section v-if="loading" class="card">
      <p class="muted">正在加载记录详情...</p>
    </section>

    <section v-else-if="error" class="card">
      <p class="error-text">{{ error }}</p>
    </section>

    <template v-else-if="record && template">
      <section class="page-hero record-detail-hero">
        <div>
          <p class="eyebrow">记录详情</p>
          <h2>{{ record.title }}</h2>
          <p class="muted">
            项目：{{ record.project_name || record.project_id }}
            · 模板：{{ record.template_name || record.template_id }}
            · 状态：{{ getRecordStatusLabel(record.status) }}
          </p>
        </div>
        <div class="row-between print-hidden" style="gap: 12px; flex-wrap: wrap; align-items: center;">
          <RouterLink class="button secondary" to="/records">返回列表</RouterLink>
          <button class="button secondary" type="button" @click="openAssistant">AI 助手</button>
          <button class="button secondary" type="button" @click="printRecord">打印 / 导出 PDF</button>
          <RouterLink v-if="isEditable" class="button" :to="`/records/${record.id}/edit`">编辑记录</RouterLink>
          <span v-else class="badge">当前正文已锁定</span>
        </div>
      </section>

      <section class="card detail-overview-grid">
        <div class="sub-card">
          <strong>状态</strong>
          <div class="detail-overview-value">{{ getRecordStatusLabel(record.status) }}</div>
          <p class="muted">{{ isEditable ? "当前可继续编辑正文。" : "当前需通过流程动作才能重新进入可编辑状态。" }}</p>
        </div>
        <div class="sub-card">
          <strong>项目</strong>
          <div class="detail-overview-value">{{ record.project_name || record.project_id }}</div>
          <p class="muted">模板版本：v{{ record.template_version }}</p>
        </div>
        <div class="sub-card">
          <strong>最后更新时间</strong>
          <div class="detail-overview-value">{{ new Date(record.updated_at).toLocaleString() }}</div>
          <p class="muted">创建时间：{{ new Date(record.created_at).toLocaleString() }}</p>
        </div>
      </section>

      <section class="card">
        <div class="section-header">
          <div>
            <h3>摘要</h3>
            <p class="muted">{{ record.summary || "暂无摘要" }}</p>
          </div>
        </div>
        <div class="print-hidden">
          <RecordAISummaryPanel :summary="record.summary || ''" :context="aiContext" :editable="false" />
        </div>
      </section>

      <RecordAIQualityPanel
        class="print-hidden"
        :context="buildRecordQualityContext({
          template,
          page: 'record-detail',
          recordId: record.id,
          recordTitle: record.title,
          recordStatus: record.status,
          summary: record.summary || '',
          projectId: record.project_id,
          projectName: record.project_name || '',
          templateName: template.name,
          templateKey: template.key,
          fieldValues: recordFieldValues,
        })"
        :editable="false"
      />

      <RecordWorkflowPanel class="print-hidden" :record="record" @changed="loadRecord" />

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

      <AttachmentManager class="print-hidden" :record-id="record.id" @changed="loadRecord" />
      <RecordVersionsPanel class="print-hidden" :record-id="record.id" @restored="loadRecord" />
      <AuditLogPanel
        class="print-hidden"
        title="当前记录审计日志"
        :initial-resource-type="'record'"
        :initial-resource-id="record.id"
      />
    </template>
  </div>
</template>

<style scoped>
.detail-overview-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.detail-overview-value {
  margin-top: 8px;
  font-size: 1.05rem;
  font-weight: 700;
}

.detail-section {
  display: grid;
  gap: 16px;
}

.detail-item {
  display: grid;
  gap: 8px;
}

@media (max-width: 960px) {
  .detail-overview-grid {
    grid-template-columns: 1fr;
  }
}
</style>
