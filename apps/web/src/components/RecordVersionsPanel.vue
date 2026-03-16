<script setup lang="ts">
import { onMounted, ref } from "vue";

import {
  createManualSnapshot,
  fetchRecordVersionDetail,
  fetchRecordVersions,
} from "../api/records";
import type {
  RecordVersionDetail,
  RecordVersionSummary,
} from "../types/api";

const props = defineProps<{
  recordId: string;
}>();

const versions = ref<RecordVersionSummary[]>([]);
const selectedVersion = ref<RecordVersionDetail | null>(null);
const comment = ref("");
const createdBy = ref("");
const loading = ref(false);
const creating = ref(false);
const error = ref("");

async function loadVersions() {
  loading.value = true;
  error.value = "";
  try {
    versions.value = await fetchRecordVersions(props.recordId);
    if (versions.value.length > 0 && !selectedVersion.value) {
      selectedVersion.value = await fetchRecordVersionDetail(
        props.recordId,
        versions.value[0].id,
      );
    }
  } catch (err) {
    console.error(err);
    error.value = "版本列表加载失败。";
  } finally {
    loading.value = false;
  }
}

async function selectVersion(versionId: string) {
  try {
    selectedVersion.value = await fetchRecordVersionDetail(props.recordId, versionId);
  } catch (err) {
    console.error(err);
    error.value = "版本详情加载失败。";
  }
}

async function createSnapshot() {
  creating.value = true;
  error.value = "";
  try {
    selectedVersion.value = await createManualSnapshot(props.recordId, {
      comment: comment.value || undefined,
      created_by: createdBy.value || undefined,
    });
    comment.value = "";
    await loadVersions();
  } catch (err) {
    console.error(err);
    error.value = "手动快照创建失败。";
  } finally {
    creating.value = false;
  }
}
onMounted(loadVersions);
</script>

<template>
  <section class="card">
    <h3>版本快照</h3>

    <div class="form-item">
      <label class="label">快照说明</label>
      <input v-model="comment" class="input" type="text" placeholder="例如：完成初稿后留档" />
    </div>

    <div class="form-item">
      <label class="label">创建人 ID（可选）</label>
      <input v-model="createdBy" class="input" type="text" placeholder="可留空" />
    </div>

    <button class="button" :disabled="creating" @click="createSnapshot">
      {{ creating ? "创建中..." : "手动创建快照" }}
    </button>

    <p v-if="error" class="error-text">{{ error }}</p>
    <p v-if="loading" class="muted">正在加载版本...</p>

    <div class="stack" style="margin-top:16px;">
      <article
        v-for="item in versions"
        :key="item.id"
        class="sub-card"
        style="cursor:pointer;"
        @click="selectVersion(item.id)"
      >
        <strong>v{{ item.version_no }}</strong>
        <p class="muted">{{ item.comment || "无说明" }}</p>
        <p class="muted">{{ item.created_at }}</p>
      </article>
    </div>

    <div v-if="selectedVersion" style="margin-top:16px;">
      <h4>当前查看：v{{ selectedVersion.version_no }}</h4>
      <pre class="detail-value">{{ JSON.stringify(selectedVersion.snapshot_json, null, 2) }}</pre>
    </div>
  </section>
</template>