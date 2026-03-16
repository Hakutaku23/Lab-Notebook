<script setup lang="ts">
import { onMounted, ref } from "vue";

import {
  deleteAttachment,
  fetchAttachments,
  uploadAttachment,
} from "../api/attachments";
import type { AttachmentItem } from "../types/api";

const props = defineProps<{
  recordId: string;
}>();

const attachments = ref<AttachmentItem[]>([]);
const loading = ref(false);
const uploading = ref(false);
const error = ref("");
const description = ref("");
const uploadedBy = ref("");

const emit = defineEmits<{
  changed: [];
}>();

function humanSize(size: number): string {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

async function loadAttachments() {
  loading.value = true;
  error.value = "";
  try {
    attachments.value = await fetchAttachments(props.recordId);
  } catch (err) {
    console.error(err);
    error.value = "附件列表加载失败。";
  } finally {
    loading.value = false;
  }
}

async function onFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  uploading.value = true;
  error.value = "";
  try {
    await uploadAttachment(
      props.recordId,
      file,
      description.value || undefined,
      uploadedBy.value || undefined,
    );
    description.value = "";
    target.value = "";
    await loadAttachments();
    emit("changed");
  } catch (err) {
    console.error(err);
    error.value = "附件上传失败。";
  } finally {
    uploading.value = false;
  }
}

async function removeAttachment(id: string) {
  const confirmed = window.confirm("确认删除这个附件吗？");
  if (!confirmed) return;

  try {
    await deleteAttachment(id);
    await loadAttachments();
    emit("changed");
  } catch (err) {
    console.error(err);
    error.value = "附件删除失败。";
  }
}

onMounted(loadAttachments);
</script>

<template>
  <section class="card">
    <div class="section-header">
      <div>
        <h3>附件管理</h3>
        <p class="muted">支持上传实验图片、原始数据和补充文档。</p>
      </div>
    </div>

    <div class="form-item">
      <label class="label">附件说明</label>
      <input v-model="description" class="input" type="text" placeholder="可选，便于团队理解附件用途" />
    </div>

    <div class="form-item">
      <label class="label">上传者 ID（可选）</label>
      <input v-model="uploadedBy" class="input" type="text" placeholder="默认使用当前登录用户" />
    </div>

    <div class="form-item">
      <label class="label">选择文件</label>
      <input class="input" type="file" :disabled="uploading" @change="onFileChange" />
    </div>

    <p v-if="error" class="error-text">{{ error }}</p>
    <p v-if="loading" class="muted">正在加载附件...</p>
    <p v-if="uploading" class="muted">正在上传附件...</p>

    <div v-if="attachments.length === 0" class="empty-state">暂无附件。</div>

    <div v-else class="stack">
      <article v-for="item in attachments" :key="item.id" class="sub-card">
        <div class="row-between">
          <div>
            <h4>{{ item.original_name }}</h4>
            <p class="muted">大小：{{ humanSize(item.size_bytes) }}</p>
            <p class="muted">说明：{{ item.description || "无" }}</p>
          </div>

          <div class="actions">
            <a
              class="button secondary"
              :href="item.download_url"
              target="_blank"
              rel="noreferrer"
            >
              下载
            </a>
            <button class="button danger" @click="removeAttachment(item.id)">删除</button>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>
