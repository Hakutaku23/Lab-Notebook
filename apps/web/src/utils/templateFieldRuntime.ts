import type { ExperimentTemplateDetail, RecordFieldValuePayload, TemplateField } from "../types/api";

import {
  buildRecordPayloadValues,
  createEmptyChemicalEquationValue,
  createEmptyReactionProcessStep,
  getFieldDefaultValue,
  initializeFieldValues,
  normalizeChemicalEquationValue,
  normalizeFieldValueForSubmit,
  normalizeReactionProcessValue,
  toPrettyJson,
} from "./templateRuntime";

export type {
  ChemicalEquationValue,
  ReactionProcessStep,
} from "./templateRuntime";

export function createDefaultFieldValue(field: TemplateField): unknown {
  if (field.field_type === "chemical_equation") {
    return createEmptyChemicalEquationValue();
  }

  if (field.field_type === "reaction_process") {
    return [];
  }

  return getFieldDefaultValue(field);
}

export function initializeTemplateFieldValues(template: ExperimentTemplateDetail): Record<string, unknown> {
  return initializeFieldValues(template);
}

export function normalizeTemplateFieldValue(field: TemplateField, value: unknown): unknown {
  return normalizeFieldValueForSubmit(field, value);
}

export function buildRecordValuePayload(
  template: ExperimentTemplateDetail,
  values: Record<string, unknown>,
): RecordFieldValuePayload[] {
  return buildRecordPayloadValues(template, values);
}

export function asTextAreaValue(value: unknown): string {
  return toPrettyJson(value);
}

export {
  createEmptyChemicalEquationValue,
  createEmptyReactionProcessStep,
  normalizeChemicalEquationValue,
  normalizeReactionProcessValue,
};
