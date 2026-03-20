import { computed, ref, watch } from "vue";
import { defineStore } from "pinia";

import { checkLLMStatus, fetchLLMStatus } from "../api/llm";
import type { LLMRuntimeConfig, LLMStatus } from "../types/api";

const STORAGE_KEY = "lab-notebook.ai-settings";

export interface AIAssistantContextState {
  title: string;
  description: string;
  placeholder: string;
  task: string;
  context: Record<string, unknown>;
}

function defaultConfig(): LLMRuntimeConfig {
  return {
    mode: "local",
    base_url: "",
    model: "",
    api_key: "",
  };
}

function sanitizeConfig(config: LLMRuntimeConfig): LLMRuntimeConfig {
  return {
    mode: config.mode === "api_key" ? "api_key" : "local",
    base_url: config.base_url?.trim() || "",
    model: config.model?.trim() || "",
    api_key: config.api_key?.trim() || "",
  };
}

function readStoredConfig(): LLMRuntimeConfig {
  if (typeof window === "undefined") {
    return defaultConfig();
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return defaultConfig();
    }
    const parsed = JSON.parse(raw) as Partial<LLMRuntimeConfig>;
    return sanitizeConfig({
      ...defaultConfig(),
      ...parsed,
    });
  } catch {
    return defaultConfig();
  }
}

function writeStoredConfig(config: LLMRuntimeConfig) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(sanitizeConfig(config)));
}

function createDefaultAssistantState(): AIAssistantContextState {
  return {
    title: "AI 助手",
    description: "可随时结合当前页面上下文提问。",
    placeholder: "例如：请结合当前页面内容给我一个简明建议。",
    task: "assistant",
    context: {},
  };
}

export const useAIStore = defineStore("ai", () => {
  const config = ref<LLMRuntimeConfig>(readStoredConfig());
  const defaultStatus = ref<LLMStatus | null>(null);
  const overrideStatus = ref<LLMStatus | null>(null);
  const loadingDefaultStatus = ref(false);
  const checkingConfig = ref(false);
  const error = ref("");
  const assistantOpen = ref(false);
  const assistantPrompt = ref("");
  const assistantState = ref<AIAssistantContextState>(createDefaultAssistantState());

  const isApiKeyMode = computed(() => config.value.mode === "api_key");
  const activeStatus = computed(() => (isApiKeyMode.value ? overrideStatus.value : defaultStatus.value));
  const hasApiKeyConfig = computed(() => {
    return Boolean(config.value.base_url?.trim() && config.value.model?.trim() && config.value.api_key?.trim());
  });

  watch(
    config,
    (nextValue) => {
      writeStoredConfig(nextValue);
      if (nextValue.mode === "local") {
        overrideStatus.value = null;
      }
      error.value = "";
    },
    { deep: true },
  );

  function updateConfig(patch: Partial<LLMRuntimeConfig>) {
    config.value = sanitizeConfig({
      ...config.value,
      ...patch,
    });
  }

  function setAssistantContext(patch: Partial<AIAssistantContextState>) {
    assistantState.value = {
      ...assistantState.value,
      ...patch,
      context: patch.context ?? assistantState.value.context,
    };
  }

  function resetAssistantContext() {
    assistantState.value = createDefaultAssistantState();
    assistantPrompt.value = "";
  }

  function openAssistant(options?: { prompt?: string; patch?: Partial<AIAssistantContextState> }) {
    if (options?.patch) {
      setAssistantContext(options.patch);
    }
    if (typeof options?.prompt === "string") {
      assistantPrompt.value = options.prompt;
    }
    assistantOpen.value = true;
  }

  function closeAssistant() {
    assistantOpen.value = false;
  }

  function getRuntimeConfig(): LLMRuntimeConfig {
    return sanitizeConfig(config.value);
  }

  async function refreshDefaultStatus() {
    loadingDefaultStatus.value = true;
    error.value = "";
    try {
      defaultStatus.value = await fetchLLMStatus();
    } catch (err) {
      console.error(err);
      defaultStatus.value = null;
      error.value = "默认本地模型状态读取失败，请检查后端服务。";
    } finally {
      loadingDefaultStatus.value = false;
    }
  }

  async function validateCurrentConfig() {
    if (config.value.mode === "local") {
      await refreshDefaultStatus();
      return defaultStatus.value;
    }

    checkingConfig.value = true;
    error.value = "";
    try {
      overrideStatus.value = await checkLLMStatus({ config: getRuntimeConfig() });
      return overrideStatus.value;
    } catch (err) {
      console.error(err);
      overrideStatus.value = null;
      error.value = "API key 配置检测失败，请检查地址、模型名和 API key。";
      throw err;
    } finally {
      checkingConfig.value = false;
    }
  }

  return {
    config,
    defaultStatus,
    overrideStatus,
    loadingDefaultStatus,
    checkingConfig,
    error,
    assistantOpen,
    assistantPrompt,
    assistantState,
    isApiKeyMode,
    activeStatus,
    hasApiKeyConfig,
    updateConfig,
    setAssistantContext,
    resetAssistantContext,
    openAssistant,
    closeAssistant,
    getRuntimeConfig,
    refreshDefaultStatus,
    validateCurrentConfig,
  };
});
