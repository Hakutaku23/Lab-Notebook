<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { fetchAuditLogs } from "../api/audit";
import { transitionRecordWorkflow } from "../api/records";
import type {
  AuditLogItem,
  ExperimentRecordDetail,
  RecordWorkflowAction,
} from "../types/api";
import { getRecordStatusLabel } from "../utils/record-status";

const props = defineProps<{
  record: ExperimentRecordDetail;
}>();

const emit = defineEmits<{
  changed: [ExperimentRecordDetail];
}>();

const comment = ref("");
const loadingAction = ref<RecordWorkflowAction | "">("");
const timelineLoading = ref(false);
const error = ref("");
const timelineError = ref("");
const successText = ref("");
const timelineItems = ref<AuditLogItem[]>([]);

const actions = computed(() => props.record.allowed_actions || []);
const isEditable = computed(() => props.record.status === "draft");

function actionLabel(action: RecordWorkflowAction) {
  switch (action) {
    case "submit":
      return "提交审核";
    case "withdraw":
      return "撤回为草稿";
    case "approve":
      return "审核通过";
    case "reopen":
      return "重新打开";
    default:
      return action;
  }
}

function actionDescription(action: RecordWorkflowAction) {
  switch (action) {
    case "submit":
      return "提交后正文将锁定，等待审核。";
    case "withdraw":
      return "撤回后可重新编辑记录内容。";
    case "approve":
      return "通过后记录进入已审核状态。";
    case "reopen":
      return "重新打开后记录回到草稿状态。";
    default:
      return "";
  }
}

function statusHint(status: string) {
  switch (status) {
    case "draft":
      return "当前仍可继续编辑正文，也可以提交审核。";
    case "submitted":
      return "正文已锁定，等待项目负责人或管理员审核。";
    case "approved":
      return "记录已通过审核；如需继续修改，请先重新打开为草稿。";
    default:
      return "当前状态暂未定义。";
  }
}

function lockDescription(status: string) {
  switch (status) {
    case "draft":
      return "当前正文可编辑，附件可继续补充。";
    case "submitted":
      return "正文和附件建议保持锁定，仅允许通过流程动作继续流转。";
    case "approved":
      return "记录已归档为已审核状态，需重新打开后才能再次编辑。";
    default:
      return "当前锁定状态未知。";
  }
}

function formatTime(value: string) {
  return new Date(value).toLocaleString();
}

function extractWorkflowComment(item: AuditLogItem) {
  const detail = item.detail_json as Record<string, unknown> | null | undefined;
  const commentValue = detail?.comment;
  return typeof commentValue === "string" && commentValue.trim() ? commentValue.trim() : "";
}

function extractStatusChange(item: AuditLogItem) {
  const detail = item.detail_json as Record<string, unknown> | null | undefined;
  const beforeStatus = typeof detail?.before_status === "string" ? detail.before_status : "";
  const afterStatus = typeof detail?.after_status === "string" ? detail.after_status : "";
  if (!beforeStatus && !afterStatus) {
    return "";
  }
  return `${getRecordStatusLabel(beforeStatus || "-")} → ${getRecordStatusLabel(afterStatus || "-")}`;
}

async function loadTimeline() {
  timelineLoading.value = true;
  timelineError.value = "";

  try {
    timelineItems.value = await fetchAuditLogs({
      resource_type: "record",
      resource_id: props.record.id,
      limit: 20,
    });
  } catch (err) {
    console.error(err);
    timelineItems.value = [];
    timelineError.value = "流程时间线加载失败。";
  } finally {
    timelineLoading.value = false;
  }
}

async function runAction(action: RecordWorkflowAction) {
  loadingAction.value = action;
  error.value = "";
  successText.value = "";

  try {
    const updated = await transitionRecordWorkflow(props.record.id, {
      action,
      comment: comment.value || undefined,
    });

    comment.value = "";
    successText.value = `已完成：${actionLabel(action)}`;
    emit("changed", updated);
    await loadTimeline();
  } catch (err: any) {
    console.error(err);
    error.value = err?.response?.data?.detail || "状态流转失败。";
  } finally {
    loadingAction.value = "";
  }
}

watch(
  () => [props.record.id, props.record.updated_at],
  () => {
    void loadTimeline();
  },
  { immediate: true },
);
</script>

<template>
  <section class="card workflow-panel">
    <div class="section-header">
      <div>
        <h3>记录流程</h3>
        <p class="muted">当前状态：<strong>{{ getRecordStatusLabel(record.status) }}</strong></p>
        <p class="muted">{{ statusHint(record.status) }}</p>
      </div>
      <span class="badge">{{ isEditable ? "正文可编辑" : "正文已锁定" }}</span>
    </div>

    <div class="workflow-grid">
      <section class="sub-card workflow-lock-card">
        <strong>状态锁定</strong>
        <p class="muted">{{ lockDescription(record.status) }}</p>
      </section>

      <section class="sub-card workflow-action-card">
        <div class="form-item">
          <label class="label">审核意见 / 流转说明</label>
          <textarea
            v-model="comment"
            class="textarea"
            rows="3"
            placeholder="例如：数据已核对完成，同意进入下一状态。"
          />
        </div>

        <div v-if="actions.length > 0" class="workflow-actions">
          <button
            v-for="action in actions"
            :key="action"
            class="button secondary workflow-action-button"
            :disabled="loadingAction !== ''"
            @click="runAction(action)"
          >
            <span>{{ loadingAction === action ? "处理中..." : actionLabel(action) }}</span>
            <small>{{ actionDescription(action) }}</small>
          </button>
        </div>

        <p v-else class="muted">当前没有可执行的流程动作。</p>
        <p v-if="successText" class="muted">{{ successText }}</p>
        <p v-if="error" class="error-text">{{ error }}</p>
      </section>
    </div>

    <section class="sub-card workflow-timeline-card">
      <div class="row-between timeline-header">
        <div>
          <strong>流程时间线</strong>
          <p class="muted">包含审核动作、恢复版本和关键流转记录。</p>
        </div>
        <button class="button secondary" type="button" @click="loadTimeline">刷新时间线</button>
      </div>

      <p v-if="timelineLoading" class="muted">正在加载流程时间线...</p>
      <p v-else-if="timelineError" class="error-text">{{ timelineError }}</p>
      <div v-else-if="timelineItems.length === 0" class="empty-state">当前还没有流程时间线。</div>

      <div v-else class="timeline-list">
        <article v-for="item in timelineItems" :key="item.id" class="timeline-item">
          <div class="timeline-marker" />
          <div class="timeline-content">
            <div class="row-between timeline-item-header">
              <div>
                <strong>{{ item.summary }}</strong>
                <div class="muted">{{ formatTime(item.created_at) }}</div>
              </div>
              <div class="muted timeline-actor">{{ item.actor_username || item.actor_id || "系统" }}</div>
            </div>

            <div v-if="extractStatusChange(item)" class="muted">状态变化：{{ extractStatusChange(item) }}</div>
            <div v-if="extractWorkflowComment(item)" class="timeline-comment">
              <span class="detail-label">审核意见</span>
              <p>{{ extractWorkflowComment(item) }}</p>
            </div>
          </div>
        </article>
      </div>
    </section>
  </section>
</template>

<style scoped>
.workflow-panel {
  display: grid;
  gap: 16px;
}

.workflow-grid {
  display: grid;
  grid-template-columns: minmax(220px, 280px) minmax(0, 1fr);
  gap: 16px;
}

.workflow-lock-card,
.workflow-action-card,
.workflow-timeline-card {
  display: grid;
  gap: 12px;
}

.workflow-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
}

.workflow-action-button {
  min-height: 64px;
  justify-content: space-between;
  text-align: left;
  border-radius: 18px;
}

.workflow-action-button small {
  display: block;
  color: inherit;
  opacity: 0.72;
}

.timeline-header {
  align-items: center;
}

.timeline-list {
  display: grid;
  gap: 12px;
}

.timeline-item {
  display: grid;
  grid-template-columns: 20px minmax(0, 1fr);
  gap: 12px;
}

.timeline-marker {
  width: 12px;
  height: 12px;
  border-radius: 999px;
  background: var(--accent);
  margin-top: 8px;
  box-shadow: 0 0 0 6px rgba(239, 71, 111, 0.12);
}

.timeline-content {
  display: grid;
  gap: 8px;
  padding: 14px 16px;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.92);
}

.timeline-item-header {
  align-items: flex-start;
}

.timeline-actor {
  text-align: right;
}

.timeline-comment {
  display: grid;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(239, 71, 111, 0.06);
}

.timeline-comment p {
  margin: 0;
}

@media (max-width: 960px) {
  .workflow-grid {
    grid-template-columns: 1fr;
  }

  .timeline-item {
    grid-template-columns: 1fr;
  }

  .timeline-marker {
    display: none;
  }
}
</style>
