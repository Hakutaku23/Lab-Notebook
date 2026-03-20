<script setup lang="ts">
import type { Root } from "react-dom/client";
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

import {
  getChemicalEquationDisplayText,
  getChemicalEquationSource,
  normalizeChemicalEquationValue,
  type ChemicalEquationValue,
} from "../utils/templateRuntime";

interface Props {
  modelValue: ChemicalEquationValue | string | null | undefined;
  placeholder?: string | null;
  readonly?: boolean;
  label?: string;
  helpText?: string | null;
}

type KetcherApi = {
  containsReaction?: () => boolean;
  getKet?: () => Promise<string>;
  getRxn?: (version?: string) => Promise<string>;
  getMolfile?: (version?: string) => Promise<string>;
  getSmiles?: () => Promise<string>;
  generateImage?: (
    source: string,
    options?: Record<string, unknown>,
  ) => Promise<Blob>;
  setMolecule?: (source: string) => Promise<void>;
  editor?: {
    subscribe?: (
      eventName: string,
      handler: () => void | Promise<void>,
    ) => unknown;
  };
};

const props = withDefaults(defineProps<Props>(), {
  modelValue: null,
  placeholder: "请输入化学结构描述、SMILES 或反应式。",
  readonly: false,
  label: "化学结构/反应编辑",
  helpText: "优先使用 Ketcher 结构编辑器；初始化失败时会自动回退到文本录入。",
});

const emit = defineEmits<{
  (event: "update:modelValue", value: ChemicalEquationValue | null): void;
}>();

const containerRef = ref<HTMLDivElement | null>(null);
const textValue = ref("");
const editorMode = ref<"editor" | "text">("editor");
const isBootingEditor = ref(false);
const editorReady = ref(false);
const statusText = ref("等待初始化结构编辑器...");
const errorText = ref("");

let reactRoot: Root | null = null;
let ketcher: KetcherApi | null = null;
let unsubscribeChange: (() => void) | null = null;
let syncingFromEditor = false;
let lastLoadedSource = "";

function normalizeValue(value: Props["modelValue"]): ChemicalEquationValue | null {
  return normalizeChemicalEquationValue(value);
}

function toSource(value: Props["modelValue"]): string {
  return getChemicalEquationSource(value);
}

function toText(value: Props["modelValue"]): string {
  return getChemicalEquationDisplayText(value);
}

const previewSvg = computed(() => normalizeValue(props.modelValue)?.svg || "");
const previewKind = computed(() =>
  normalizeValue(props.modelValue)?.kind === "reaction" ? "反应" : "分子",
);

function emitTextValue(value: string) {
  textValue.value = value;
  const trimmed = value.trim();

  if (!trimmed) {
    emit("update:modelValue", null);
    return;
  }

  emit(
    "update:modelValue",
    normalizeChemicalEquationValue({
      kind: "molecule",
      plain_text: trimmed,
      smiles: "",
      molfile: "",
      rxnfile: "",
      ket: "",
      svg: previewSvg.value || "",
    }),
  );
}

function cleanupEditor() {
  if (typeof unsubscribeChange === "function") {
    unsubscribeChange();
  }
  unsubscribeChange = null;
  ketcher = null;
  editorReady.value = false;
  reactRoot?.unmount();
  reactRoot = null;
}

async function loadValueIntoEditor(source: string) {
  if (!ketcher?.setMolecule) {
    return;
  }

  try {
    await ketcher.setMolecule(source || "");
    lastLoadedSource = source;
  } catch (error) {
    console.error(error);
    errorText.value = "结构内容载入失败，已切换为文本录入模式。";
    editorMode.value = "text";
    cleanupEditor();
  }
}

async function emitStructuredValue() {
  if (!ketcher) {
    return;
  }

  try {
    syncingFromEditor = true;

    const containsReaction = Boolean(ketcher.containsReaction?.());
    const kind = containsReaction ? "reaction" : "molecule";
    const ket = (await ketcher.getKet?.()) || "";
    const rxnfile = containsReaction ? (await ketcher.getRxn?.("v2000")) || "" : "";
    const molfile = !containsReaction ? (await ketcher.getMolfile?.("auto")) || "" : "";
    const smiles = !containsReaction ? (await ketcher.getSmiles?.()) || "" : "";
    const plainText = smiles || rxnfile || molfile || ket || textValue.value.trim();
    const sourceForImage = rxnfile || molfile || ket || "";

    let svg = previewSvg.value || "";
    if (sourceForImage && typeof ketcher.generateImage === "function") {
      try {
        const blob = await ketcher.generateImage(sourceForImage, {
          outputFormat: "svg",
          backgroundColor: "#ffffff",
          bondThickness: 1,
        });
        svg = await blob.text();
      } catch (error) {
        console.warn("Ketcher SVG export failed:", error);
      }
    }

    textValue.value = plainText;
    lastLoadedSource = sourceForImage || plainText;
    emit(
      "update:modelValue",
      normalizeChemicalEquationValue({
        kind,
        ket,
        rxnfile,
        molfile,
        smiles,
        svg,
        plain_text: plainText,
      }),
    );
    statusText.value = containsReaction ? "已同步反应结构。" : "已同步分子结构。";
    errorText.value = "";
  } catch (error) {
    console.error(error);
    errorText.value = "结构同步失败，已切换为文本录入模式。";
    editorMode.value = "text";
    cleanupEditor();
  } finally {
    syncingFromEditor = false;
  }
}

function normalizeSubscription(subscription: unknown): (() => void) | null {
  if (typeof subscription === "function") {
    return subscription as () => void;
  }

  if (
    subscription &&
    typeof subscription === "object" &&
    "unsubscribe" in subscription &&
    typeof (subscription as { unsubscribe?: unknown }).unsubscribe === "function"
  ) {
    return () => (subscription as { unsubscribe: () => void }).unsubscribe();
  }

  return null;
}

async function bootEditor() {
  if (props.readonly || !containerRef.value || isBootingEditor.value || reactRoot) {
    return;
  }

  isBootingEditor.value = true;
  statusText.value = "正在加载 Ketcher 结构编辑器...";
  errorText.value = "";

  try {
    const [
      React,
      reactDomClient,
      ketcherReact,
      standaloneModule,
      _cssLoaded,
    ] = await Promise.all([
      import("react"),
      import("react-dom/client"),
      import("ketcher-react"),
      import("ketcher-standalone"),
      import("ketcher-react/dist/index.css"),
    ]);

    const root = reactDomClient.createRoot(containerRef.value);
    reactRoot = root;

    const EditorComponent = ketcherReact.Editor as unknown;
    const standaloneExports = standaloneModule as Record<string, unknown>;
    const StandaloneStructServiceProvider =
      "StandaloneStructServiceProvider" in standaloneExports
        ? (standaloneExports.StandaloneStructServiceProvider as new () => unknown)
        : ("default" in standaloneExports
            ? (standaloneExports.default as new () => unknown)
            : null);

    if (!StandaloneStructServiceProvider) {
      throw new Error("未找到 Ketcher standalone 服务提供器导出。");
    }

    const structServiceProvider = new StandaloneStructServiceProvider() as unknown;

    const handleInit = async (instance: unknown) => {
      ketcher = instance as KetcherApi;
      editorReady.value = true;
      statusText.value = "Ketcher 已就绪。";

      await loadValueIntoEditor(toSource(props.modelValue));

      if (props.readonly) {
        return;
      }

      const subscription = ketcher.editor?.subscribe?.("change", async () => {
        if (syncingFromEditor) {
          return;
        }
        await emitStructuredValue();
      });
      unsubscribeChange = normalizeSubscription(subscription);
    };

    const handleError = (message: string) => {
      console.error("Ketcher initialization failed:", message);
      errorText.value = message || "Ketcher 初始化失败，已切换为文本录入模式。";
      editorMode.value = "text";
      cleanupEditor();
    };

    root.render(
      React.createElement(EditorComponent as any, {
        staticResourcesUrl: "/ketcher/dist",
        structServiceProvider,
        errorHandler: handleError,
        onInit: handleInit,
        disableMacromoleculesEditor: true,
      }),
    );
  } catch (error) {
    console.error(error);
    const detail = error instanceof Error ? error.message : String(error ?? "");
    errorText.value = detail
      ? `Ketcher 资源加载失败：${detail}`
      : "Ketcher 资源加载失败，已切换为文本录入模式。";
    editorMode.value = "text";
    cleanupEditor();
  } finally {
    isBootingEditor.value = false;
  }
}

async function retryEditor() {
  editorMode.value = "editor";
  await bootEditor();
}

watch(
  () => props.modelValue,
  async (value) => {
    textValue.value = toText(value);

    if (!editorReady.value || syncingFromEditor) {
      return;
    }

    const source = toSource(value);
    if (source === lastLoadedSource) {
      return;
    }

    await loadValueIntoEditor(source);
  },
  { deep: true, immediate: true },
);

onMounted(() => {
  void bootEditor();
});

onBeforeUnmount(() => {
  cleanupEditor();
});
</script>

<template>
  <div class="ketcher-field">
    <div class="ketcher-field__header">
      <div>
        <strong>{{ label }}</strong>
        <p class="muted ketcher-field__help">{{ helpText }}</p>
      </div>

      <div class="ketcher-field__toolbar">
        <span class="muted">{{ statusText }}</span>
        <button
          v-if="editorMode === 'text' && !readonly"
          class="button secondary"
          type="button"
          @click="retryEditor"
        >
          重试编辑器
        </button>
      </div>
    </div>

    <p v-if="errorText" class="error-text">{{ errorText }}</p>

    <div v-show="editorMode === 'editor'" ref="containerRef" class="ketcher-field__canvas" />

    <textarea
      v-if="editorMode === 'text'"
      class="textarea"
      rows="6"
      :placeholder="placeholder || ''"
      :value="textValue"
      :disabled="readonly"
      @input="emitTextValue(($event.target as HTMLTextAreaElement).value)"
    />

    <div v-if="previewSvg" class="ketcher-field__preview card">
      <div class="row-between ketcher-field__preview-head">
        <strong>当前结构预览</strong>
        <span class="muted">{{ previewKind }}</span>
      </div>
      <div class="ketcher-field__preview-svg" v-html="previewSvg" />
    </div>
  </div>
</template>

<style scoped>
.ketcher-field {
  display: grid;
  gap: 12px;
}

.ketcher-field__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.ketcher-field__help {
  margin-top: 6px;
}

.ketcher-field__toolbar {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
  align-items: center;
}

.ketcher-field__canvas {
  min-height: 560px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  border-radius: 14px;
  overflow: hidden;
  background: #fff;
}

.ketcher-field__preview {
  padding: 16px;
}

.ketcher-field__preview-head {
  align-items: center;
  gap: 12px;
}

.ketcher-field__preview-svg {
  margin-top: 12px;
  overflow-x: auto;
}

.ketcher-field__preview-svg :deep(svg) {
  max-width: 100%;
  height: auto;
}

@media (max-width: 960px) {
  .ketcher-field__header {
    flex-direction: column;
  }

  .ketcher-field__toolbar {
    justify-content: flex-start;
  }

  .ketcher-field__canvas {
    min-height: 420px;
  }
}
</style>
