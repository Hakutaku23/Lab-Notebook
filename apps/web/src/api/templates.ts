import { http } from "./http";
import type {
  ExperimentTemplateDetail,
  ExperimentTemplateSummary,
  TemplateCreatePayload,
  TemplateUpdatePayload,
} from "../types/api";

export async function fetchTemplates(
  activeOnly = true,
): Promise<ExperimentTemplateSummary[]> {
  const { data } = await http.get<ExperimentTemplateSummary[]>("/templates", {
    params: { active_only: activeOnly },
  });
  return data;
}

export async function fetchTemplateDetail(
  templateId: string,
): Promise<ExperimentTemplateDetail> {
  const { data } = await http.get<ExperimentTemplateDetail>(
    `/templates/${templateId}`,
  );
  return data;
}

export async function fetchTemplateByKey(
  templateKey: string,
): Promise<ExperimentTemplateDetail> {
  const { data } = await http.get<ExperimentTemplateDetail>(
    `/templates/by-key/${templateKey}`,
  );
  return data;
}

export async function createTemplate(
  payload: TemplateCreatePayload,
): Promise<ExperimentTemplateDetail> {
  const { data } = await http.post<ExperimentTemplateDetail>("/templates", payload);
  return data;
}

export async function updateTemplate(
  templateId: string,
  payload: TemplateUpdatePayload,
): Promise<ExperimentTemplateDetail> {
  const { data } = await http.put<ExperimentTemplateDetail>(
    `/templates/${templateId}`,
    payload,
  );
  return data;
}

export async function deleteTemplate(templateId: string): Promise<void> {
  await http.delete(`/templates/${templateId}`);
}