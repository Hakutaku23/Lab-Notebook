<script setup lang="ts">
import { onBeforeUnmount, onMounted, reactive, ref, watchEffect } from "vue";
import { RouterLink } from "vue-router";

import { createProject, deleteProject, fetchProjects } from "../api/projects";
import { useAIStore } from "../stores/ai";
import type { ProjectItem } from "../types/api";

const aiStore = useAIStore();

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


watchEffect(() => {
  aiStore.setAssistantContext({
    title: "项目 AI 助手",
    description: "结合当前项目列表和新建表单，辅助梳理项目命名、描述和后续记录组织方式。",
    placeholder: "例如：请根据当前项目信息，帮我优化项目描述，并建议适合的实验记录模板分类。",
    task: "assistant",
    context: {
      page: "projects",
      draft_project: {
        name: form.name,
        code: form.code,
        description: form.description,
        owner_id: form.owner_id,
      },
      projects: projects.value.map((project) => ({
        id: project.id,
        name: project.name,
        code: project.code || "",
        description: project.description || "",
      })),
    },
  });
});

onBeforeUnmount(() => {
  aiStore.resetAssistantContext();
});

function openAssistant() {
  aiStore.openAssistant({
    prompt: "请根据当前项目列表和我正在填写的项目信息，给出命名、描述和后续实验记录组织建议。",
  });
}

onMounted(loadProjects);
</script>

<template>
  <div class="page">
    <section class="page-hero">
      <div>
        <p class="eyebrow">项目管理</p>
        <h2>项目工作台</h2>
        <p class="muted">先建立项目，再基于项目组织实验记录和模板使用范围。</p>
      </div>
      <div class="actions">
        <button class="button secondary" type="button" @click="openAssistant">AI 助手</button>
        <RouterLink class="button" to="/records/new">新建实验记录</RouterLink>
      </div>
    </section>

    <section class="card">
      <div class="section-header">
        <div>
          <h3>AI 规划入口</h3>
          <p class="muted">可让 AI 帮你梳理项目命名、项目描述，以及应该优先配套哪些实验记录模板。</p>
        </div>
        <button class="button secondary" type="button" @click="openAssistant">立即提问</button>
      </div>
    </section>

    <section class="card">
      <div class="section-header">
        <div>
          <h3>创建项目</h3>
          <p class="muted">负责人 ID 可留空，默认会使用当前登录用户。</p>
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
        <label class="label">负责人 ID（可选）</label>
        <input v-model="form.owner_id" class="input" type="text" placeholder="留空则使用当前用户" />
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
              <p class="muted">项目 ID：{{ project.id }}</p>
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
