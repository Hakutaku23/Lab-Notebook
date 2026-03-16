import { http } from "./http";
import type { ProjectCreatePayload, ProjectItem } from "../types/api";

export async function fetchProjects(): Promise<ProjectItem[]> {
  const { data } = await http.get<ProjectItem[]>("/projects");
  return data;
}

export async function fetchProjectDetail(projectId: string): Promise<ProjectItem> {
  const { data } = await http.get<ProjectItem>(`/projects/${projectId}`);
  return data;
}

export async function createProject(
  payload: ProjectCreatePayload,
): Promise<ProjectItem> {
  const { data } = await http.post<ProjectItem>("/projects", payload);
  return data;
}

export async function deleteProject(projectId: string): Promise<void> {
  await http.delete(`/projects/${projectId}`);
}