<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";

import { fetchAuditLogs } from "../api/audit";
import type { AuditLogItem } from "../types/api";

const props = withDefaults(
  defineProps<{
    title?: string;
    showFilters?: boolean;
    initialResourceType?: string;
    initialResourceId?: string;
  }>(),
  {
    title: "审计日志",
    showFilters: false,
    initialResourceType: "",
    initialResourceId: "",
  },
);

const loading = ref(false);
const error = ref("");
const logs = ref<AuditLogItem[]>([]);

const filters = reactive({
  q: "",
  resource_type: props.initialResourceType,
  resource_id: props.initialResourceId,
  actor_id: "",
  action: "",
  limit: 50,
});

function buildParams() {
  return {
    q: filters.q || undefined,
    resource_type: filters.resource_type || undefined,
    resource_id: filters.resource_id || undefined,
    actor_id: filters.actor_id || undefined,
    action: filters.action || undefined,
    limit: filters.limit || 50,
  };
}

async function loadLogs() {
  loading.value = true;
  error.value = "";

  try {
    logs.value = await fetchAuditLogs(buildParams());
  } catch (err: any) {
    console.error(err);
    error.value = err?.response?.data?.detail || "审计日志加载失败，请检查筛选条件或权限。";
  } finally {
    loading.value = false;
  }
}

function resetFilters() {
  filters.q = "";
  filters.resource_type = props.initialResourceType || "";
  filters.resource_id = props.initialResourceId || "";
  filters.actor_id = "";
  filters.action = "";
  filters.limit = 50;
  void loadLogs();
}

function formatTime(value: string) {
  return new Date(value).toLocaleString();
}

function formatDetail(value: unknown) {
  if (value === null || value === undefined) {
    return "";
  }
  return JSON.stringify(value, null, 2);
}

watch(
  [() => props.initialResourceType, () => props.initialResourceId],
  ([resourceType, resourceId]) => {
    filters.resource_type = resourceType || "";
    filters.resource_id = resourceId || "";
    void loadLogs();
  },
);

onMounted(() => {
  void loadLogs();
});
</script>

<template>
  <section class="card audit-panel">
    <div class="row-between" style="gap: 16px; align-items: flex-start;">
      <div>
        <h3>{{ title }}</h3>
        <p class="muted">{{ showFilters ? "支持关键词、资源、操作人和动作筛选。" : "展示当前资源的审计轨迹。" }}</p>
      </div>

      <div class="actions">
        <button v-if="showFilters" class="button secondary" type="button" @click="resetFilters">重置</button>
        <button class="button secondary" type="button" @click="loadLogs">刷新</button>
      </div>
    </div>

    <form v-if="showFilters" class="audit-filter-grid" @submit.prevent="loadLogs">
      <label class="form-item audit-filter-grid__search">
        <span>关键词</span>
        <input v-model="filters.q" type="text" placeholder="搜索摘要、动作、资源类型或操作人" />
      </label>

      <label class="form-item">
        <span>资源类型</span>
        <input v-model="filters.resource_type" type="text" placeholder="例如：record / project" />
      </label>

      <label class="form-item">
        <span>资源 ID</span>
        <input v-model="filters.resource_id" type="text" placeholder="UUID" />
      </label>

      <label class="form-item">
        <span>操作人 ID</span>
        <input v-model="filters.actor_id" type="text" placeholder="UUID" />
      </label>

      <label class="form-item">
        <span>动作</span>
        <input v-model="filters.action" type="text" placeholder="例如：record.update" />
      </label>

      <label class="form-item">
        <span>数量上限</span>
        <input v-model.number="filters.limit" type="number" min="1" max="200" />
      </label>

      <div class="audit-filter-actions">
        <button class="button" type="submit">查询</button>
      </div>
    </form>

    <p v-if="loading" class="muted">正在加载审计日志...</p>
    <p v-else-if="error" class="error-text">{{ error }}</p>

    <div v-else class="audit-log-list">
      <p v-if="logs.length === 0" class="empty-state">当前条件下没有审计日志。</p>

      <article v-for="item in logs" :key="item.id" class="audit-log-card">
        <div class="row-between" style="gap: 16px; align-items: flex-start;">
          <div>
            <strong>{{ item.summary }}</strong>
            <div class="audit-log-card__meta">
              <span class="badge">{{ item.action }}</span>
              <span class="muted">{{ item.resource_type }} / {{ item.resource_id || "无" }}</span>
            </div>
          </div>

          <div class="muted audit-log-card__actor">
            <div>{{ item.actor_username || item.actor_id || "系统" }}</div>
            <div>{{ formatTime(item.created_at) }}</div>
          </div>
        </div>

        <details v-if="item.detail_json" class="audit-log-card__details">
          <summary>查看详情 JSON</summary>
          <pre class="detail-value">{{ formatDetail(item.detail_json) }}</pre>
        </details>
      </article>
    </div>
  </section>
</template>

<style scoped>
.audit-panel,
.audit-log-list {
  display: grid;
  gap: 16px;
}

.audit-filter-grid {
  display: grid;
  grid-template-columns: minmax(260px, 1.3fr) repeat(4, minmax(0, 1fr)) minmax(110px, 140px) auto;
  gap: 12px;
  margin-top: 8px;
}

.audit-filter-grid__search {
  grid-column: span 1;
}

.audit-filter-actions {
  display: flex;
  align-items: end;
}

.audit-log-card {
  display: grid;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.94);
}

.audit-log-card__meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
  margin-top: 8px;
}

.audit-log-card__actor {
  text-align: right;
}

.audit-log-card__details summary {
  cursor: pointer;
  color: var(--accent-strong);
}

@media (max-width: 1100px) {
  .audit-filter-grid {
    grid-template-columns: 1fr;
  }

  .audit-log-card__actor {
    text-align: left;
  }
}
</style>
