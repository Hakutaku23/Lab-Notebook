<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
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
  project_id: "",
  template_id: "",
  status: "",
});

async function loadOptions() {
  const [projectData, templateData] = await Promise.all([
    fetchProjects(),
    fetchTemplates(),
  ]);
  projects.value = projectData;
  templates.value = templateData;
}

async function loadRecords() {
  loading.value = true;
  error.value = "";
  try {
    records.value = await fetchRecords({
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
        <h2>实验记录</h2>
        <p class="muted">按项目、模板和状态筛选记录，快速进入详情和编辑流程。</p>
      </div>
      <RouterLink class="button" to="/records/new">新建实验记录</RouterLink>
    </section>

    <section class="card">
      <div class="row-between">
        <h3>记录列表</h3>
        <RouterLink class="button secondary" to="/records/new">新建实验记录</RouterLink>
      </div>

      <div class="filters">
        <div class="form-item">
          <label class="label">项目筛选</label>
          <select v-model="filters.project_id" class="input">
            <option value="">全部项目</option>
            <option v-for="project in projects" :key="project.id" :value="project.id">
              {{ project.name }}
            </option>
          </select>
        </div>

        <div class="form-item">
          <label class="label">模板筛选</label>
          <select v-model="filters.template_id" class="input">
            <option value="">全部模板</option>
            <option v-for="template in templates" :key="template.id" :value="template.id">
              {{ template.name }}
            </option>
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

      <button class="button secondary" @click="loadRecords">应用筛选</button>

      <p v-if="error" class="error-text">{{ error }}</p>
      <p v-if="loading" class="muted">正在加载实验记录...</p>

      <div v-else-if="records.length === 0" class="empty-state">
        暂无实验记录。
      </div>

      <div v-else class="stack">
        <article v-for="record in records" :key="record.id" class="sub-card">
          <div class="row-between">
            <div>
              <h3>{{ record.title }}</h3>
              <p class="muted">项目：{{ record.project_name || record.project_id }}</p>
              <p class="muted">模板：{{ record.template_name || record.template_id }}</p>
              <p class="muted">状态：{{ getRecordStatusLabel(record.status) }}</p>
            </div>

            <div class="actions">
              <RouterLink class="button secondary" :to="`/records/${record.id}`">查看详情</RouterLink>
              <button class="button danger" @click="removeRecord(record.id)">删除</button>
            </div>
          </div>

          <p>{{ record.summary || "暂无摘要" }}</p>
        </article>
      </div>
    </section>
  </div>
</template>
