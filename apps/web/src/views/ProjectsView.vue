<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { RouterLink } from "vue-router";

import { createProject, deleteProject, fetchProjects } from "../api/projects";
import type { ProjectItem } from "../types/api";

const loading = ref(false);
const submitting = ref(false);
const error = ref("");
const projects = ref<ProjectItem[]>([]);

const form = reactive({
  name: "",
  code: "",
  description: "",
  owner_id: "",
});

async function loadProjects() {
  loading.value = true;
  error.value = "";
  try {
    projects.value = await fetchProjects();
  } catch (err) {
    console.error(err);
    error.value = "项目列表加载失败。";
  } finally {
    loading.value = false;
  }
}

async function submitProject() {
  submitting.value = true;
  error.value = "";
  try {
    await createProject({
      name: form.name,
      code: form.code || undefined,
      description: form.description || undefined,
      owner_id: form.owner_id || undefined,
    });

    form.name = "";
    form.code = "";
    form.description = "";
    form.owner_id = "";

    await loadProjects();
  } catch (err) {
    console.error(err);
    error.value = "项目创建失败。请先确认开发用户已初始化。";
  } finally {
    submitting.value = false;
  }
}

async function removeProject(projectId: string) {
  const confirmed = window.confirm("确认删除该项目？若项目下已有记录将无法删除。");
  if (!confirmed) {
    return;
  }

  try {
    await deleteProject(projectId);
    await loadProjects();
  } catch (err) {
    console.error(err);
    error.value = "项目删除失败。";
  }
}

onMounted(loadProjects);
</script>

<template>
  <div class="page">
    <section class="card">
      <h2>创建项目</h2>
      <p class="muted">owner_id 可先留空，后端会自动选取第一个开发用户。</p>

      <div class="form-item">
        <label class="label">项目名称</label>
        <input v-model="form.name" class="input" type="text" placeholder="例如：基础化学实验课程" />
      </div>

      <div class="form-item">
        <label class="label">项目编码</label>
        <input v-model="form.code" class="input" type="text" placeholder="例如：CHEM-101" />
      </div>

      <div class="form-item">
        <label class="label">项目描述</label>
        <textarea v-model="form.description" class="textarea" rows="4" />
      </div>

      <div class="form-item">
        <label class="label">Owner ID（可选）</label>
        <input v-model="form.owner_id" class="input" type="text" placeholder="可留空" />
      </div>

      <button class="button" :disabled="submitting || !form.name.trim()" @click="submitProject">
        {{ submitting ? "创建中..." : "创建项目" }}
      </button>

      <p v-if="error" class="error-text">{{ error }}</p>
    </section>

    <section class="card">
      <div class="row-between">
        <h2>项目列表</h2>
        <RouterLink class="button secondary" to="/records/new">新建实验记录</RouterLink>
      </div>

      <p v-if="loading" class="muted">正在加载项目列表...</p>

      <div v-else-if="projects.length === 0" class="muted">
        暂无项目。
      </div>

      <div v-else class="stack">
        <article v-for="project in projects" :key="project.id" class="sub-card">
          <div class="row-between">
            <div>
              <h3>{{ project.name }}</h3>
              <p class="muted">编码：{{ project.code || "—" }}</p>
              <p class="muted">ID：{{ project.id }}</p>
            </div>

            <div class="actions">
              <RouterLink class="button secondary" :to="`/records/new?projectId=${project.id}`">
                基于此项目新建记录
              </RouterLink>
              <button class="button danger" @click="removeProject(project.id)">删除</button>
            </div>
          </div>

          <p>{{ project.description || "暂无描述" }}</p>
        </article>
      </div>
    </section>
  </div>
</template>