<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useRoute } from "vue-router";

import AttachmentManager from "../components/AttachmentManager.vue";
import DynamicTemplateForm from "../components/DynamicTemplateForm.vue";
import RecordVersionsPanel from "../components/RecordVersionsPanel.vue";
import { fetchRecordDetail, updateRecord } from "../api/records";
import { fetchTemplateDetail } from "../api/templates";
import type { ExperimentRecordDetail, ExperimentTemplateDetail } from "../types/api";
import { getRecordStatusLabel } from "../utils/record-status";
import { buildRecordPayloadValues, initializeFieldValues, mapRecordValues } from "../utils/templateRuntime";

const route = useRoute();

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

async function saveRecord() {
  if (!record.value || !template.value) return;

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
        <p class="muted">保存后会自动生成新快照，便于回溯内容变更。</p>
      </div>
    </section>

    <section class="card">
      <div v-if="loading" class="muted">正在加载记录...</div>

      <template v-else-if="record && template">
        <div class="form-item">
          <label class="label">标题</label>
          <input v-model="form.title" class="input" type="text" />
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
          <textarea v-model="form.summary" class="textarea" rows="3" />
        </div>

        <DynamicTemplateForm v-model="fieldValues" :template="template" />

        <button class="button" :disabled="saving" @click="saveRecord">
          {{ saving ? "保存中..." : "保存修改" }}
        </button>

        <p v-if="successText" class="muted">{{ successText }}</p>
        <p v-if="error" class="error-text">{{ error }}</p>
      </template>
    </section>

    <AttachmentManager v-if="record" :record-id="record.id" @changed="loadRecord" />
    <RecordVersionsPanel v-if="record" :record-id="record.id" @restored="handleVersionRestored" />
  </div>
</template>
