<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { RouterLink } from "vue-router";

import { fetchProjects } from "../api/projects";
import { deleteRecord, fetchRecords } from "../api/records";
import { fetchTemplates } from "../api/templates";
import type {
  ExperimentRecordSummary,
  ExperimentTemplateSummary,
  ProjectItem,
} from "../types/api";
import { getRecordStatusLabel } from "../utils/record-status";

const loading = ref(false);
const error = ref("");

const records = ref<ExperimentRecordSummary[]>([]);
const projects = ref<ProjectItem[]>([]);
const templates = ref<ExperimentTemplateSummary[]>([]);

const filters = reactive({
  q: "",
  project_id: "",
  template_id: "",
  status: "",
});

const activeFilterCount = computed(() => {
  return [filters.q, filters.project_id, filters.template_id, filters.status].filter(Boolean).length;
});

function formatTime(value: string) {
  return new Date(value).toLocaleString();
}

async function loadOptions() {
  const [projectData, templateData] = await Promise.all([fetchProjects(), fetchTemplates()]);
  projects.value = projectData;
  templates.value = templateData;
}

async function loadRecords() {
  loading.value = true;
  error.value = "";
  try {
    records.value = await fetchRecords({
      q: filters.q || undefined,
      project_id: filters.project_id || undefined,
      template_id: filters.template_id || undefined,
      status: filters.status || undefined,
    });
  } catch (err) {
    console.error(err);
    error.value = "实验记录列表加载失败。";
  } finally {
    loading.value = false;
  }
}

function resetFilters() {
  filters.q = "";
  filters.project_id = "";
  filters.template_id = "";
  filters.status = "";
  void loadRecords();
}

async function removeRecord(recordId: string) {
  const confirmed = window.confirm("确认删除该实验记录吗？");
  if (!confirmed) {
    return;
  }

  try {
    await deleteRecord(recordId);
    await loadRecords();
  } catch (err) {
    console.error(err);
    error.value = "实验记录删除失败。";
  }
}

onMounted(async () => {
  try {
    await loadOptions();
    await loadRecords();
  } catch (err) {
    console.error(err);
    error.value = "页面初始化失败。";
  }
});
</script>

<template>
  <div class="page">
    <section class="page-hero">
      <div>
        <p class="eyebrow">实验记录</p>
        <h2>实验记录检索</h2>
        <p class="muted">按关键词、项目、模板和状态筛选记录，快速进入详情、审核与打印流程。</p>
      </div>
      <div class="actions">
        <RouterLink class="button secondary" to="/projects">返回项目</RouterLink>
        <RouterLink class="button" to="/records/new">新建实验记录</RouterLink>
      </div>
    </section>

    <section class="card records-filter-card">
      <div class="section-header">
        <div>
          <h3>筛选条件</h3>
          <p class="muted">当前已启用 {{ activeFilterCount }} 个筛选条件。</p>
        </div>
        <div class="actions">
          <button class="button secondary" type="button" @click="resetFilters">重置筛选</button>
          <button class="button" type="button" @click="loadRecords">开始检索</button>
        </div>
      </div>

      <div class="records-filter-grid">
        <div class="form-item records-filter-grid__search">
          <label class="label">关键词</label>
          <input v-model="filters.q" class="input" type="text" placeholder="搜索标题或摘要中的关键词" />
        </div>

        <div class="form-item">
          <label class="label">项目</label>
          <select v-model="filters.project_id" class="input">
            <option value="">全部项目</option>
            <option v-for="project in projects" :key="project.id" :value="project.id">{{ project.name }}</option>
          </select>
        </div>

        <div class="form-item">
          <label class="label">模板</label>
          <select v-model="filters.template_id" class="input">
            <option value="">全部模板</option>
            <option v-for="template in templates" :key="template.id" :value="template.id">{{ template.name }}</option>
          </select>
        </div>

        <div class="form-item">
          <label class="label">状态</label>
          <select v-model="filters.status" class="input">
            <option value="">全部状态</option>
            <option value="draft">{{ getRecordStatusLabel("draft") }}</option>
            <option value="submitted">{{ getRecordStatusLabel("submitted") }}</option>
            <option value="approved">{{ getRecordStatusLabel("approved") }}</option>
          </select>
        </div>
      </div>

      <p v-if="error" class="error-text">{{ error }}</p>
    </section>

    <section class="card">
      <div class="row-between records-list-header">
        <div>
          <h3>检索结果</h3>
          <p class="muted">共 {{ records.length }} 条记录。</p>
        </div>
      </div>

      <p v-if="loading" class="muted">正在加载实验记录...</p>
      <div v-else-if="records.length === 0" class="empty-state">当前条件下没有实验记录。</div>

      <div v-else class="records-list-grid">
        <article v-for="record in records" :key="record.id" class="record-card">
          <div class="row-between" style="align-items: flex-start; gap: 16px;">
            <div>
              <h3>{{ record.title }}</h3>
              <div class="record-card__meta">
                <span class="badge">{{ getRecordStatusLabel(record.status) }}</span>
                <span class="muted">{{ record.project_name || record.project_id }}</span>
                <span class="muted">{{ record.template_name || record.template_id }}</span>
              </div>
            </div>
            <div class="muted">{{ formatTime(record.updated_at) }}</div>
          </div>

          <p class="record-card__summary">{{ record.summary || "暂无摘要" }}</p>

          <div class="actions record-card__actions">
            <RouterLink class="button secondary" :to="`/records/${record.id}`">查看详情</RouterLink>
            <RouterLink class="button secondary" :to="`/records/${record.id}/edit`">继续编辑</RouterLink>
            <button class="button danger" @click="removeRecord(record.id)">删除</button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<style scoped>
.records-filter-card,
.records-list-grid {
  display: grid;
  gap: 16px;
}

.records-filter-grid {
  display: grid;
  grid-template-columns: minmax(260px, 1.3fr) repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.records-filter-grid__search {
  grid-column: span 1;
}

.records-list-header {
  align-items: center;
}

.record-card {
  display: grid;
  gap: 14px;
  padding: 18px;
  border: 1px solid var(--border);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.94);
}

.record-card__meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}

.record-card__summary {
  margin: 0;
  color: var(--text);
}

.record-card__actions {
  justify-content: flex-start;
}

@media (max-width: 960px) {
  .records-filter-grid {
    grid-template-columns: 1fr;
  }
}
</style>
