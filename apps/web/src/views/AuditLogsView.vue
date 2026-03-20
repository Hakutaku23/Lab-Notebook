<script setup lang="ts">
import AuditLogPanel from "../components/AuditLogPanel.vue";
</script>

<template>
  <section class="page">
    <section class="page-hero">
      <div>
        <p class="eyebrow">审计日志</p>
        <h2>全局审计检索</h2>
        <p class="muted">管理员可按关键词、资源、操作人和动作查看全局审计轨迹。</p>
      </div>
    </section>

    <AuditLogPanel title="全局审计日志" :show-filters="true" />
  </section>
</template>
