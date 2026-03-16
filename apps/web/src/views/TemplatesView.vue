<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";

import {
  createTemplate,
  deleteTemplate,
  fetchTemplateDetail,
  fetchTemplates,
  updateTemplate,
} from "../api/templates";
import type {
  ExperimentTemplateDetail,
  ExperimentTemplateSummary,
  TemplateSectionPayload,
} from "../types/api";

const templates = ref<ExperimentTemplateSummary[]>([]);
const selected = ref<ExperimentTemplateDetail | null>(null);
const loading = ref(false);
const saving = ref(false);
const error = ref("");
const sectionsText = ref("[]");

const form = reactive({
  id: "",
  name: "",
  key: "",
  description: "",
  category: "generic",
  parent_template_id: "",
  created_by: "",
  is_active: true,
});

function resetForm() {
  form.id = "";
  form.name = "";
  form.key = "";
  form.description = "";
  form.category = "generic";
  form.parent_template_id = "";
  form.created_by = "";
  form.is_active = true;
  sectionsText.value = "[]";
  selected.value = null;
}

function toEditableSections(template: ExperimentTemplateDetail): TemplateSectionPayload[] {
  return template.sections.map((section) => ({
    key: section.key,
    title: section.title,
    description: section.description ?? undefined,
    order_index: section.order_index,
    is_repeatable: section.is_repeatable,
    fields: section.fields.map((field) => ({
      key: field.key,
      label: field.label,
      field_type: field.field_type,
      required: field.required,
      order_index: field.order_index,
      placeholder: field.placeholder ?? undefined,
      help_text: field.help_text ?? undefined,
      default_value: field.default_value,
      options: field.options ?? undefined,
      validation_rules: field.validation_rules ?? undefined,
      ui_props: field.ui_props ?? undefined,
    })),
  }));
}

async function loadTemplates() {
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

async function loadTemplate(id: string) {
  error.value = "";
  try {
    const detail = await fetchTemplateDetail(id);
    selected.value = detail;

    form.id = detail.id;
    form.name = detail.name;
    form.key = detail.key;
    form.description = detail.description || "";
    form.category = detail.category;
    form.parent_template_id = detail.parent_template_id || "";
    form.is_active = detail.is_active;

    sectionsText.value = JSON.stringify(toEditableSections(detail), null, 2);
  } catch (err) {
    console.error(err);
    error.value = "模板详情加载失败。";
  }
}

function duplicateCurrent() {
  if (!selected.value) return;

  form.id = "";
  form.name = `${form.name}-副本`;
  form.key = `${form.key}-copy`;
}

async function saveTemplate() {
  saving.value = true;
  error.value = "";

  try {
    const sections = JSON.parse(sectionsText.value) as TemplateSectionPayload[];

    const payload = {
      name: form.name,
      key: form.key,
      description: form.description || undefined,
      category: form.category,
      parent_template_id: form.parent_template_id || undefined,
      created_by: form.created_by || undefined,
      is_active: form.is_active,
      sections,
    };

    let savedId = form.id;

    if (form.id) {
      const updated = await updateTemplate(form.id, {
        name: payload.name,
        key: payload.key,
        description: payload.description,
        category: payload.category,
        parent_template_id: payload.parent_template_id,
        is_active: payload.is_active,
        sections: payload.sections,
      });
      savedId = updated.id;
    } else {
      const created = await createTemplate(payload);
      savedId = created.id;
    }

    await loadTemplates();
    await loadTemplate(savedId);
  } catch (err) {
    console.error(err);
    error.value = "模板保存失败。请检查 JSON 结构、模板 key 是否重复，或是否试图修改系统模板。";
  } finally {
    saving.value = false;
  }
}

async function removeTemplate() {
  if (!form.id) return;
  const confirmed = window.confirm("确认删除该模板？");
  if (!confirmed) return;

  try {
    await deleteTemplate(form.id);
    resetForm();
    await loadTemplates();
  } catch (err) {
    console.error(err);
    error.value = "模板删除失败。系统模板或已被使用的模板不能删除。";
  }
}

onMounted(async () => {
  await loadTemplates();
});
</script>

<template>
  <div class="page" style="grid-template-columns: 320px 1fr;">
    <section class="card">
      <div class="row-between">
        <h2>模板列表</h2>
        <button class="button secondary" @click="resetForm">新建</button>
      </div>

      <p v-if="loading" class="muted">正在加载模板...</p>

      <div class="stack">
        <article
          v-for="item in templates"
          :key="item.id"
          class="sub-card"
          style="cursor:pointer;"
          @click="loadTemplate(item.id)"
        >
          <h3>{{ item.name }}</h3>
          <p class="muted">{{ item.key }}</p>
          <p class="muted">{{ item.category }} / v{{ item.version }}</p>
          <p class="muted">{{ item.is_system ? "系统模板" : "自定义模板" }}</p>
        </article>
      </div>
    </section>

    <section class="card">
      <div class="row-between">
        <h2>{{ form.id ? "编辑模板" : "新建模板" }}</h2>
        <div class="actions">
          <button class="button secondary" @click="duplicateCurrent" :disabled="!selected">
            复制当前
          </button>
          <button class="button" :disabled="saving || !form.name || !form.key" @click="saveTemplate">
            {{ saving ? "保存中..." : "保存模板" }}
          </button>
          <button class="button danger" :disabled="!form.id" @click="removeTemplate">删除</button>
        </div>
      </div>

      <p class="muted">第一版模板管理采用 JSON 结构编辑。系统模板建议先复制后再改。</p>

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
        <input v-model="form.parent_template_id" class="input" type="text" placeholder="可留空" />
      </div>

      <div class="form-item">
        <label class="label">创建人 ID（仅新建时可选）</label>
        <input v-model="form.created_by" class="input" type="text" placeholder="可留空" />
      </div>

      <div class="form-item">
        <label class="label">描述</label>
        <textarea v-model="form.description" class="textarea" rows="3" />
      </div>

      <div class="form-item">
        <label class="label">
          <input v-model="form.is_active" type="checkbox" />
          启用
        </label>
      </div>

      <div class="form-item">
        <label class="label">sections JSON</label>
        <textarea v-model="sectionsText" class="textarea" rows="24" />
      </div>

      <p v-if="error" class="error-text">{{ error }}</p>
    </section>
  </div>
</template>