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
} from "../types/api";
import { getRecordStatusLabel } from "../utils/record-status";
import { buildRecordPayloadValues, initializeFieldValues } from "../utils/templateRuntime";

const route = useRoute();
const router = useRouter();

const loading = ref(false);
const submitting = ref(false);
const error = ref("");

const projects = ref<ProjectItem[]>([]);
const templates = ref<ExperimentTemplateSummary[]>([]);
const selectedTemplate = ref<ExperimentTemplateDetail | null>(null);
const fieldValues = ref<Record<string, unknown>>({});

const initialStatus = "draft";

const form = reactive({
  title: "",
  summary: "",
  project_id: "",
  template_id: "",
  created_by: "",
});

async function loadTemplate(templateId: string) {
  if (!templateId) {
    selectedTemplate.value = null;
    fieldValues.value = {};
    return;
  }

  const template = await fetchTemplateDetail(templateId);
  selectedTemplate.value = template;
  fieldValues.value = initializeFieldValues(template);
}

async function loadPageData() {
  loading.value = true;
  error.value = "";

  try {
    const [projectData, templateData] = await Promise.all([fetchProjects(), fetchTemplates(true)]);
    projects.value = projectData;
    templates.value = templateData;

    const projectIdFromQuery =
      typeof route.query.projectId === "string"
        ? route.query.projectId
        : typeof route.query.project_id === "string"
          ? route.query.project_id
          : "";

    const templateIdFromQuery =
      typeof route.query.templateId === "string"
        ? route.query.templateId
        : typeof route.query.template_id === "string"
          ? route.query.template_id
          : "";

    const templateKeyFromQuery =
      typeof route.query.templateKey === "string"
        ? route.query.templateKey
        : typeof route.query.template_key === "string"
          ? route.query.template_key
          : "";

    if (projectIdFromQuery) {
      form.project_id = projectIdFromQuery;
    } else if (projects.value[0]) {
      form.project_id = projects.value[0].id;
    }

    if (templateIdFromQuery) {
      form.template_id = templateIdFromQuery;
      await loadTemplate(templateIdFromQuery);
      return;
    }

    if (templateKeyFromQuery) {
      const template = await fetchTemplateByKey(templateKeyFromQuery);
      form.template_id = template.id;
      selectedTemplate.value = template;
      fieldValues.value = initializeFieldValues(template);
      return;
    }

    try {
      const defaultTemplate = await fetchTemplateByKey("generic-experiment-v1");
      form.template_id = defaultTemplate.id;
      selectedTemplate.value = defaultTemplate;
      fieldValues.value = initializeFieldValues(defaultTemplate);
    } catch {
      if (templates.value[0]) {
        form.template_id = templates.value[0].id;
        await loadTemplate(form.template_id);
      }
    }
  } catch (err) {
    console.error(err);
    error.value = "项目或模板加载失败。";
  } finally {
    loading.value = false;
  }
}

async function submitRecord() {
  if (!selectedTemplate.value) {
    error.value = "请先选择模板。";
    return;
  }

  if (!form.title.trim() || !form.project_id) {
    error.value = "请先填写标题并选择项目。";
    return;
  }

  submitting.value = true;
  error.value = "";

  try {
    const created = await createRecord({
      title: form.title.trim(),
      summary: form.summary || undefined,
      status: initialStatus,
      project_id: form.project_id,
      template_id: selectedTemplate.value.id,
      created_by: form.created_by || undefined,
      values: buildRecordPayloadValues(selectedTemplate.value, fieldValues.value),
    });

    await router.push(`/records/${created.id}`);
  } catch (err) {
    console.error(err);
    error.value = "实验记录创建失败，请检查必填项。";
  } finally {
    submitting.value = false;
  }
}

watch(
  () => form.template_id,
  async (templateId, previousTemplateId) => {
    if (!templateId || templateId === previousTemplateId) return;
    try {
      await loadTemplate(templateId);
    } catch (err) {
      console.error(err);
      error.value = "模板加载失败。";
    }
  },
);

onMounted(loadPageData);
</script>

<template>
  <div class="page">
    <section class="page-hero">
      <div>
        <p class="eyebrow">新建记录</p>
        <h2>新建实验记录</h2>
        <p class="muted">新建记录默认保存为草稿，后续可提交审核、补充附件并查看历史快照。</p>
      </div>
    </section>

    <section class="card">
      <div class="section-header">
        <div>
          <h3>记录表单</h3>
          <p class="muted">表单内容由模板动态生成。</p>
        </div>
      </div>

      <div v-if="loading" class="muted">正在加载项目与模板...</div>

      <template v-else>
        <div class="form-item">
          <label class="label">记录标题</label>
          <input
            v-model="form.title"
            class="input"
            type="text"
            placeholder="例如：酸碱滴定实验记录（第一次）"
          />
        </div>

        <div class="grid-two">
          <div class="form-item">
            <label class="label">所属项目</label>
            <select v-model="form.project_id" class="input">
              <option value="">请选择项目</option>
              <option v-for="project in projects" :key="project.id" :value="project.id">{{ project.name }}</option>
            </select>
          </div>

          <div class="form-item">
            <label class="label">模板</label>
            <select v-model="form.template_id" class="input">
              <option value="">请选择模板</option>
              <option v-for="template in templates" :key="template.id" :value="template.id">
                {{ template.name }}（{{ template.category }} / v{{ template.version }}）
              </option>
            </select>
          </div>
        </div>

        <div class="form-item">
          <label class="label">初始状态</label>
          <div class="status-display">
            <span class="badge">{{ getRecordStatusLabel(initialStatus) }}</span>
            <p class="muted">状态流转请在记录详情页的流程面板中执行。</p>
          </div>
        </div>

        <div class="form-item">
          <label class="label">创建者 ID（可选）</label>
          <input v-model="form.created_by" class="input" type="text" placeholder="留空则使用当前登录用户" />
        </div>

        <div class="form-item">
          <label class="label">摘要</label>
          <textarea v-model="form.summary" class="textarea" rows="3" placeholder="简述实验目标、样品批次或当前结论" />
        </div>

        <DynamicTemplateForm v-model="fieldValues" :template="selectedTemplate" />

        <button class="button" :disabled="submitting || !selectedTemplate" @click="submitRecord">
          {{ submitting ? "提交中..." : "创建草稿记录" }}
        </button>

        <p v-if="error" class="error-text">{{ error }}</p>
      </template>
    </section>
  </div>
</template>

<style scoped>
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
