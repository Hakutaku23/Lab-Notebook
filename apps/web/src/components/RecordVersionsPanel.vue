<script setup lang="ts">
import { reactive, ref, watch } from "vue";
import {
  compareRecordVersions,
  createManualSnapshot,
  fetchRecordVersionDetail,
  fetchRecordVersions,
  restoreRecordVersion,
} from "../api/records";
import type {
  ExperimentRecordDetail,
  RecordVersionCompareResult,
  RecordVersionDetail,
  RecordVersionSummary,
} from "../types/api";

const props = defineProps<{
  recordId: string;
}>();

const emit = defineEmits<{
  restored: [ExperimentRecordDetail];
}>();

const loading = ref(false);
const detailLoading = ref(false);
const creating = ref(false);
const comparing = ref(false);
const restoring = ref(false);

const error = ref("");
const compareError = ref("");
const restoreError = ref("");
const restoreSuccess = ref("");

const versions = ref<RecordVersionSummary[]>([]);
const selectedVersion = ref<RecordVersionDetail | null>(null);
const compareResult = ref<RecordVersionCompareResult | null>(null);

const fromVersionId = ref("");
const toVersionId = ref("");
const restoreComment = ref("");

const snapshotForm = reactive({
  comment: "",
});

function formatTime(value: string) {
  return new Date(value).toLocaleString();
}

function formatValue(value: unknown) {
  if (value === null || value === undefined) {
    return "—";
  }
  if (typeof value === "string") {
    return value || "—";
  }
  return JSON.stringify(value, null, 2);
}

function versionLabel(item: RecordVersionSummary) {
  return `v${item.version_no} · ${formatTime(item.created_at)}`;
}

async function loadSelectedVersion(versionId: string) {
  if (!versionId) {
    selectedVersion.value = null;
    return;
  }

  detailLoading.value = true;
  error.value = "";

  try {
    selectedVersion.value = await fetchRecordVersionDetail(props.recordId, versionId);
  } catch (err) {
    console.error(err);
    error.value = "版本详情加载失败。";
  } finally {
    detailLoading.value = false;
  }
}

async function runCompare() {
  compareError.value = "";

  if (!fromVersionId.value || !toVersionId.value) {
    compareResult.value = null;
    return;
  }

  if (fromVersionId.value === toVersionId.value) {
    compareError.value = "对比版本不能相同。";
    compareResult.value = null;
    return;
  }

  comparing.value = true;

  try {
    compareResult.value = await compareRecordVersions(
      props.recordId,
      fromVersionId.value,
      toVersionId.value,
    );
  } catch (err) {
    console.error(err);
    compareError.value = "版本差异计算失败。";
    compareResult.value = null;
  } finally {
    comparing.value = false;
  }
}

async function refreshVersions(preferredVersionId?: string) {
  loading.value = true;
  error.value = "";

  try {
    const list = await fetchRecordVersions(props.recordId);
    versions.value = list;

    if (list.length === 0) {
      selectedVersion.value = null;
      fromVersionId.value = "";
      toVersionId.value = "";
      compareResult.value = null;
      return;
    }

    const latestVersion = list[0];
    if (!latestVersion) {
      selectedVersion.value = null;
      return;
    }

    const selectedId =
      preferredVersionId ||
      selectedVersion.value?.id ||
      latestVersion.id;

    await loadSelectedVersion(selectedId);

    if (!toVersionId.value || !list.some((item) => item.id === toVersionId.value)) {
      toVersionId.value = latestVersion.id;
    }

    if (
      !fromVersionId.value ||
      !list.some((item) => item.id === fromVersionId.value) ||
      fromVersionId.value === toVersionId.value
    ) {
      fromVersionId.value = list[1]?.id || "";
    }

    if (fromVersionId.value && toVersionId.value && fromVersionId.value !== toVersionId.value) {
      await runCompare();
    } else {
      compareResult.value = null;
    }
  } catch (err) {
    console.error(err);
    error.value = "版本列表加载失败。";
  } finally {
    loading.value = false;
  }
}

async function handleCreateSnapshot() {
  creating.value = true;
  error.value = "";

  try {
    const created = await createManualSnapshot(props.recordId, {
      comment: snapshotForm.comment || undefined,
    });

    snapshotForm.comment = "";
    await refreshVersions(created.id);
  } catch (err) {
    console.error(err);
    error.value = "手动创建快照失败。";
  } finally {
    creating.value = false;
  }
}

async function handleRestoreVersion() {
  if (!selectedVersion.value) {
    restoreError.value = "请先选择要恢复的版本。";
    return;
  }

  const sourceVersionId = selectedVersion.value.id;
  const sourceVersionNo = selectedVersion.value.version_no;

  restoring.value = true;
  restoreError.value = "";
  restoreSuccess.value = "";

  try {
    const restored = await restoreRecordVersion(props.recordId, sourceVersionId, {
      comment: restoreComment.value || undefined,
    });

    restoreComment.value = "";
    restoreSuccess.value = `已恢复为 v${sourceVersionNo}，系统已自动生成新的当前版本。`;
    emit("restored", restored);

    selectedVersion.value = null;
    await refreshVersions();
  } catch (err) {
    console.error(err);
    restoreError.value = "历史版本恢复失败。";
  } finally {
    restoring.value = false;
  }
}

watch(
  () => props.recordId,
  () => {
    compareResult.value = null;
    fromVersionId.value = "";
    toVersionId.value = "";
    selectedVersion.value = null;
    snapshotForm.comment = "";
    restoreComment.value = "";
    restoreError.value = "";
    restoreSuccess.value = "";
    void refreshVersions();
  },
  { immediate: true },
);
</script>

<template>
  <section class="card">
    <div class="row-between" style="gap: 16px; align-items: flex-start;">
      <div>
        <h3>版本快照</h3>
        <p class="muted">
          支持手动打点、查看任意版本快照，并对比两个历史版本之间的差异。
        </p>
      </div>

      <button class="button secondary" type="button" @click="refreshVersions()">
        刷新
      </button>
    </div>

    <form
      style="display: grid; grid-template-columns: 1fr auto; gap: 12px; margin-top: 16px;"
      @submit.prevent="handleCreateSnapshot"
    >
      <input
        v-model="snapshotForm.comment"
        type="text"
        placeholder="快照说明，例如：修改实验条件后手动留档"
      />
      <button class="button" type="submit" :disabled="creating">
        {{ creating ? "创建中..." : "手动创建快照" }}
      </button>
    </form>

    <p v-if="error" class="error-text" style="margin-top: 12px;">
      {{ error }}
    </p>

    <p v-if="loading" class="muted" style="margin-top: 16px;">
      正在加载版本...
    </p>

    <template v-else>
      <p v-if="versions.length === 0" class="muted" style="margin-top: 16px;">
        当前还没有可用版本。
      </p>

      <div v-else style="display: grid; gap: 18px; margin-top: 16px;">
        <div class="card" style="padding: 16px; margin: 0;">
          <div class="row-between" style="gap: 16px; align-items: flex-start;">
            <div>
              <strong>版本列表</strong>
              <div class="muted">点击任一版本可查看完整快照。</div>
            </div>
          </div>

          <div style="display: grid; gap: 8px; margin-top: 12px;">
            <button
              v-for="item in versions"
              :key="item.id"
              type="button"
              class="button secondary"
              style="justify-content: space-between; text-align: left;"
              @click="loadSelectedVersion(item.id)"
            >
              <span>{{ versionLabel(item) }}</span>
              <span>{{ item.comment || "无说明" }}</span>
            </button>
          </div>
        </div>

        <div class="card" style="padding: 16px; margin: 0;">
          <div class="row-between" style="gap: 16px; align-items: flex-start;">
            <div>
              <strong>版本差异对比</strong>
              <div class="muted">选择两个版本，查看字段变化明细。</div>
            </div>
          </div>

          <div
            style="
              display: grid;
              grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
              gap: 12px;
              margin-top: 12px;
            "
          >
            <label style="display: grid; gap: 6px;">
              <span>起始版本</span>
              <select v-model="fromVersionId">
                <option value="">请选择</option>
                <option v-for="item in versions" :key="item.id" :value="item.id">
                  {{ versionLabel(item) }}
                </option>
              </select>
            </label>

            <label style="display: grid; gap: 6px;">
              <span>目标版本</span>
              <select v-model="toVersionId">
                <option value="">请选择</option>
                <option v-for="item in versions" :key="item.id" :value="item.id">
                  {{ versionLabel(item) }}
                </option>
              </select>
            </label>

            <div style="display: flex; align-items: end;">
              <button class="button" type="button" :disabled="comparing" @click="runCompare">
                {{ comparing ? "对比中..." : "开始对比" }}
              </button>
            </div>
          </div>

          <p v-if="compareError" class="error-text" style="margin-top: 12px;">
            {{ compareError }}
          </p>

          <template v-if="compareResult">
            <div style="margin-top: 16px;">
              <div class="muted">
                对比 v{{ compareResult.from_version.version_no }}
                → v{{ compareResult.to_version.version_no }}
              </div>
              <div style="margin-top: 4px;">
                共发现 <strong>{{ compareResult.change_count }}</strong> 处变化
              </div>
            </div>

            <div v-if="compareResult.items.length > 0" style="margin-top: 12px;">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>分组</th>
                    <th>字段</th>
                    <th>变化类型</th>
                    <th>修改前</th>
                    <th>修改后</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in compareResult.items" :key="`${item.group}-${item.key}`">
                    <td>{{ item.group }}</td>
                    <td>{{ item.label || item.key }}</td>
                    <td>{{ item.change_type }}</td>
                    <td><pre class="detail-value">{{ formatValue(item.before) }}</pre></td>
                    <td><pre class="detail-value">{{ formatValue(item.after) }}</pre></td>
                  </tr>
                </tbody>
              </table>
            </div>

            <p v-else class="muted" style="margin-top: 12px;">两个版本之间没有字段变化。</p>
          </template>
        </div>

        <div class="card" style="padding: 16px; margin: 0;">
          <strong>当前查看快照</strong>

          <p v-if="detailLoading" class="muted" style="margin-top: 12px;">
            正在加载版本详情...
          </p>

          <template v-else-if="selectedVersion">
            <div class="muted" style="margin-top: 12px;">
              v{{ selectedVersion.version_no }} · {{ formatTime(selectedVersion.created_at) }}
            </div>
            <div class="muted">{{ selectedVersion.comment || "无说明" }}</div>

            <pre class="detail-value" style="margin-top: 12px;">{{
JSON.stringify(selectedVersion.snapshot_json, null, 2)
            }}</pre>

            <div
              style="
                display: grid;
                gap: 12px;
                margin-top: 16px;
                padding-top: 16px;
                border-top: 1px solid rgba(148, 163, 184, 0.25);
              "
            >
              <div>
                <strong>恢复为当前快照</strong>
                <div class="muted">
                  会覆盖当前记录的标题、状态、摘要与字段值，并自动生成新快照；附件文件不会回滚。
                </div>
              </div>

              <input
                v-model="restoreComment"
                type="text"
                placeholder="恢复说明，例如：回退到审核前版本"
              />

              <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
                <button
                  class="button danger"
                  type="button"
                  :disabled="restoring"
                  @click="handleRestoreVersion"
                >
                  {{ restoring ? "恢复中..." : `恢复为 v${selectedVersion.version_no}` }}
                </button>

                <span v-if="restoreSuccess" class="muted">
                  {{ restoreSuccess }}
                </span>
              </div>

              <p v-if="restoreError" class="error-text">
                {{ restoreError }}
              </p>
            </div>
          </template>

          <p v-else class="muted" style="margin-top: 12px;">尚未选择版本。</p>
        </div>
      </div>
    </template>
  </section>
</template>