<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useRoute } from "vue-router";

import AttachmentManager from "../components/AttachmentManager.vue";
import DynamicTemplateForm from "../components/DynamicTemplateForm.vue";
import RecordVersionsPanel from "../components/RecordVersionsPanel.vue";

import { fetchRecordDetail, updateRecord } from "../api/records";
import { fetchTemplateDetail } from "../api/templates";
import type {
  ExperimentRecordDetail,
  ExperimentTemplateDetail,
  RecordFieldValuePayload,
} from "../types/api";
import { getRecordStatusLabel } from "../utils/record-status";
import {
  initializeTemplateFieldValues,
  normalizeFieldValue,
} from "../utils/templateFields";

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

function buildPayloadValues(tpl: ExperimentTemplateDetail): RecordFieldValuePayload[] {
  return tpl.sections.flatMap((section) =>
    section.fields.map((field) => ({
      field_id: field.id,
      value_json: normalizeFieldValue(field, fieldValues.value[field.id]),
    })),
  );
}

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

    const nextValues = initializeTemplateFieldValues(templateData);
    recordData.values.forEach((item) => {
      nextValues[item.field_id] = item.value_json;
    });
    fieldValues.value = nextValues;
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
      values: buildPayloadValues(template.value),
    });

    successText.value = "记录已保存，系统已自动生成新的历史快照。";
    await loadRecord();
  } catch (err) {
    console.error(err);
    error.value = "记录保存失败，请检查必填字段是否完整。";
  } finally {
    saving.value = false;
  }
}

onMounted(loadRecord);
</script>

<template>
  <div class="page">
    <section class="card">
      <div class="section-header">
        <div>
          <h2>编辑实验记录</h2>
          <p class="muted">保存后会自动生成一条新快照，便于回溯内容变更。</p>
        </div>
      </div>

      <p v-if="loading" class="muted">正在加载记录...</p>

      <template v-else-if="record && template">
        <div class="form-item">
          <label class="label">标题</label>
          <input v-model="form.title" class="input" type="text" />
        </div>

        <div class="form-item">
          <label class="label">当前状态</label>
          <div class="status-display">
            <span class="badge">{{ getRecordStatusLabel(record.status) }}</span>
            <p class="muted">状态流转请在详情页的流程面板中操作，编辑页仅负责内容修改。</p>
          </div>
        </div>

        <div class="form-item">
          <label class="label">摘要</label>
          <textarea v-model="form.summary" class="textarea" rows="4" />
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
    <RecordVersionsPanel v-if="record" :record-id="record.id" />
  </div>
</template>
