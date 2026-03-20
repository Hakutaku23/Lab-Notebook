import type { ExperimentTemplateDetail, RecordFieldValueItem, TemplateField } from "../types/api";

export interface ChemicalEquationValue {
  kind?: "reaction" | "molecule";
  ket?: string | null;
  rxnfile?: string | null;
  molfile?: string | null;
  smiles?: string | null;
  svg?: string | null;
  plain_text?: string | null;
}

export interface ReactionProcessStep {
  title: string;
  operation?: string;
  reagent?: string;
  condition?: string;
  observation?: string;
  note?: string;
}

export function getFieldDefaultValue(field: TemplateField): unknown {
  if (field.default_value !== undefined && field.default_value !== null) {
    return field.default_value;
  }

  switch (field.field_type) {
    case "checkbox":
      return false;
    case "number":
      return "";
    case "json":
    case "table":
      return [];
    case "file":
      return [];
    case "reaction_process":
      return [];
    case "chemical_equation":
      return {
        kind: "molecule",
        ket: "",
        rxnfile: "",
        molfile: "",
        smiles: "",
        svg: "",
        plain_text: "",
      } satisfies ChemicalEquationValue;
    default:
      return "";
  }
}

export function initializeFieldValues(
  template: ExperimentTemplateDetail,
  existingValues?: Record<string, unknown>,
): Record<string, unknown> {
  const nextValues: Record<string, unknown> = {};

  template.sections.forEach((section) => {
    section.fields.forEach((field) => {
      const existing = existingValues?.[field.id];
      nextValues[field.id] = existing !== undefined ? existing : getFieldDefaultValue(field);
    });
  });

  return nextValues;
}

export function mapRecordValues(items: RecordFieldValueItem[]): Record<string, unknown> {
  const mapped: Record<string, unknown> = {};
  items.forEach((item) => {
    mapped[item.field_id] = item.value_json;
  });
  return mapped;
}

function parseJsonLike(value: string): unknown {
  const trimmed = value.trim();
  if (!trimmed) return "";
  try {
    return JSON.parse(trimmed);
  } catch {
    return value;
  }
}

function normalizeReactionProcess(value: unknown): ReactionProcessStep[] | string {
  if (Array.isArray(value)) {
    return value as ReactionProcessStep[];
  }

  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) return [];
    try {
      const parsed = JSON.parse(trimmed);
      if (Array.isArray(parsed)) return parsed as ReactionProcessStep[];
      return trimmed;
    } catch {
      return trimmed
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => ({ title: line }));
    }
  }

  return [];
}

function normalizeChemicalEquation(value: unknown): ChemicalEquationValue | string | null {
  if (value === null || value === undefined) return null;
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed ? { plain_text: trimmed } : null;
  }
  if (typeof value === "object") {
    return value as ChemicalEquationValue;
  }
  return null;
}

export function normalizeFieldValueForSubmit(field: TemplateField, value: unknown): unknown {
  if (value === undefined) return null;

  switch (field.field_type) {
    case "checkbox":
      return Boolean(value);
    case "number": {
      if (value === "" || value === null) return null;
      const numberValue = typeof value === "number" ? value : Number(value);
      return Number.isFinite(numberValue) ? numberValue : value;
    }
    case "json":
    case "table":
    case "file":
      return typeof value === "string" ? parseJsonLike(value) : value;
    case "reaction_process":
      return normalizeReactionProcess(value);
    case "chemical_equation":
      return normalizeChemicalEquation(value);
    default:
      return value;
  }
}

export function buildRecordPayloadValues(
  template: ExperimentTemplateDetail,
  values: Record<string, unknown>,
): Array<{ field_id: string; value_json: unknown }> {
  return template.sections.flatMap((section) =>
    section.fields.map((field) => ({
      field_id: field.id,
      value_json: normalizeFieldValueForSubmit(field, values[field.id]),
    })),
  );
}

export function toPrettyJson(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}
