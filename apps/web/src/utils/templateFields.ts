import type { ExperimentTemplateDetail, TemplateField } from "../types/api";

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

export interface ChemicalEquationValue {
  equation: string;
  conditions: string;
  notes: string;
}

export interface ReactionProcessStep {
  title: string;
  description: string;
  conditions: string;
  observation: string;
}

export const FIELD_TYPE_REGISTRY: Record<string, FieldTypeMeta> = {
  text: {
    key: "text",
    label: "单行文本",
    category: "basic",
    description: "短文本输入。",
  },
  textarea: {
    key: "textarea",
    label: "多行文本",
    category: "basic",
    description: "长文本输入。",
  },
  richtext: {
    key: "richtext",
    label: "富文本",
    category: "basic",
    description: "当前以前端多行文本方式编辑。",
  },
  date: {
    key: "date",
    label: "日期",
    category: "basic",
    description: "日期输入。",
  },
  number: {
    key: "number",
    label: "数字",
    category: "basic",
    description: "数值输入。",
  },
  select: {
    key: "select",
    label: "下拉选择",
    category: "basic",
    description: "单选枚举值。",
  },
  checkbox: {
    key: "checkbox",
    label: "勾选项",
    category: "basic",
    description: "布尔值。",
  },
  json: {
    key: "json",
    label: "JSON 数据",
    category: "structured",
    description: "复杂对象。",
    acceptsStructuredValue: true,
  },
  table: {
    key: "table",
    label: "表格数据",
    category: "structured",
    description: "JSON、CSV 或 Markdown 表格。",
    acceptsStructuredValue: true,
  },
  file: {
    key: "file",
    label: "文件说明",
    category: "structured",
    description: "附件说明信息。",
    acceptsStructuredValue: true,
  },
  chemical_equation: {
    key: "chemical_equation",
    label: "化学反应方程式",
    category: "chemistry",
    description: "记录反应式、条件与备注。",
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

function safeString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

export function initializeTemplateFieldValues(
  template: ExperimentTemplateDetail,
): Record<string, unknown> {
  const nextValues: Record<string, unknown> = {};

  template.sections.forEach((section) => {
    section.fields.forEach((field) => {
      nextValues[field.id] =
        field.default_value !== undefined && field.default_value !== null
          ? field.default_value
          : defaultFieldValue(field.field_type);
    });
  });

  return nextValues;
}

export function defaultFieldValue(fieldType: string): unknown {
  if (fieldType === "checkbox") return false;
  if (fieldType === "chemical_equation") {
    return { equation: "", conditions: "", notes: "" } satisfies ChemicalEquationValue;
  }
  if (fieldType === "reaction_process") {
    return [] satisfies ReactionProcessStep[];
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
            label: safeString(item.label ?? item.value),
            value: safeString(item.value ?? item.label),
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
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

export function coerceChemicalEquationValue(value: unknown): ChemicalEquationValue {
  if (!isPlainObject(value)) {
    return { equation: "", conditions: "", notes: "" };
  }

  return {
    equation: safeString(value.equation),
    conditions: safeString(value.conditions),
    notes: safeString(value.notes),
  };
}

export function emptyReactionProcessStep(): ReactionProcessStep {
  return {
    title: "",
    description: "",
    conditions: "",
    observation: "",
  };
}

export function coerceReactionProcessSteps(value: unknown): ReactionProcessStep[] {
  if (!Array.isArray(value)) return [];

  return value.map((item) => {
    if (!isPlainObject(item)) return emptyReactionProcessStep();
    return {
      title: safeString(item.title),
      description: safeString(item.description),
      conditions: safeString(item.conditions),
      observation: safeString(item.observation),
    };
  });
}

export function normalizeFieldValue(field: TemplateField, value: unknown): unknown {
  if (field.field_type === "checkbox") {
    return Boolean(value);
  }

  if (field.field_type === "number") {
    if (typeof value === "number") return Number.isFinite(value) ? value : "";
    if (typeof value !== "string") return value;
    const trimmed = value.trim();
    return trimmed === "" ? "" : Number(trimmed);
  }

  if (field.field_type === "chemical_equation") {
    const next = coerceChemicalEquationValue(value);
    const hasContent = Object.values(next).some((item) => item.trim() !== "");
    return hasContent ? next : "";
  }

  if (field.field_type === "reaction_process") {
    const next = coerceReactionProcessSteps(value).filter((step) =>
      Object.values(step).some((item) => item.trim() !== ""),
    );
    return next.length > 0 ? next : "";
  }

  if (typeof value !== "string") {
    return value;
  }

  const trimmed = value.trim();
  if (!trimmed) return "";

  if (["json", "table", "file"].includes(field.field_type)) {
    try {
      return JSON.parse(trimmed);
    } catch {
      return value;
    }
  }

  return value;
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

  if (typeof value === "string") return value;

  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}
