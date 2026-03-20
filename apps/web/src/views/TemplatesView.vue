<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref, watchEffect } from "vue";

import TemplateAIGeneratorPanel from "../components/TemplateAIGeneratorPanel.vue";
import {
  createTemplate,
  createTemplateVersion,
  deleteTemplate,
  fetchTemplateDetail,
  fetchTemplateLineage,
  fetchTemplates,
  updateTemplate,
} from "../api/templates";
import { useAIStore } from "../stores/ai";
import type {
  ExperimentTemplateDetail,
  ExperimentTemplateSummary,
  TemplateCreatePayload,
  TemplateLineage,
  TemplateSectionPayload,
  TemplateUpdatePayload,
  TemplateVersionCreatePayload,
} from "../types/api";
import { buildTemplatePreset } from "../utils/templatePresets";

const aiStore = useAIStore();

const loading = ref(false);
const saving = ref(false);
const versioning = ref(false);
const deleting = ref(false);
const lineageLoading = ref(false);
const error = ref("");
const success = ref("");
const templates = ref<ExperimentTemplateSummary[]>([]);
const selectedTemplate = ref<ExperimentTemplateDetail | null>(null);
const lineage = ref<TemplateLineage | null>(null);

const form = reactive({
  id: "",
  name: "",
  key: "",
  category: "generic",
  parent_template_id: "",
  created_by: "",
  description: "",
  is_active: true,
});

const sectionsText = ref("[]");
const generatorSectionRef = ref<HTMLElement | null>(null);

watchEffect(() => {
  aiStore.setAssistantContext({
    title: "模板 AI 助手",
    description: "围绕当前模板结构、Sections JSON 和字段设计发起提问。",
    placeholder: "例如：请检查当前模板还缺哪些与实验追溯相关的字段，并给出修改建议。",
    task: "assistant",
    context: {
      page: "templates",
      template_id: form.id,
      template_name: form.name,
      template_key: form.key,
      category: form.category,
      description: form.description,
      sections_json: sectionsText.value,
    },
  });
});

onBeforeUnmount(() => {
  aiStore.resetAssistantContext();
});

function prettyJson(value: unknown) {
  return JSON.stringify(value, null, 2);
}

function resetForm() {
  form.id = "";
  form.name = "";
  form.key = "";
  form.category = "generic";
  form.parent_template_id = "";
  form.created_by = "";
  form.description = "";
  form.is_active = true;
  sectionsText.value = "[]";
  selectedTemplate.value = null;
  lineage.value = null;
  error.value = "";
  success.value = "";
}

function fillForm(detail: ExperimentTemplateDetail) {
  form.id = detail.id;
  form.name = detail.name;
  form.key = detail.key;
  form.category = detail.category;
  form.parent_template_id = detail.parent_template_id || "";
  form.created_by = "";
  form.description = detail.description || "";
  form.is_active = detail.is_active;
  sectionsText.value = prettyJson(
    detail.sections.map((section) => ({
      key: section.key,
      title: section.title,
      description: section.description,
      order_index: section.order_index,
      is_repeatable: section.is_repeatable,
      fields: section.fields.map((field) => ({
        key: field.key,
        label: field.label,
        field_type: field.field_type,
        required: field.required,
        order_index: field.order_index,
        placeholder: field.placeholder,
        help_text: field.help_text,
        default_value: field.default_value,
        options: field.options,
        validation_rules: field.validation_rules,
        ui_props: field.ui_props,
      })),
    })),
  );
}

function parseSections(): TemplateSectionPayload[] {
  const parsed = JSON.parse(sectionsText.value);
  if (!Array.isArray(parsed)) {
    throw new Error("Sections JSON 必须是数组。");
  }
  return parsed as TemplateSectionPayload[];
}

async function loadTemplatesList() {
  loading.value = true;
  error.value = "";
  try {
    templates.value = await fetchTemplates(false);
  } catch (err) {
    console.error(err);
    error.value = "模板列表加载失败。";
  } finally {
    loading.value = false;
  }
}

async function loadTemplateDetail(templateId: string) {
  error.value = "";
  success.value = "";
  lineageLoading.value = true;
  try {
    const detail = await fetchTemplateDetail(templateId);
    selectedTemplate.value = detail;
    fillForm(detail);
    lineage.value = await fetchTemplateLineage(templateId);
  } catch (err) {
    console.error(err);
    error.value = "模板详情加载失败。";
  } finally {
    lineageLoading.value = false;
  }
}

function applyPreset(kind: "generic" | "chemistry") {
  const preset = buildTemplatePreset(kind);
  form.id = "";
  form.name = preset.name;
  form.key = preset.key;
  form.category = preset.category;
  form.parent_template_id = "";
  form.description = preset.description;
  form.is_active = true;
  sectionsText.value = prettyJson(preset.sections);
  success.value = kind === "chemistry" ? "已载入化学实验模板预设。" : "已载入通用实验模板预设。";
  error.value = "";
}

function applyGeneratedSections(nextSectionsText: string) {
  sectionsText.value = nextSectionsText;
  success.value = "AI 生成结果已写入 Sections JSON 编辑区。";
  error.value = "";
}

function openAssistant() {
  aiStore.openAssistant();
}

async function focusGenerator() {
  await nextTick();
  generatorSectionRef.value?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function openGeneratorAssistant() {
  aiStore.openAssistant({
    prompt: "请根据当前模板名称、说明和已有 sections JSON，给我一版更完整的模板结构建议。",
  });
  void focusGenerator();
}

async function saveCurrentTemplate() {
  error.value = "";
  success.value = "";
  saving.value = true;

  try {
    const sections = parseSections();

    if (form.id) {
      const payload: TemplateUpdatePayload = {
        name: form.name,
        key: form.key,
        description: form.description || undefined,
        category: form.category,
        parent_template_id: form.parent_template_id || undefined,
        is_active: form.is_active,
        sections,
      };
      const detail = await updateTemplate(form.id, payload);
      selectedTemplate.value = detail;
      fillForm(detail);
      success.value = "模板已更新。";
    } else {
      const payload: TemplateCreatePayload = {
        name: form.name,
        key: form.key,
        description: form.description || undefined,
        category: form.category,
        parent_template_id: form.parent_template_id || undefined,
        created_by: form.created_by || undefined,
        is_active: form.is_active,
        sections,
      };
      const detail = await createTemplate(payload);
      selectedTemplate.value = detail;
      fillForm(detail);
      success.value = "模板已创建。";
    }

    await loadTemplatesList();
    if (selectedTemplate.value) {
      lineage.value = await fetchTemplateLineage(selectedTemplate.value.id);
    }
  } catch (err: any) {
    console.error(err);
    const detail = err?.response?.data?.detail;
    if (typeof detail === "string") {
      if (detail.includes("不能直接修改") || detail.includes("不可直接编辑")) {
        error.value = `${detail} 如需继续调整，请使用“派生新版本”。`;
      } else {
        error.value = detail;
      }
    } else if (err instanceof Error) {
      error.value = err.message;
    } else {
      error.value = "模板保存失败。";
    }
  } finally {
    saving.value = false;
  }
}

async function deriveNewVersion() {
  if (!selectedTemplate.value) return;

  error.value = "";
  success.value = "";
  versioning.value = true;
  try {
    const payload: TemplateVersionCreatePayload = {
      key: `${form.key}-vnext`,
      name: form.name,
      description: form.description || undefined,
      category: form.category,
      created_by: form.created_by || undefined,
      is_active: form.is_active,
      sections: parseSections(),
    };
    const detail = await createTemplateVersion(selectedTemplate.value.id, payload);
    selectedTemplate.value = detail;
    fillForm(detail);
    success.value = "已派生新的模板版本。";
    await loadTemplatesList();
    lineage.value = await fetchTemplateLineage(detail.id);
  } catch (err: any) {
    console.error(err);
    error.value = err?.response?.data?.detail || err?.message || "模板派生失败。";
  } finally {
    versioning.value = false;
  }
}

async function removeTemplate() {
  if (!selectedTemplate.value) return;

  error.value = "";
  success.value = "";
  deleting.value = true;
  try {
    await deleteTemplate(selectedTemplate.value.id);
    success.value = "模板已删除。";
    resetForm();
    await loadTemplatesList();
  } catch (err: any) {
    console.error(err);
    error.value = err?.response?.data?.detail || "模板删除失败。";
  } finally {
    deleting.value = false;
  }
}

function lineageItemLabel(item: ExperimentTemplateSummary) {
  return `${item.name} / ${item.key} / v${item.version}`;
}

onMounted(async () => {
  await loadTemplatesList();
  if (templates.value[0]) {
    await loadTemplateDetail(templates.value[0].id);
  } else {
    applyPreset("generic");
  }
});
</script>

<template>
  <div class="page">
    <section class="page-hero">
      <div>
        <h2>模板中心</h2>
        <p class="muted">支持模板版本管理、AI 辅助生成 Sections JSON，以及针对化学实验的字段扩展。</p>
      </div>
      <div class="actions">
        <button class="button secondary" type="button" @click="openAssistant">AI 助手</button>
        <button class="button secondary" type="button" @click="openGeneratorAssistant">AI 辅助生成</button>
        <button class="button secondary" type="button" @click="loadTemplatesList">刷新</button>
        <button class="button" type="button" @click="resetForm">新建模板</button>
      </div>
    </section>

    <div class="template-layout">
      <section class="card">
        <h3>模板列表</h3>
        <p v-if="loading" class="muted">正在加载模板...</p>
        <div v-else class="template-list">
          <button
            v-for="item in templates"
            :key="item.id"
            class="template-list-item"
            :class="{ active: selectedTemplate?.id === item.id }"
            type="button"
            @click="loadTemplateDetail(item.id)"
          >
            <strong>{{ item.name }}</strong>
            <div class="muted">{{ item.key }}</div>
            <div class="muted">{{ item.category }} / v{{ item.version }}</div>
          </button>
          <p v-if="templates.length === 0" class="muted">当前还没有模板。</p>
        </div>
      </section>

      <section class="card stack">
        <div class="row-between" style="align-items: flex-start; gap: 16px;">
          <div>
            <h3>{{ form.id ? "编辑模板" : "新建模板" }}</h3>
            <p class="muted">如果模板已经被实验记录使用，建议通过“派生新版本”继续演化，而不是直接改写历史模板。</p>
            <p v-if="selectedTemplate" class="muted">
              当前选中：{{ selectedTemplate.name }} / {{ selectedTemplate.key }} / v{{ selectedTemplate.version }}
            </p>
          </div>
          <div class="actions actions-wrap">
            <button class="button secondary" type="button" @click="applyPreset('generic')">载入通用预设</button>
            <button class="button secondary" type="button" @click="applyPreset('chemistry')">载入化学预设</button>
          </div>
        </div>

        <div class="form-grid two-col">
          <div class="form-item">
            <label class="label">模板名称</label>
            <input v-model="form.name" class="input" type="text" />
          </div>

          <div class="form-item">
            <label class="label">模板 key</label>
            <input v-model="form.key" class="input" type="text" />
          </div>

          <div class="form-item">
            <label class="label">分类</label>
            <input v-model="form.category" class="input" type="text" />
          </div>

          <div class="form-item">
            <label class="label">父模板 ID</label>
            <input v-model="form.parent_template_id" class="input" type="text" />
          </div>

          <div class="form-item">
            <label class="label">创建者 ID（新建或派生时可选）</label>
            <input v-model="form.created_by" class="input" type="text" />
          </div>

          <div class="form-item checkbox-holder">
            <label class="label checkbox-row">
              <input v-model="form.is_active" type="checkbox" />
              <span>启用模板</span>
            </label>
          </div>
        </div>

        <div class="form-item">
          <label class="label">模板说明</label>
          <textarea v-model="form.description" class="textarea" rows="3" />
        </div>

        <div class="preset-help card inner-card">
          <strong>字段建议</strong>
          <p class="muted">
            当前系统已经支持 chemical_equation 与 reaction_process 等化学字段，也支持 text、number、table、json、select、file 等常规字段类型。
          </p>
        </div>

        <section ref="generatorSectionRef" class="template-ai-generator-section">
          <div class="section-header">
            <div>
              <h3>AI 辅助生成</h3>
              <p class="muted">可基于当前模板名称、分类、说明和已有 Sections JSON，快速生成可直接应用的新结构。</p>
            </div>
            <button class="button secondary" type="button" @click="openGeneratorAssistant">在 AI 助手中继续讨论</button>
          </div>

          <TemplateAIGeneratorPanel
            :template-name="form.name"
            :template-key="form.key"
            :category="form.category"
            :description-text="form.description"
            :sections-text="sectionsText"
            @apply="applyGeneratedSections"
          />
        </section>

        <div class="form-item">
          <label class="label">Sections JSON</label>
          <textarea v-model="sectionsText" class="textarea code-area" rows="24" />
        </div>

        <div class="actions actions-wrap">
          <button class="button secondary" type="button" :disabled="!selectedTemplate || versioning" @click="deriveNewVersion">
            {{ versioning ? "派生中..." : "派生新版本" }}
          </button>
          <button class="button" type="button" :disabled="saving" @click="saveCurrentTemplate">
            {{ saving ? "保存中..." : "保存模板" }}
          </button>
          <button class="button danger" type="button" :disabled="!selectedTemplate || deleting" @click="removeTemplate">
            {{ deleting ? "删除中..." : "删除模板" }}
          </button>
        </div>

        <p v-if="success" class="muted">{{ success }}</p>
        <p v-if="error" class="error-text">{{ error }}</p>
      </section>
    </div>

    <section class="card">
      <div class="row-between" style="gap: 16px; align-items: flex-start;">
        <div>
          <h3>模板谱系</h3>
          <p class="muted">展示当前模板所在的版本链，便于查看父模板、当前版本和后续派生版本。</p>
        </div>
      </div>

      <p v-if="lineageLoading" class="muted">正在加载模板谱系...</p>
      <template v-else-if="lineage && lineage.items.length > 0">
        <div class="lineage-list">
          <div v-for="item in lineage.items" :key="item.id" class="lineage-item">
            <div class="row-between" style="gap: 16px; align-items: flex-start;">
              <div>
                <strong>{{ lineageItemLabel(item) }}</strong>
                <div class="muted">父模板：{{ item.parent_template_id || "无" }}</div>
              </div>
              <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                <span v-if="item.id === lineage.root_template_id" class="muted">根模板</span>
                <span v-if="item.id === lineage.current_template_id" class="muted">当前模板</span>
                <button class="button secondary" type="button" @click="loadTemplateDetail(item.id)">查看</button>
              </div>
            </div>
          </div>
        </div>
      </template>
      <p v-else class="muted">当前没有可展示的模板谱系信息。</p>
    </section>
  </div>
</template>

<style scoped>
.template-layout {
  display: grid;
  grid-template-columns: minmax(240px, 320px) minmax(0, 1fr);
  gap: 16px;
}

.template-list {
  display: grid;
  gap: 10px;
}

.template-list-item {
  text-align: left;
  border: 1px solid var(--color-border, #d9dce3);
  border-radius: 12px;
  padding: 12px;
  background: white;
  cursor: pointer;
}

.template-list-item.active {
  border-color: var(--color-primary, #ef476f);
  background: rgba(239, 71, 111, 0.06);
}

.form-grid.two-col {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.actions-wrap {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.checkbox-holder {
  display: flex;
  align-items: end;
}

.checkbox-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.template-ai-generator-section {
  display: grid;
  gap: 16px;
}

.code-area {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.inner-card {
  margin: 8px 0 12px;
}

.lineage-list {
  display: grid;
  gap: 10px;
  margin-top: 12px;
}

.lineage-item {
  border: 1px solid var(--color-border, #d9dce3);
  border-radius: 12px;
  padding: 14px;
}

@media (max-width: 960px) {
  .template-layout {
    grid-template-columns: 1fr;
  }
}
</style>
