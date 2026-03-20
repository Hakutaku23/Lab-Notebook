import type { ExperimentTemplateDetail, TemplateField } from "../types/api";

import {
  createEmptyChemicalEquationValue,
  createEmptyReactionProcessStep,
  initializeFieldValues,
  normalizeChemicalEquationValue,
  normalizeFieldValueForSubmit,
  normalizeReactionProcessValue,
  toPrettyJson,
  type ChemicalEquationValue,
  type ReactionProcessStep,
} from "./templateRuntime";

export interface FieldTypeMeta {
  key: string;
  label: string;
  category: string;
  description: string;
  acceptsStructuredValue?: boolean;
}

export interface SelectOption {
  label: string;
  value: string;
}

export type { ChemicalEquationValue, ReactionProcessStep };

export const FIELD_TYPE_REGISTRY: Record<string, FieldTypeMeta> = {
  text: { key: "text", label: "单行文本", category: "basic", description: "短文本输入。" },
  textarea: { key: "textarea", label: "多行文本", category: "basic", description: "长文本输入。" },
  richtext: { key: "richtext", label: "富文本", category: "basic", description: "当前以前端多行文本方式编辑。" },
  date: { key: "date", label: "日期", category: "basic", description: "日期输入。" },
  number: { key: "number", label: "数字", category: "basic", description: "数值输入。" },
  select: { key: "select", label: "下拉选择", category: "basic", description: "单选枚举值。" },
  checkbox: { key: "checkbox", label: "勾选项", category: "basic", description: "布尔值。" },
  json: { key: "json", label: "JSON 数据", category: "structured", description: "复杂对象。", acceptsStructuredValue: true },
  table: { key: "table", label: "表格数据", category: "structured", description: "JSON、CSV 或 Markdown 表格。", acceptsStructuredValue: true },
  file: { key: "file", label: "文件说明", category: "structured", description: "附件说明信息。", acceptsStructuredValue: true },
  chemical_equation: {
    key: "chemical_equation",
    label: "化学结构/反应式",
    category: "chemistry",
    description: "使用 Ketcher 保存分子或反应式，并保留结构源文件与预览图。",
    acceptsStructuredValue: true,
  },
  reaction_process: {
    key: "reaction_process",
    label: "反应过程步骤",
    category: "chemistry",
    description: "结构化记录反应步骤、条件和现象。",
    acceptsStructuredValue: true,
  },
};

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isBlankString(value: unknown): boolean {
  return typeof value === "string" && value.trim() === "";
}

export function initializeTemplateFieldValues(
  template: ExperimentTemplateDetail,
): Record<string, unknown> {
  return initializeFieldValues(template);
}

export function defaultFieldValue(fieldType: string): unknown {
  if (fieldType === "chemical_equation") {
    return createEmptyChemicalEquationValue();
  }
  if (fieldType === "reaction_process") {
    return [] satisfies ReactionProcessStep[];
  }
  if (fieldType === "checkbox") {
    return false;
  }
  return "";
}

export function buildSelectOptions(rawOptions: unknown): SelectOption[] {
  if (!rawOptions) return [];

  if (Array.isArray(rawOptions)) {
    return rawOptions
      .map((item) => {
        if (typeof item === "string") {
          return { label: item, value: item };
        }
        if (isPlainObject(item)) {
          return {
            label: String(item.label ?? item.value ?? ""),
            value: String(item.value ?? item.label ?? ""),
          };
        }
        return null;
      })
      .filter((item): item is SelectOption => Boolean(item?.value));
  }

  if (!isPlainObject(rawOptions)) return [];

  const nested = rawOptions.items ?? rawOptions.options ?? rawOptions.values;
  if (nested) {
    return buildSelectOptions(nested);
  }

  return Object.entries(rawOptions).map(([value, label]) => ({
    value,
    label: typeof label === "string" ? label : value,
  }));
}

export function asTextAreaValue(value: unknown): string {
  return toPrettyJson(value);
}

export function coerceChemicalEquationValue(value: unknown): ChemicalEquationValue {
  return normalizeChemicalEquationValue(value) ?? createEmptyChemicalEquationValue();
}

export function emptyReactionProcessStep(): ReactionProcessStep {
  return createEmptyReactionProcessStep();
}

export function coerceReactionProcessSteps(value: unknown): ReactionProcessStep[] {
  return normalizeReactionProcessValue(value);
}

export function normalizeFieldValue(field: TemplateField, value: unknown): unknown {
  return normalizeFieldValueForSubmit(field, value);
}

export function formatFieldValue(field: TemplateField, value: unknown): string {
  if (value === null || value === undefined || isBlankString(value)) {
    return "无";
  }

  if (field.field_type === "checkbox") {
    return value ? "已勾选" : "未勾选";
  }

  if (field.field_type === "select") {
    const options = buildSelectOptions(field.options);
    const matched = options.find((item) => item.value === String(value));
    return matched?.label ?? String(value);
  }

  if (field.field_type === "chemical_equation") {
    const normalized = coerceChemicalEquationValue(value);
    return normalized.plain_text || normalized.smiles || normalized.rxnfile || normalized.molfile || normalized.ket || "无";
  }

  if (field.field_type === "reaction_process") {
    const steps = coerceReactionProcessSteps(value);
    return steps.length > 0 ? toPrettyJson(steps) : "无";
  }

  if (typeof value === "string") return value;

  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}
