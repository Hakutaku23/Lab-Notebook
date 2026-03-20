<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watchEffect } from "vue";
import { useRoute } from "vue-router";

import AttachmentManager from "../components/AttachmentManager.vue";
import DynamicTemplateForm from "../components/DynamicTemplateForm.vue";
import RecordAISummaryPanel from "../components/RecordAISummaryPanel.vue";
import RecordVersionsPanel from "../components/RecordVersionsPanel.vue";
import { fetchRecordDetail, updateRecord } from "../api/records";
import { fetchTemplateDetail } from "../api/templates";
import { useAIStore } from "../stores/ai";
import type { ExperimentRecordDetail, ExperimentTemplateDetail } from "../types/api";
import { getRecordStatusLabel } from "../utils/record-status";
import { buildRecordPayloadValues, initializeFieldValues, mapRecordValues } from "../utils/templateRuntime";

const route = useRoute();
const aiStore = useAIStore();

const loading = ref(false);
const saving = ref(false);
const error = ref("");
const successText = ref("");

const record = ref<ExperimentRecordDetail | null>(null);
const template = ref<ExperimentTemplateDetail | null>(null);
const fieldValues = ref<Record<string, unknown>>({});

const form = reactive({
  title: "",
  summary: "",
});

const isLocked = computed(() => record.value?.status !== "draft");

watchEffect(() => {
  aiStore.setAssistantContext({
    title: "记录 AI 助手",
    description: "围绕当前实验记录的摘要、字段和版本内容发起提问。",
    placeholder: "例如：请帮我检查当前记录还缺哪些关键实验信息。",
    task: "assistant",
    context: {
      page: "record-edit",
      record_id: record.value?.id || "",
      title: form.title,
      status: record.value?.status || "",
      template_name: template.value?.name || "",
      template_key: template.value?.key || "",
      current_summary: form.summary,
      field_values: fieldValues.value,
    },
  });
});

onBeforeUnmount(() => {
  aiStore.resetAssistantContext();
});

const aiContext = ref<Record<string, unknown>>({});
watchEffect(() => {
  aiContext.value = {
    page: "record-edit",
    record_id: record.value?.id || "",
    title: form.title,
    status: record.value?.status || "",
    template_name: template.value?.name || "",
    template_key: template.value?.key || "",
    current_summary: form.summary,
    field_values: fieldValues.value,
  };
});

async function loadRecord() {
  const recordId = String(route.params.id || "");
  if (!recordId) return;

  loading.value = true;
  error.value = "";
  successText.value = "";

  try {
    const recordData = await fetchRecordDetail(recordId);
    const templateData = await fetchTemplateDetail(recordData.template_id);

    record.value = recordData;
    template.value = templateData;

    form.title = recordData.title;
    form.summary = recordData.summary || "";
    fieldValues.value = initializeFieldValues(templateData, mapRecordValues(recordData.values));
  } catch (err) {
    console.error(err);
    error.value = "记录加载失败。";
  } finally {
    loading.value = false;
  }
}

function openAssistant() {
  aiStore.openAssistant();
}

async function saveRecord() {
  if (!record.value || !template.value || isLocked.value) return;

  saving.value = true;
  error.value = "";
  successText.value = "";

  try {
    await updateRecord(record.value.id, {
      title: form.title,
      summary: form.summary || undefined,
      values: buildRecordPayloadValues(template.value, fieldValues.value),
    });

    successText.value = "记录已保存，系统已自动生成新的历史快照。";
    await loadRecord();
  } catch (err) {
    console.error(err);
    error.value = "记录保存失败，请检查字段格式。";
  } finally {
    saving.value = false;
  }
}

function applyRecordToForm(recordData: ExperimentRecordDetail) {
  if (!template.value) {
    return;
  }

  record.value = recordData;
  form.title = recordData.title;
  form.summary = recordData.summary || "";
  fieldValues.value = initializeFieldValues(template.value, mapRecordValues(recordData.values));
}

async function handleVersionRestored(restored: ExperimentRecordDetail) {
  successText.value = "已恢复历史版本，编辑表单已同步为当前记录内容。";
  if (!template.value || template.value.id !== restored.template_id) {
    await loadRecord();
    return;
  }

  applyRecordToForm(restored);
}

onMounted(loadRecord);
</script>

<template>
  <div class="page">
    <section class="page-hero">
      <div>
        <p class="eyebrow">编辑记录</p>
        <h2>编辑实验记录</h2>
        <p class="muted">保存后会自动生成新快照，便于回溯内容变更，并可使用 AI 辅助完善摘要。</p>
      </div>
      <div class="actions print-hidden">
        <button class="button secondary" type="button" @click="openAssistant">AI 助手</button>
      </div>
    </section>

    <section class="card">
      <div v-if="loading" class="muted">正在加载记录...</div>

      <template v-else-if="record && template">
        <div v-if="isLocked" class="status-display">
          <strong>当前正文已锁定</strong>
          <p class="muted">只有草稿状态允许直接编辑。若要继续修改，请先在详情页执行对应流程动作。</p>
        </div>

        <div class="form-item">
          <label class="label">标题</label>
          <input v-model="form.title" class="input" type="text" :disabled="isLocked" />
        </div>

        <div class="form-item">
          <label class="label">当前状态</label>
          <div class="status-display">
            <span class="badge">{{ getRecordStatusLabel(record.status) }}</span>
            <p class="muted">状态流转请到详情页的流程面板中操作。</p>
          </div>
        </div>

        <div class="form-item">
          <label class="label">摘要</label>
          <textarea v-model="form.summary" class="textarea" rows="4" :disabled="isLocked" />
        </div>

                <RecordAISummaryPanel v-if="!isLocked" v-model:summary="form.summary" :context="aiContext" />
        <p v-else class="muted">当前记录已锁定，AI 摘要建议请在详情页查看或先重新打开为草稿。</p>

        <DynamicTemplateForm v-model="fieldValues" :template="template" :disabled="isLocked" />

        <button class="button" :disabled="saving || isLocked" @click="saveRecord">
          {{ saving ? "保存中..." : "保存修改" }}
        </button>

        <p v-if="successText" class="muted">{{ successText }}</p>
        <p v-if="error" class="error-text">{{ error }}</p>
      </template>
    </section>

    <AttachmentManager v-if="record" :record-id="record.id" :disabled="isLocked" @changed="loadRecord" />
    <RecordVersionsPanel v-if="record" :record-id="record.id" @restored="handleVersionRestored" />
  </div>
</template>

