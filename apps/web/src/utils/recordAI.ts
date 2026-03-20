import type { ExperimentTemplateDetail, TemplateField } from "../types/api";

export interface RecordAISectionFieldItem {
  field_id: string;
  field_key: string;
  field_label: string;
  field_type: string;
  required: boolean;
  help_text: string;
  value: unknown;
}

export interface RecordAISectionItem {
  section_id: string;
  section_key: string;
  section_title: string;
  fields: RecordAISectionFieldItem[];
}

export function buildRecordSectionsContext(
  template: ExperimentTemplateDetail | null,
  fieldValues: Record<string, unknown>,
): RecordAISectionItem[] {
  if (!template) {
    return [];
  }

  return template.sections.map((section) => ({
    section_id: section.id,
    section_key: section.key,
    section_title: section.title,
    fields: section.fields.map((field) => ({
      field_id: field.id,
      field_key: field.key,
      field_label: field.label,
      field_type: field.field_type,
      required: field.required,
      help_text: field.help_text || "",
      value: fieldValues[field.id],
    })),
  }));
}

export function buildRecordFieldAIContext(options: {
  template: ExperimentTemplateDetail | null;
  field: TemplateField;
  fieldValue: unknown;
  page: string;
  recordId?: string;
  recordTitle?: string;
  recordStatus?: string;
  summary?: string;
  projectId?: string;
  templateName?: string;
  templateKey?: string;
  allFieldValues: Record<string, unknown>;
}) {
  return {
    page: options.page,
    record_id: options.recordId || "",
    title: options.recordTitle || "",
    status: options.recordStatus || "draft",
    project_id: options.projectId || "",
    template_name: options.templateName || options.template?.name || "",
    template_key: options.templateKey || options.template?.key || "",
    current_summary: options.summary || "",
    target_field: {
      field_id: options.field.id,
      field_key: options.field.key,
      field_label: options.field.label,
      field_type: options.field.field_type,
      required: options.field.required,
      placeholder: options.field.placeholder || "",
      help_text: options.field.help_text || "",
      current_value: options.fieldValue,
      options: options.field.options || null,
      validation_rules: options.field.validation_rules || null,
      ui_props: options.field.ui_props || null,
    },
    sections: buildRecordSectionsContext(options.template, options.allFieldValues),
  };
}

export function buildRecordQualityContext(options: {
  template: ExperimentTemplateDetail | null;
  page: string;
  recordId?: string;
  recordTitle?: string;
  recordStatus?: string;
  summary?: string;
  projectId?: string;
  projectName?: string;
  templateName?: string;
  templateKey?: string;
  fieldValues: Record<string, unknown>;
}) {
  return {
    page: options.page,
    record_id: options.recordId || "",
    title: options.recordTitle || "",
    status: options.recordStatus || "draft",
    summary: options.summary || "",
    project_id: options.projectId || "",
    project_name: options.projectName || "",
    template_name: options.templateName || options.template?.name || "",
    template_key: options.templateKey || options.template?.key || "",
    sections: buildRecordSectionsContext(options.template, options.fieldValues),
  };
}
