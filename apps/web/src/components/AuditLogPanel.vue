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
  resource_type: props.initialResourceType,
  resource_id: props.initialResourceId,
  actor_id: "",
  action: "",
  limit: 50,
});

function buildParams() {
  return {
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
    error.value =
      err?.response?.data?.detail || "审计日志加载失败，请检查筛选条件或权限。";
  } finally {
    loading.value = false;
  }
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
  <section class="card">
    <div class="row-between" style="gap: 16px; align-items: flex-start;">
      <div>
        <h3>{{ title }}</h3>
        <p class="muted">
          {{ showFilters ? "支持按资源、操作人和动作筛选。" : "当前资源的审计轨迹。" }}
        </p>
      </div>

      <button class="button secondary" type="button" @click="loadLogs">
        刷新
      </button>
    </div>

    <form
      v-if="showFilters"
      style="
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 12px;
        margin-top: 16px;
      "
      @submit.prevent="loadLogs"
    >
      <label style="display: grid; gap: 6px;">
        <span>资源类型</span>
        <input v-model="filters.resource_type" type="text" placeholder="如：record / project" />
      </label>

      <label style="display: grid; gap: 6px;">
        <span>资源 ID</span>
        <input v-model="filters.resource_id" type="text" placeholder="UUID" />
      </label>

      <label style="display: grid; gap: 6px;">
        <span>操作人 ID</span>
        <input v-model="filters.actor_id" type="text" placeholder="UUID" />
      </label>

      <label style="display: grid; gap: 6px;">
        <span>动作</span>
        <input v-model="filters.action" type="text" placeholder="如：record.updated" />
      </label>

      <label style="display: grid; gap: 6px;">
        <span>数量上限</span>
        <input v-model.number="filters.limit" type="number" min="1" max="200" />
      </label>

      <div style="display: flex; align-items: end;">
        <button class="button" type="submit">查询</button>
      </div>
    </form>

    <p v-if="loading" class="muted" style="margin-top: 16px;">
      正在加载审计日志...
    </p>

    <p v-else-if="error" class="error-text" style="margin-top: 16px;">
      {{ error }}
    </p>

    <div v-else style="display: grid; gap: 12px; margin-top: 16px;">
      <p v-if="logs.length === 0" class="muted">当前条件下没有审计日志。</p>

      <article
        v-for="item in logs"
        :key="item.id"
        class="card"
        style="padding: 16px; margin: 0;"
      >
        <div class="row-between" style="gap: 16px; align-items: flex-start;">
          <div>
            <strong>{{ item.action }}</strong>
            <div class="muted">{{ formatTime(item.created_at) }}</div>
          </div>

          <div class="muted" style="text-align: right;">
            操作人：{{ item.actor_username || item.actor_id || "系统" }}
          </div>
        </div>

        <div class="muted" style="margin-top: 8px;">
          资源：{{ item.resource_type }} / {{ item.resource_id || "—" }}
        </div>

        <p style="margin: 8px 0 0;">{{ item.summary }}</p>

        <details v-if="item.detail_json" style="margin-top: 10px;">
          <summary>详情 JSON</summary>
          <pre class="detail-value" style="margin-top: 8px;">{{ formatDetail(item.detail_json) }}</pre>
        </details>
      </article>
    </div>
  </section>
</template>