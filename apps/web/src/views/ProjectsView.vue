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
    error.value = "项目创建失败，请确认当前登录用户有权限。";
  } finally {
    submitting.value = false;
  }
}

async function removeProject(projectId: string) {
  const confirmed = window.confirm("确认删除该项目吗？若项目下已有记录，将无法删除。");
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
    <section class="page-hero">
      <div>
        <p class="eyebrow">Projects</p>
        <h2>项目工作台</h2>
        <p class="muted">先建立项目，再基于项目组织实验记录和模板使用范围。</p>
      </div>
      <RouterLink class="button" to="/records/new">新建实验记录</RouterLink>
    </section>

    <section class="card">
      <div class="section-header">
        <div>
          <h3>创建项目</h3>
          <p class="muted">`owner_id` 可留空，默认会使用当前登录用户。</p>
        </div>
      </div>

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
        <input v-model="form.owner_id" class="input" type="text" placeholder="默认当前用户" />
      </div>

      <button class="button" :disabled="submitting || !form.name.trim()" @click="submitProject">
        {{ submitting ? "创建中..." : "创建项目" }}
      </button>

      <p v-if="error" class="error-text">{{ error }}</p>
    </section>

    <section class="card">
      <div class="row-between">
        <h3>项目列表</h3>
        <RouterLink class="button secondary" to="/records/new">新建实验记录</RouterLink>
      </div>

      <p v-if="loading" class="muted">正在加载项目列表...</p>

      <div v-else-if="projects.length === 0" class="empty-state">
        暂无项目。
      </div>

      <div v-else class="stack">
        <article v-for="project in projects" :key="project.id" class="sub-card">
          <div class="row-between">
            <div>
              <h3>{{ project.name }}</h3>
              <p class="muted">编码：{{ project.code || "未设置" }}</p>
              <p class="muted">ID：{{ project.id }}</p>
            </div>

            <div class="actions">
              <RouterLink class="button secondary" :to="`/records/new?projectId=${project.id}`">
                基于该项目新建记录
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
