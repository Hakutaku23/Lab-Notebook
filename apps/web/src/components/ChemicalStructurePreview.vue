<script setup lang="ts">
import type { Root } from "react-dom/client";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

interface Props {
  structure: string;
}

const props = defineProps<Props>();

const containerRef = ref<HTMLDivElement | null>(null);
const errorText = ref("");

let reactRoot: Root | null = null;

function cleanup() {
  reactRoot?.unmount();
  reactRoot = null;
}

async function renderPreview() {
  if (!containerRef.value || !props.structure.trim()) {
    cleanup();
    return;
  }

  errorText.value = "";

  try {
    const [React, reactDomClient, ketcherReact, _cssLoaded] = await Promise.all([
      import("react"),
      import("react-dom/client"),
      import("ketcher-react"),
      import("ketcher-react/dist/index.css"),
    ]);

    cleanup();
    reactRoot = reactDomClient.createRoot(containerRef.value);
    const StructRender = (ketcherReact as Record<string, unknown>).StructRender as unknown;

    if (!StructRender) {
      throw new Error("未找到结构预览组件。");
    }

    reactRoot.render(
      React.createElement(StructRender as any, {
        struct: props.structure,
        fullsize: true,
        options: {
          autoScale: true,
          autoScaleMargin: 12,
          hideImplicitHydrogen: false,
          ignoreMouseEvents: true,
        },
      }),
    );
  } catch (error) {
    console.error(error);
    errorText.value = error instanceof Error ? error.message : "结构预览加载失败。";
    cleanup();
  }
}

watch(
  () => props.structure,
  () => {
    void renderPreview();
  },
  { immediate: true },
);

onMounted(() => {
  void renderPreview();
});

onBeforeUnmount(() => {
  cleanup();
});
</script>

<template>
  <div class="chemical-structure-preview">
    <div v-if="errorText" class="muted chemical-structure-preview__error">
      {{ errorText }}
    </div>
    <div ref="containerRef" class="chemical-structure-preview__canvas" />
  </div>
</template>

<style scoped>
.chemical-structure-preview {
  border: 1px solid rgba(15, 23, 42, 0.1);
  border-radius: 14px;
  overflow: hidden;
  background: #fff;
}

.chemical-structure-preview__canvas {
  min-height: 260px;
}

.chemical-structure-preview__error {
  padding: 12px 14px 0;
}
</style>
