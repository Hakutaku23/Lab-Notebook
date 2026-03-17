<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";

import {
  createTemplate,
  createTemplateVersion,
  deleteTemplate,
  fetchTemplateDetail,
  fetchTemplateLineage,
  fetchTemplates,
  updateTemplate,
} from "../api/templates";

import type {
  ExperimentTemplateDetail,
  ExperimentTemplateSummary,
  TemplateLineage,
  TemplateSection,
  TemplateSectionPayload,
} from "../types/api";

const templates = ref<ExperimentTemplateSummary[]>([]);
const selectedTemplate = ref<ExperimentTemplateDetail | null>(null);
const lineage = ref<TemplateLineage | null>(null);

const loading = ref(false);
const detailLoading = ref(false);
const lineageLoading = ref(false);
const saving = ref(false);
const versioning = ref(false);

const error = ref("");
const success = ref("");
const sectionsText = ref("[]");

const form = reactive({
  id: "",
  name: "",
  key: "",
  category: "generic",
  description: "",
  parent_template_id: "",
  created_by: "",
  is_active: true,
});

function clearMessages() {
  error.value = "";
  success.value = "";
}

function serializeSections(sections: TemplateSection[]): string {
  const payload: TemplateSectionPayload[] = sections.map((section) => ({
    key: section.key,
    title: section.title,
    description: section.description ?? null,
    order_index: section.order_index,
    is_repeatable: section.is_repeatable,
    fields: section.fields.map((field) => ({
      key: field.key,
      label: field.label,
      field_type: field.field_type,
      required: field.required,
      order_index: field.order_index,
      placeholder: field.placeholder ?? null,
      help_text: field.help_text ?? null,
      default_value: field.default_value ?? null,
      options: field.options ?? null,
      validation_rules: field.validation_rules ?? null,
      ui_props: field.ui_props ?? null,
    })),
  }));

  return JSON.stringify(payload, null, 2);
}

function resetForm() {
  selectedTemplate.value = null;
  lineage.value = null;
  form.id = "";
  form.name = "";
  form.key = "";
  form.category = "generic";
  form.description = "";
  form.parent_template_id = "";
  form.created_by = "";
  form.is_active = true;
  sectionsText.value = "[]";
}

function applyTemplate(detail: ExperimentTemplateDetail) {
  selectedTemplate.value = detail;
  form.id = detail.id;
  form.name = detail.name;
  form.key = detail.key;
  form.category = detail.category;
  form.description = detail.description ?? "";
  form.parent_template_id = detail.parent_template_id ?? "";
  form.created_by = "";
  form.is_active = detail.is_active;
  sectionsText.value = serializeSections(detail.sections);
}

function buildCopyKey(baseKey: string) {
  return `${baseKey}-copy-${Date.now().toString().slice(-4)}`;
}

function buildVersionKey(baseKey: string, versionNo: number) {
  const value = baseKey.trim();
  if (/[-_]v\d+$/i.test(value)) {
    return value.replace(/[-_]v\d+$/i, `-v${versionNo}`);
  }
  return `${value}-v${versionNo}`;
}

function parseSections(): TemplateSectionPayload[] {
  const parsed = JSON.parse(sectionsText.value || "[]");

  if (!Array.isArray(parsed)) {
    throw new Error("分区 JSON 配置必须是数组。");
  }

  return parsed as TemplateSectionPayload[];
}

function shouldCreateVersion(errorLike: any) {
  const status = errorLike?.response?.status;
  const detail = String(errorLike?.response?.data?.detail ?? "");
  return status === 409 || detail.includes("template_requires_version");
}

async function createVersionFromCurrentForm() {
  if (!selectedTemplate.value) {
    throw new Error("请先选择一个模板。")
  }

  const source = selectedTemplate.value;
  const sections = parseSections();
  const nextVersion = source.version + 1;

  return createTemplateVersion(source.id, {
    key: buildVersionKey(form.key || source.key, nextVersion),
    name: `${form.name || source.name} v${nextVersion}`,
    description: form.description || source.description || null,
    category: form.category || source.category,
    is_active: form.is_active,
    sections,
  });
}

async function loadLineage(templateId: string) {
  lineageLoading.value = true;

  try {
    lineage.value = await fetchTemplateLineage(templateId);
  } catch (err) {
    console.error(err);
    lineage.value = null;
  } finally {
    lineageLoading.value = false;
  }
}

async function loadTemplates(preferredId = "") {
  loading.value = true;

  try {
    templates.value = await fetchTemplates(true);

    const targetId =
      preferredId ||
      (selectedTemplate.value &&
      templates.value.some((item) => item.id === selectedTemplate.value?.id)
        ? selectedTemplate.value.id
        : templates.value[0]?.id);

    if (targetId) {
      await loadTemplateDetail(targetId);
    } else if (!form.id) {
      resetForm();
    }
  } catch (err: any) {
    error.value = err?.response?.data?.detail || "模板列表加载失败。";
  } finally {
    loading.value = false;
  }
}

async function loadTemplateDetail(templateId: string) {
  detailLoading.value = true;
  clearMessages();

  try {
    const detail = await fetchTemplateDetail(templateId);
    applyTemplate(detail);
    await loadLineage(templateId);
  } catch (err: any) {
    error.value = err?.response?.data?.detail || "模板详情加载失败。";
  } finally {
    detailLoading.value = false;
  }
}

function handleCreateNew() {
  clearMessages();
  resetForm();
}

function handleCopyCurrent() {
  if (!selectedTemplate.value) {
    error.value = "请先选择一个模板。";
    return;
  }

  clearMessages();

  const source = selectedTemplate.value;
  form.id = "";
  form.name = `${source.name} 副本`;
  form.key = buildCopyKey(source.key);
  form.category = source.category;
  form.description = source.description ?? "";
  form.parent_template_id = source.id;
  form.created_by = "";
  form.is_active = source.is_active;
  sectionsText.value = serializeSections(source.sections);

  success.value = "已复制到编辑表单，保存后会创建一个新模板。";
}

async function handleSave() {
  clearMessages();
  saving.value = true;

  try {
    const sections = parseSections();

    if (form.id) {
      try {
        const updated = await updateTemplate(form.id, {
          name: form.name.trim(),
          key: form.key.trim(),
          description: form.description.trim() || "",
          category: form.category.trim() || "generic",
          parent_template_id: form.parent_template_id.trim() || null,
          is_active: form.is_active,
          sections,
        });

        success.value = "模板已更新。";
        await loadTemplates(updated.id);
      } catch (err: any) {
        if (!shouldCreateVersion(err) || !selectedTemplate.value) {
          throw err;
        }

        const created = await createVersionFromCurrentForm();
        success.value = `当前模板不可直接修改，已自动派生新版本：${created.name}`;
        await loadTemplates(created.id);
      }
    } else {
      const created = await createTemplate({
        name: form.name.trim(),
        key: form.key.trim(),
        description: form.description.trim() || "",
        category: form.category.trim() || "generic",
        parent_template_id: form.parent_template_id.trim() || null,
        created_by: form.created_by.trim() || undefined,
        is_active: form.is_active,
        sections,
      });

      success.value = "模板已创建。";
      await loadTemplates(created.id);
    }
  } catch (err: any) {
    error.value =
      err?.response?.data?.detail ||
      err?.message ||
      "模板保存失败。";
  } finally {
    saving.value = false;
  }
}

async function handleCreateVersion() {
  if (!selectedTemplate.value) {
    error.value = "请先选择一个模板。";
    return;
  }

  clearMessages();
  versioning.value = true;

  try {
    const created = await createVersionFromCurrentForm();
    success.value = `已创建新版本：${created.name}`;
    await loadTemplates(created.id);
  } catch (err: any) {
    error.value =
      err?.response?.data?.detail ||
      err?.message ||
      "模板新版本创建失败。";
  } finally {
    versioning.value = false;
  }
}

async function handleDelete() {
  if (!form.id) {
    return;
  }

  const confirmed = window.confirm("确认删除当前模板？此操作不可撤销。");
  if (!confirmed) {
    return;
  }

  clearMessages();
  saving.value = true;

  try {
    await deleteTemplate(form.id);
    success.value = "模板已删除。";
    resetForm();
    await loadTemplates();
  } catch (err: any) {
    error.value =
      err?.response?.data?.detail || "模板删除失败。";
  } finally {
    saving.value = false;
  }
}

function lineageItemLabel(item: ExperimentTemplateSummary) {
  return `${item.name} / ${item.key} / v${item.version}`;
}

onMounted(async () => {
  await loadTemplates();
});
</script>

<template>
  <div class="page">
    <section class="page-header">
      <div>
        <h2>模板中心</h2>
        <p class="muted">
          当前版本支持模板派生、版本谱系查看，以及基于现有模板快速创建新版本。
        </p>
      </div>

      <div class="actions">
        <button class="button secondary" type="button" @click="loadTemplates(selectedTemplate?.id || '')">
          刷新
        </button>
        <button class="button" type="button" @click="handleCreateNew">
          新建
        </button>
      </div>
    </section>

    <section class="template-layout">
      <section class="card">
        <h3>模板列表</h3>
        <p v-if="loading" class="muted">正在加载模板...</p>

        <div v-else class="stack-gap">
          <button
            v-for="item in templates"
            :key="item.id"
            type="button"
            class="button secondary template-list-button"
            @click="loadTemplateDetail(item.id)"
          >
            <span>
              <strong>{{ item.name }}</strong>
              <span class="muted template-meta">{{ item.key }}</span>
            </span>
            <span class="muted">{{ item.category }} / v{{ item.version }}</span>
          </button>

          <p v-if="templates.length === 0" class="muted">
            当前没有模板。
          </p>
        </div>
      </section>

      <div class="stack-gap">
        <section class="card">
          <div class="row-between" style="gap: 16px; align-items: flex-start;">
            <div>
              <h3>{{ form.id ? "编辑模板" : "新建模板" }}</h3>
              <p class="muted">
                当模板已被实验记录使用时，系统会自动派生新版本，而不是直接覆盖旧模板。
              </p>
              <p v-if="selectedTemplate" class="muted">
                当前选中：{{ selectedTemplate.name }} / {{ selectedTemplate.key }} / v{{ selectedTemplate.version }}
              </p>
            </div>

            <div class="actions" style="flex-wrap: wrap;">
              <button
                class="button secondary"
                type="button"
                :disabled="!selectedTemplate"
                @click="handleCopyCurrent"
              >
                复制当前模板
              </button>

              <button
                class="button secondary"
                type="button"
                :disabled="!selectedTemplate || versioning"
                @click="handleCreateVersion"
              >
                {{ versioning ? "派生中..." : "派生新版本" }}
              </button>

              <button class="button" type="button" :disabled="saving" @click="handleSave">
                {{ saving ? "保存中..." : "保存模板" }}
              </button>

              <button
                class="button secondary"
                type="button"
                :disabled="!form.id || saving"
                @click="handleDelete"
              >
                删除
              </button>
            </div>
          </div>

          <p v-if="detailLoading" class="muted">正在加载模板详情...</p>

          <div class="stack-gap">
            <div class="form-item">
              <label class="label">模板名称</label>
              <input v-model="form.name" class="input" type="text" />
            </div>

            <div class="form-item">
              <label class="label">模板键</label>
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

            <div class="form-item" v-if="!form.id">
              <label class="label">创建者 ID（仅新建时可选）</label>
              <input v-model="form.created_by" class="input" type="text" />
            </div>

            <div class="form-item">
              <label class="label">描述</label>
              <textarea v-model="form.description" class="textarea" rows="4" />
            </div>

            <label class="checkbox-field">
              <input v-model="form.is_active" type="checkbox" />
              <span>启用模板</span>
            </label>

            <div class="form-item">
              <label class="label">分区 JSON 配置</label>
              <textarea v-model="sectionsText" class="textarea" rows="24" />
            </div>
          </div>

          <p v-if="success" style="margin-top: 12px;">{{ success }}</p>
          <p v-if="error" class="error-text">{{ error }}</p>
        </section>

        <section class="card">
          <div class="row-between" style="gap: 16px; align-items: flex-start;">
            <div>
              <h3>模板谱系</h3>
              <p class="muted">
                展示当前模板所在版本链，可快速识别根模板、当前模板和后续版本。
              </p>
            </div>
          </div>

          <p v-if="lineageLoading" class="muted">正在加载模板谱系...</p>

          <template v-else-if="lineage && lineage.items.length > 0">
            <div class="stack-gap" style="margin-top: 12px;">
              <div
                v-for="item in lineage.items"
                :key="item.id"
                class="card"
                style="padding: 14px; margin: 0;"
              >
                <div class="row-between" style="gap: 16px; align-items: flex-start;">
                  <div>
                    <strong>{{ lineageItemLabel(item) }}</strong>
                    <div class="muted">
                      父模板：{{ item.parent_template_id || "无" }}
                    </div>
                  </div>

                  <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                    <span v-if="item.id === lineage.root_template_id" class="muted">根模板</span>
                    <span v-if="item.id === lineage.current_template_id" class="muted">当前模板</span>
                    <button class="button secondary" type="button" @click="loadTemplateDetail(item.id)">
                      查看
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </template>

          <p v-else class="muted" style="margin-top: 12px;">
            当前没有可展示的谱系信息。
          </p>
        </section>
      </div>
    </section>
  </div>
</template>
