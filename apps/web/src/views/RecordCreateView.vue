<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import DynamicTemplateForm from "../components/DynamicTemplateForm.vue";
import { fetchProjects } from "../api/projects";
import { createRecord } from "../api/records";
import { fetchTemplateByKey, fetchTemplateDetail, fetchTemplates } from "../api/templates";
import type {
  ExperimentTemplateDetail,
  ExperimentTemplateSummary,
  ProjectItem,
  RecordFieldValuePayload,
  TemplateField,
} from "../types/api";

const route = useRoute();
const router = useRouter();

const loading = ref(false);
const submitting = ref(false);
const error = ref("");

const projects = ref<ProjectItem[]>([]);
const templates = ref<ExperimentTemplateSummary[]>([]);
const selectedTemplate = ref<ExperimentTemplateDetail | null>(null);
const fieldValues = ref<Record<string, unknown>>({});

const form = reactive({
  title: "",
  summary: "",
  project_id: "",
  template_id: "",
  created_by: "",
});

function initializeFieldValues(template: ExperimentTemplateDetail) {
  const nextValues: Record<string, unknown> = {};
  template.sections.forEach((section) => {
    section.fields.forEach((field) => {
      nextValues[field.id] =
        field.default_value !== undefined && field.default_value !== null
          ? field.default_value
          : "";
    });
  });
  fieldValues.value = nextValues;
}

async function loadTemplate(templateId: string) {
  selectedTemplate.value = await fetchTemplateDetail(templateId);
  initializeFieldValues(selectedTemplate.value);
}

function normalizeValue(field: TemplateField, value: unknown): unknown {
  if (typeof value !== "string") {
    return value;
  }

  const trimmed = value.trim();
  if (!trimmed) {
    return "";
  }

  if (field.field_type === "table" || field.field_type === "file" || field.field_type === "json") {
    try {
      return JSON.parse(trimmed);
    } catch {
      return value;
    }
  }

  return value;
}

function buildValuePayload(template: ExperimentTemplateDetail): RecordFieldValuePayload[] {
  return template.sections.flatMap((section) =>
    section.fields.map((field) => ({
      field_id: field.id,
      value_json: normalizeValue(field, fieldValues.value[field.id]),
    })),
  );
}

async function submitRecord() {
  if (!form.title.trim() || !form.project_id || !form.template_id || !selectedTemplate.value) {
    error.value = "标题、项目和模板不能为空。";
    return;
  }

  submitting.value = true;
  error.value = "";

  try {
    const created = await createRecord({
      title: form.title,
      summary: form.summary || undefined,
      project_id: form.project_id,
      template_id: form.template_id,
      created_by: form.created_by || undefined,
      values: buildValuePayload(selectedTemplate.value),
    });

    await router.push(`/records/${created.id}`);
  } catch (err) {
    console.error(err);
    error.value = "实验记录创建失败，请检查必填字段是否完整。";
  } finally {
    submitting.value = false;
  }
}

watch(
  () => form.template_id,
  async (templateId) => {
    if (!templateId) {
      selectedTemplate.value = null;
      return;
    }
    try {
      await loadTemplate(templateId);
    } catch (err) {
      console.error(err);
      error.value = "模板加载失败。";
    }
  },
);

onMounted(async () => {
  loading.value = true;
  error.value = "";

  try {
    const [projectData, templateData] = await Promise.all([
      fetchProjects(),
      fetchTemplates(),
    ]);

    projects.value = projectData;
    templates.value = templateData;

    if (typeof route.query.projectId === "string") {
      form.project_id = route.query.projectId;
    } else if (projects.value[0]) {
      form.project_id = projects.value[0].id;
    }

    try {
      const genericTemplate = await fetchTemplateByKey("generic-experiment-v1");
      form.template_id = genericTemplate.id;
    } catch {
      if (templates.value[0]) {
        form.template_id = templates.value[0].id;
      }
    }
  } catch (err) {
    console.error(err);
    error.value = "页面初始化失败。";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="page">
    <section class="page-hero">
      <div>
        <p class="eyebrow">Create Record</p>
        <h2>新建实验记录</h2>
        <p class="muted">新记录默认创建为草稿，后续可提交审核、补充附件与查看版本快照。</p>
      </div>
    </section>

    <section class="card">
      <div class="section-header">
        <div>
          <h3>记录表单</h3>
          <p class="muted">当前表单由模板动态生成，附件上传可在详情页继续补充。</p>
        </div>
      </div>

      <div v-if="loading" class="muted">正在加载项目与模板...</div>

      <template v-else>
        <div class="form-item">
          <label class="label">记录标题</label>
          <input v-model="form.title" class="input" type="text" placeholder="例如：酸碱滴定实验记录（第一次）" />
        </div>

        <div class="form-item">
          <label class="label">所属项目</label>
          <select v-model="form.project_id" class="input">
            <option value="">请选择项目</option>
            <option v-for="project in projects" :key="project.id" :value="project.id">
              {{ project.name }}
            </option>
          </select>
        </div>

        <div class="form-item">
          <label class="label">模板</label>
          <select v-model="form.template_id" class="input">
            <option value="">请选择模板</option>
            <option v-for="template in templates" :key="template.id" :value="template.id">
              {{ template.name }}（{{ template.category }}）
            </option>
          </select>
        </div>

        <div class="form-item">
          <label class="label">初始状态</label>
          <input class="input" type="text" value="draft（系统默认）" disabled />
        </div>

        <div class="form-item">
          <label class="label">创建者 ID（可选）</label>
          <input v-model="form.created_by" class="input" type="text" placeholder="默认当前用户" />
        </div>

        <div class="form-item">
          <label class="label">摘要</label>
          <textarea v-model="form.summary" class="textarea" rows="4" />
        </div>

        <DynamicTemplateForm v-model="fieldValues" :template="selectedTemplate" />

        <button
          class="button"
          :disabled="submitting || !selectedTemplate"
          @click="submitRecord"
        >
          {{ submitting ? "提交中..." : "创建草稿记录" }}
        </button>

        <p v-if="error" class="error-text">{{ error }}</p>
      </template>
    </section>
  </div>
</template>