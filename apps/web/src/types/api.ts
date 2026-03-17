export interface TemplateField {
  id: string;
  key: string;
  label: string;
  field_type: string;
  required: boolean;
  order_index: number;
  placeholder?: string | null;
  help_text?: string | null;
  default_value?: unknown;
  options?: Record<string, unknown> | null;
  validation_rules?: Record<string, unknown> | null;
  ui_props?: Record<string, unknown> | null;
}

export interface TemplateSection {
  id: string;
  key: string;
  title: string;
  description?: string | null;
  order_index: number;
  is_repeatable: boolean;
  fields: TemplateField[];
}

export interface TemplateFieldPayload {
  key: string;
  label: string;
  field_type: string;
  required: boolean;
  order_index: number;
  placeholder?: string | null;
  help_text?: string | null;
  default_value?: unknown;
  options?: Record<string, unknown> | null;
  validation_rules?: Record<string, unknown> | null;
  ui_props?: Record<string, unknown> | null;
}

export interface TemplateSectionPayload {
  key: string;
  title: string;
  description?: string | null;
  order_index: number;
  is_repeatable: boolean;
  fields: TemplateFieldPayload[];
}

export interface ExperimentTemplateSummary {
  id: string;
  name: string;
  key: string;
  description?: string | null;
  category: string;
  version: number;
  is_system: boolean;
  is_active: boolean;
  parent_template_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExperimentTemplateDetail extends ExperimentTemplateSummary {
  sections: TemplateSection[];
}

export interface TemplateCreatePayload {
  name: string;
  key: string;
  description?: string;
  category: string;
  parent_template_id?: string | null;
  created_by?: string;
  is_active: boolean;
  sections: TemplateSectionPayload[];
}

export interface TemplateUpdatePayload {
  name: string;
  key: string;
  description?: string;
  category: string;
  parent_template_id?: string | null;
  is_active: boolean;
  sections: TemplateSectionPayload[];
}

export interface ProjectItem {
  id: string;
  name: string;
  code?: string | null;
  description?: string | null;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreatePayload {
  name: string;
  code?: string;
  description?: string;
  owner_id?: string;
}

export interface RecordFieldValuePayload {
  field_id: string;
  value_json: unknown;
  note?: string | null;
}

export interface RecordCreatePayload {
  title: string;
  status: string;
  summary?: string;
  project_id: string;
  template_id: string;
  created_by?: string;
  values: RecordFieldValuePayload[];
}

export interface RecordUpdatePayload {
  title?: string;
  status?: string;
  summary?: string;
  values?: RecordFieldValuePayload[];
}

export type RecordWorkflowAction = "submit" | "withdraw" | "approve" | "reopen";

export interface RecordWorkflowPayload {
  action: RecordWorkflowAction;
  comment?: string | null;
}

export interface RecordFieldValueItem {
  id: string;
  field_id: string;
  section_key_snapshot: string;
  field_key_snapshot: string;
  field_label_snapshot: string;
  field_type_snapshot: string;
  value_json: unknown;
  note?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AttachmentItem {
  id: string;
  record_id: string;
  uploaded_by?: string | null;
  original_name: string;
  stored_name: string;
  mime_type?: string | null;
  size_bytes: number;
  description?: string | null;
  created_at: string;
  updated_at: string;
  download_url: string;
}

export interface RecordVersionSummary {
  id: string;
  record_id: string;
  created_by?: string | null;
  version_no: number;
  comment?: string | null;
  created_at: string;
  updated_at: string;
}

export interface RecordVersionDetail extends RecordVersionSummary {
  snapshot_json: Record<string, unknown>;
}

export interface SnapshotCreatePayload {
  comment?: string;
  created_by?: string;
}

export interface RestoreVersionPayload {
  comment?: string | null;
}

export interface ExperimentRecordSummary {
  id: string;
  title: string;
  status: string;
  summary?: string | null;
  project_id: string;
  project_name?: string | null;
  template_id: string;
  template_name?: string | null;
  template_version: number;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface ExperimentRecordDetail extends ExperimentRecordSummary {
  values: RecordFieldValueItem[];
  attachments: AttachmentItem[];
  allowed_actions?: RecordWorkflowAction[];
}

export interface AuditLogItem {
  id: string;
  actor_id?: string | null;
  actor_username?: string | null;
  action: string;
  resource_type: string;
  resource_id?: string | null;
  summary: string;
  detail_json?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface RecordDiffItem {
  group: string;
  key: string;
  label: string;
  change_type: string;
  before: unknown;
  after: unknown;
}

export interface RecordVersionCompareResult {
  from_version: RecordVersionSummary;
  to_version: RecordVersionSummary;
  change_count: number;
  items: RecordDiffItem[];
}

export interface LLMStatus {
  provider: string;
  model?: string | null;
  enabled: boolean;
  supports_generation: boolean;
  message: string;
}

export interface AuthUser {
  id: string;
  username: string;
  email?: string | null;
  full_name?: string | null;
  role?: string | null;
  is_active?: boolean;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  full_name?: string | null;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in?: number | null;
  user: AuthUser | null;
}

export interface AuditLogQuery {
  resource_type?: string;
  resource_id?: string;
  actor_id?: string;
  action?: string;
  limit?: number;
}

export interface TemplateVersionCreatePayload {
  key: string;
  name?: string | null;
  description?: string | null;
  category?: string | null;
  created_by?: string | null;
  is_active?: boolean;
  sections?: TemplateSectionPayload[] | null;
}

export interface TemplateLineage {
  root_template_id: string;
  current_template_id: string;
  items: ExperimentTemplateSummary[];
}
