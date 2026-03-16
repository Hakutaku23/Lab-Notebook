import { http } from "./http";
import type {
  ExperimentTemplateDetail,
  ExperimentTemplateSummary,
  TemplateCreatePayload,
  TemplateLineage,
  TemplateUpdatePayload,
  TemplateVersionCreatePayload,
} from "../types/api";

export async function fetchTemplates(
  activeOnly = true,
): Promise<ExperimentTemplateSummary[]> {
  const { data } = await http.get("/templates", {
    params: { active_only: activeOnly },
  });
  return data;
}

export async function fetchTemplateDetail(
  templateId: string,
): Promise<ExperimentTemplateDetail> {
  const { data } = await http.get(`/templates/${templateId}`);
  return data;
}

export async function fetchTemplateByKey(
  templateKey: string,
): Promise<ExperimentTemplateDetail> {
  const { data } = await http.get(`/templates/by-key/${templateKey}`);
  return data;
}

export async function createTemplate(
  payload: TemplateCreatePayload,
): Promise<ExperimentTemplateDetail> {
  const { data } = await http.post("/templates", payload);
  return data;
}

export async function updateTemplate(
  templateId: string,
  payload: TemplateUpdatePayload,
): Promise<ExperimentTemplateDetail> {
  const { data } = await http.put(`/templates/${templateId}`, payload);
  return data;
}

export async function createTemplateVersion(
  templateId: string,
  payload: TemplateVersionCreatePayload,
): Promise<ExperimentTemplateDetail> {
  const { data } = await http.post(`/templates/${templateId}/versions`, payload);
  return data;
}

export async function deleteTemplate(templateId: string): Promise<void> {
  await http.delete(`/templates/${templateId}`);
}

export async function fetchTemplateLineage(
  templateId: string,
): Promise<TemplateLineage> {
  const { data } = await http.get(`/templates/${templateId}/lineage`);
  return data;
}