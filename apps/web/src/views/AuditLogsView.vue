<script setup lang="ts">
import AuditLogPanel from "../components/AuditLogPanel.vue";
</script>

<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h2>审计日志</h2>
        <p class="muted">管理员可按资源、操作人和动作查看全局审计轨迹。</p>
      </div>
    </div>

    <AuditLogPanel title="全局审计日志" :show-filters="true" />
  </section>
</template>