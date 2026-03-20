<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watchEffect } from "vue";
import { useRoute } from "vue-router";

import AttachmentManager from "../components/AttachmentManager.vue";
import DynamicTemplateForm from "../components/DynamicTemplateForm.vue";
import RecordAISummaryPanel from "../components/RecordAISummaryPanel.vue";
import RecordAIQualityPanel from "../components/RecordAIQualityPanel.vue";
import RecordVersionsPanel from "../components/RecordVersionsPanel.vue";
import { fetchRecordDetail, updateRecord } from "../api/records";
import { fetchTemplateDetail } from "../api/templates";
import { useAIStore } from "../stores/ai";
import type { ExperimentRecordDetail, ExperimentTemplateDetail } from "../types/api";
import { buildRecordQualityContext, buildRecordSectionsContext } from "../utils/recordAI";
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
    sections: buildRecordSectionsContext(template.value, fieldValues.value),
  };

  aiStore.setAssistantContext({
    title: "记录 AI 助手",
    description: isLocked.value
      ? "当前记录正文已锁定，可用于查看建议、质检与审核前说明。"
      : "围绕当前实验记录的摘要、字段补全和提交流程发起提问。",
    placeholder: isLocked.value
      ? "例如：请帮我检查这条已锁定记录是否还有需要在审核意见中说明的风险点。"
      : "例如：请帮我检查当前记录还缺哪些关键实验信息。",
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
  aiStore.openAssistant({
    prompt: isLocked.value
      ? "请结合当前记录内容，帮我做一次审核前检查，并指出应在流程意见中补充说明的风险点。"
      : "请结合当前记录标题、摘要和字段内容，帮我补全缺失信息并给出提交审核前的修改建议。",
  });
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
        <p class="muted">保存后会自动生成新快照，便于回溯内容变更，并可使用 AI 辅助完善摘要与字段。</p>
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
          <p class="muted">只有草稿状态允许直接编辑。锁定期间仅保留 AI 查看/质检能力，不允许字段或摘要回写。</p>
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
        <RecordAISummaryPanel v-else :summary="form.summary" :context="aiContext" :editable="false" />

        <RecordAIQualityPanel
          :context="buildRecordQualityContext({
            template,
            page: 'record-edit',
            recordId: record.id,
            recordTitle: form.title,
            recordStatus: record.status,
            summary: form.summary,
            projectId: record.project_id,
            projectName: record.project_name || '',
            fieldValues,
          })"
          :editable="!isLocked"
        />

        <DynamicTemplateForm
          v-model="fieldValues"
          :template="template"
          :disabled="isLocked"
          :ai-enabled="!isLocked"
          ai-page="record-edit"
          :ai-record-id="record.id"
          :ai-record-title="form.title"
          :ai-record-status="record.status"
          :ai-summary="form.summary"
          :ai-project-id="record.project_id"
        />

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
