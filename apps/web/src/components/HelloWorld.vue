<script setup lang="ts">
import { ref } from "vue";

defineProps<{ msg: string }>();

const count = ref(0);
</script>

<template>
  <section class="card">
    <h3>{{ msg }}</h3>
    <p class="muted">这是一个未启用的演示组件，当前仅保留为本地调试占位。</p>
    <button type="button" class="button secondary" @click="count += 1">
      已点击 {{ count }} 次
    </button>
  </section>
</template>
