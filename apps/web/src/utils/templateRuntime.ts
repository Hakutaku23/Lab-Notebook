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

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function cleanString(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

export function isStructuredChemicalSource(value: string): boolean {
  const trimmed = value.trim();
  return (
    trimmed.startsWith("$RXN") ||
    trimmed.includes("M  END") ||
    (trimmed.startsWith("{") && trimmed.endsWith("}"))
  );
}

export function createEmptyChemicalEquationValue(
  kind: ChemicalEquationValue["kind"] = "molecule",
): ChemicalEquationValue {
  return {
    kind,
    ket: "",
    rxnfile: "",
    molfile: "",
    smiles: "",
    svg: "",
    plain_text: "",
  };
}

export function createEmptyReactionProcessStep(): ReactionProcessStep {
  return {
    title: "",
    operation: "",
    reagent: "",
    condition: "",
    observation: "",
    note: "",
  };
}

export function normalizeChemicalEquationValue(value: unknown): ChemicalEquationValue | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (typeof value === "string") {
    const plainText = value.trim();
    if (!plainText) return null;

    const next = createEmptyChemicalEquationValue(
      plainText.startsWith("$RXN") ? "reaction" : "molecule",
    );
    next.plain_text = plainText;
    return next;
  }

  if (!isPlainObject(value)) {
    return null;
  }

  const ket = cleanString(value.ket);
  const rxnfile = cleanString(value.rxnfile);
  const molfile = cleanString(value.molfile);
  const smiles = cleanString(value.smiles);
  const svg = cleanString(value.svg);
  const plainTextInput = cleanString(value.plain_text);

  const kind =
    value.kind === "reaction" || rxnfile
      ? "reaction"
      : value.kind === "molecule"
        ? "molecule"
        : "molecule";

  const plainText = plainTextInput || smiles || rxnfile || molfile || ket || "";
  if (!plainText && !svg) {
    return null;
  }

  return {
    kind,
    ket,
    rxnfile,
    molfile,
    smiles,
    svg,
    plain_text: plainText,
  };
}

export function normalizeReactionProcessValue(value: unknown): ReactionProcessStep[] {
  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (!isPlainObject(item)) {
          return createEmptyReactionProcessStep();
        }

        return {
          title: cleanString(item.title),
          operation: cleanString(item.operation),
          reagent: cleanString(item.reagent),
          condition: cleanString(item.condition),
          observation: cleanString(item.observation),
          note: cleanString(item.note),
        } satisfies ReactionProcessStep;
      })
      .filter((item) => Object.values(item).some(Boolean));
  }

  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) return [];

    try {
      const parsed = JSON.parse(trimmed);
      return normalizeReactionProcessValue(parsed);
    } catch {
      return trimmed
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => ({
          title: line,
          operation: "",
          reagent: "",
          condition: "",
          observation: "",
          note: "",
        }));
    }
  }

  return [];
}

export function getChemicalEquationSource(value: unknown): string {
  const normalized = normalizeChemicalEquationValue(value);
  if (!normalized) return "";

  return (
    normalized.rxnfile ||
    normalized.molfile ||
    normalized.ket ||
    normalized.smiles ||
    normalized.plain_text ||
    ""
  );
}

export function getChemicalEquationPreviewSource(value: unknown): string {
  const normalized = normalizeChemicalEquationValue(value);
  if (!normalized) return "";

  return (
    normalized.rxnfile ||
    normalized.molfile ||
    normalized.ket ||
    (normalized.plain_text && isStructuredChemicalSource(normalized.plain_text)
      ? normalized.plain_text
      : "")
  );
}

export function getChemicalEquationDisplayText(value: unknown): string {
  const normalized = normalizeChemicalEquationValue(value);
  if (!normalized) return "";

  return (
    normalized.plain_text ||
    normalized.smiles ||
    normalized.rxnfile ||
    normalized.molfile ||
    normalized.ket ||
    ""
  );
}

export function getFieldDefaultValue(field: TemplateField): unknown {
  if (field.default_value !== undefined && field.default_value !== null) {
    return normalizeFieldValueForForm(field, field.default_value);
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
      return createEmptyChemicalEquationValue();
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
      nextValues[field.id] =
        existing !== undefined
          ? normalizeFieldValueForForm(field, existing)
          : getFieldDefaultValue(field);
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

export function normalizeFieldValueForForm(field: TemplateField, value: unknown): unknown {
  switch (field.field_type) {
    case "checkbox":
      return Boolean(value);
    case "reaction_process":
      return normalizeReactionProcessValue(value);
    case "chemical_equation":
      return normalizeChemicalEquationValue(value) ?? createEmptyChemicalEquationValue();
    default:
      return value;
  }
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
    case "reaction_process": {
      const normalized = normalizeReactionProcessValue(value);
      return normalized.length > 0 ? normalized : null;
    }
    case "chemical_equation":
      return normalizeChemicalEquationValue(value);
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
