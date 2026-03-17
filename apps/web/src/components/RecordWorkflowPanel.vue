<script setup lang="ts">
import { computed, ref } from "vue";

import { transitionRecordWorkflow } from "../api/records";
import type {
  ExperimentRecordDetail,
  RecordWorkflowAction,
} from "../types/api";

const props = defineProps<{
  record: ExperimentRecordDetail;
}>();

const emit = defineEmits<{
  changed: [ExperimentRecordDetail];
}>();

const comment = ref("");
const loadingAction = ref<RecordWorkflowAction | "">("");
const error = ref("");
const successText = ref("");

const actions = computed(() => props.record.allowed_actions || []);

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

function statusText(status: string) {
  switch (status) {
    case "draft":
      return "草稿";
    case "submitted":
      return "待审核";
    case "approved":
      return "已通过";
    default:
      return status;
  }
}

function statusHint(status: string) {
  switch (status) {
    case "draft":
      return "可继续编辑正文，也可提交审核。";
    case "submitted":
      return "正文已冻结，等待项目负责人或管理员审核。";
    case "approved":
      return "已通过审核；如需改动，请重新打开为草稿。";
    default:
      return "未知状态。";
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
  } catch (err) {
    console.error(err);
    error.value = "状态流转失败。";
  } finally {
    loadingAction.value = "";
  }
}
</script>

<template>
  <section class="card">
    <div class="section-header">
      <div>
        <h3>记录流程</h3>
        <p class="muted">
          当前状态：<strong>{{ statusText(record.status) }}</strong>
        </p>
        <p class="muted">{{ statusHint(record.status) }}</p>
      </div>
    </div>

    <div v-if="actions.length > 0" class="stack">
      <div class="form-item">
        <label class="label">流转说明（可选）</label>
        <input
          v-model="comment"
          class="input"
          type="text"
          placeholder="例如：内容补充完成，提交项目负责人审核"
        />
      </div>

      <div class="actions">
        <button
          v-for="action in actions"
          :key="action"
          class="button secondary"
          :disabled="loadingAction !== ''"
          @click="runAction(action)"
        >
          {{ loadingAction === action ? "处理中..." : actionLabel(action) }}
        </button>
      </div>
    </div>

    <p v-else class="muted">当前没有可执行的流程动作。</p>
    <p v-if="successText" class="muted">{{ successText }}</p>
    <p v-if="error" class="error-text">{{ error }}</p>
  </section>
</template>