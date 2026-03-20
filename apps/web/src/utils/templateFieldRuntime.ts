import type { ExperimentTemplateDetail, RecordFieldValuePayload, TemplateField } from "../types/api";

export interface ChemicalEquationValue {
  mode?: "structured" | "manual";
  reactants?: string[];
  products?: string[];
  arrow?: string;
  conditions?: string;
  equation_text?: string;
}

export interface ReactionProcessStep {
  title?: string;
  operation?: string;
  condition?: string;
  observation?: string;
  expected_result?: string;
}

export function createDefaultFieldValue(field: TemplateField): unknown {
  if (field.default_value !== undefined && field.default_value !== null) {
    return field.default_value;
  }

  switch (field.field_type) {
    case "checkbox":
      return false;
    case "reaction_process":
      return [] as ReactionProcessStep[];
    case "chemical_equation":
      return {
        mode: field.ui_props?.mode === "manual" ? "manual" : "structured",
        reactants: [],
        products: [],
        arrow: typeof field.ui_props?.arrow === "string" ? field.ui_props.arrow : "→",
        conditions: "",
        equation_text: "",
      } as ChemicalEquationValue;
    default:
      return "";
  }
}

export function initializeTemplateFieldValues(template: ExperimentTemplateDetail): Record<string, unknown> {
  const nextValues: Record<string, unknown> = {};
  template.sections.forEach((section) => {
    section.fields.forEach((field) => {
      nextValues[field.id] = createDefaultFieldValue(field);
    });
  });
  return nextValues;
}

function normalizeChemicalEquationValue(value: unknown): unknown {
  if (typeof value === "string") {
    return value.trim();
  }

  if (!value || typeof value !== "object") {
    return "";
  }

  const input = value as ChemicalEquationValue;
  const reactants = (input.reactants ?? []).map((item) => String(item).trim()).filter(Boolean);
  const products = (input.products ?? []).map((item) => String(item).trim()).filter(Boolean);
  const conditions = String(input.conditions ?? "").trim();
  const manualText = String(input.equation_text ?? "").trim();
  const arrow = String(input.arrow ?? "→").trim() || "→";
  const mode = input.mode === "manual" ? "manual" : "structured";

  const preview = reactants.length || products.length ? `${reactants.join(" + ")} ${arrow} ${products.join(" + ")}`.trim() : "";
  const equationText = mode === "manual" ? manualText : preview || manualText;

  if (!equationText && !conditions) {
    return "";
  }

  return {
    mode,
    ...(reactants.length ? { reactants } : {}),
    ...(products.length ? { products } : {}),
    ...(conditions ? { conditions } : {}),
    ...(arrow ? { arrow } : {}),
    equation_text: equationText,
  } satisfies ChemicalEquationValue;
}

function normalizeReactionProcessValue(value: unknown): unknown {
  if (!Array.isArray(value)) {
    return [];
  }

  const cleaned = value
    .map((item) => {
      const step = item as ReactionProcessStep;
      return {
        title: String(step?.title ?? "").trim(),
        operation: String(step?.operation ?? "").trim(),
        condition: String(step?.condition ?? "").trim(),
        observation: String(step?.observation ?? "").trim(),
        expected_result: String(step?.expected_result ?? "").trim(),
      } satisfies ReactionProcessStep;
    })
    .filter((item) => Object.values(item).some(Boolean));

  return cleaned;
}

export function normalizeTemplateFieldValue(field: TemplateField, value: unknown): unknown {
  if (field.field_type === "checkbox") {
    return Boolean(value);
  }

  if (field.field_type === "number") {
    if (typeof value === "number") {
      return Number.isFinite(value) ? value : "";
    }
    if (typeof value === "string") {
      const trimmed = value.trim();
      return trimmed === "" ? "" : Number(trimmed);
    }
    return value;
  }

  if (field.field_type === "chemical_equation") {
    return normalizeChemicalEquationValue(value);
  }

  if (field.field_type === "reaction_process") {
    return normalizeReactionProcessValue(value);
  }

  if (typeof value !== "string") {
    return value;
  }

  const trimmed = value.trim();
  if (!trimmed) {
    return "";
  }

  if (["table", "file", "json"].includes(field.field_type)) {
    try {
      return JSON.parse(trimmed);
    } catch {
      return value;
    }
  }

  return value;
}

export function buildRecordValuePayload(
  template: ExperimentTemplateDetail,
  values: Record<string, unknown>,
): RecordFieldValuePayload[] {
  return template.sections.flatMap((section) =>
    section.fields.map((field) => ({
      field_id: field.id,
      value_json: normalizeTemplateFieldValue(field, values[field.id]),
    })),
  );
}
