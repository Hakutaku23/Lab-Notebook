<script setup lang="ts">
import { computed, ref } from "vue";

import { generateLLMContent } from "../api/llm";
import { useAIStore } from "../stores/ai";

const props = defineProps<{
  templateName: string;
  templateKey: string;
  category: string;
  descriptionText: string;
  sectionsText: string;
}>();

const emit = defineEmits<{
  apply: [sectionsText: string];
}>();

const aiStore = useAIStore();

const instruction = ref("");
const generatedSections = ref("");
const loading = ref(false);
const error = ref("");
const successText = ref("");

const isConfigured = computed(() => {
  if (aiStore.config.mode === "api_key") {
    return aiStore.hasApiKeyConfig;
  }
  return aiStore.activeStatus?.configured ?? true;
});

function stripCodeFence(value: string) {
  return value
    .trim()
    .replace(/^```json\s*/i, "")
    .replace(/^```\s*/i, "")
    .replace(/\s*```$/i, "")
    .trim();
}

function normalizeGeneratedSections(content: string) {
  const cleaned = stripCodeFence(content);
  const parsed = JSON.parse(cleaned) as unknown;
  if (Array.isArray(parsed)) {
    return JSON.stringify(parsed, null, 2);
  }
  if (parsed && typeof parsed === "object" && Array.isArray((parsed as { sections?: unknown }).sections)) {
    return JSON.stringify((parsed as { sections: unknown[] }).sections, null, 2);
  }
  throw new Error("AI 返回的内容不是合法的 sections JSON。");
}

async function generateSections() {
  loading.value = true;
  error.value = "";
  successText.value = "";

  try {
    const result = await generateLLMContent({
      task: "template_json",
      prompt:
        instruction.value.trim() ||
        "请根据当前模板信息，生成一份适合实验记录系统使用的 sections JSON。",
      context: {
        template_name: props.templateName,
        template_key: props.templateKey,
        category: props.category,
        description: props.descriptionText,
        current_sections_json: props.sectionsText,
      },
      config: aiStore.getRuntimeConfig(),
    });

    generatedSections.value = normalizeGeneratedSections(result.content);
    successText.value = "AI 已生成新的 sections JSON，你可以先预览，再决定是否应用。";
  } catch (err: any) {
    console.error(err);
    error.value =
      err?.response?.data?.detail || err?.message || "AI 生成模板 JSON 失败，请检查模型配置或提示词。";
  } finally {
    loading.value = false;
  }
}

function applyGeneratedSections() {
  if (!generatedSections.value) {
    return;
  }
  emit("apply", generatedSections.value);
  successText.value = "AI 生成的 sections JSON 已应用到编辑区。";
}
</script>

<template>
  <section class="card stack">
    <div class="section-header">
      <div>
        <h3>AI 生成模板 JSON</h3>
        <p class="muted">输入模板需求后，AI 会尝试生成可直接应用到 Sections JSON 的结构。</p>
      </div>
      <span class="badge">{{ aiStore.config.mode === "api_key" ? "API key" : "本地模型" }}</span>
    </div>

    <div class="form-item">
      <label class="label">生成要求</label>
      <textarea
        v-model="instruction"
        class="textarea"
        rows="5"
        placeholder="例如：生成一个适用于有机合成实验的模板，需要包含试剂信息、反应方程式、反应步骤、产物表征、安全注意事项。"
      />
    </div>

    <div class="actions">
      <button class="button" type="button" :disabled="loading || !isConfigured" @click="generateSections">
        {{ loading ? "生成中..." : "生成 Sections JSON" }}
      </button>
      <button class="button secondary" type="button" :disabled="!generatedSections" @click="applyGeneratedSections">
        应用到编辑区
      </button>
    </div>

    <p v-if="!isConfigured" class="muted">当前模式尚未配置完成，请先在 AI 设置中补齐模型信息。</p>
    <p v-if="successText" class="muted">{{ successText }}</p>
    <p v-if="error" class="error-text">{{ error }}</p>

    <div v-if="generatedSections" class="form-item">
      <label class="label">生成结果预览</label>
      <textarea class="textarea code-area ai-result-area" :value="generatedSections" rows="12" readonly />
    </div>
  </section>
</template>
