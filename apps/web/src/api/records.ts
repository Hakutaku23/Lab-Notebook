import { http } from "./http";
import type {
  ExperimentRecordDetail,
  ExperimentRecordSummary,
  RecordCreatePayload,
  RecordUpdatePayload,
  RecordVersionCompareResult,
  RecordVersionDetail,
  RecordVersionSummary,
  SnapshotCreatePayload,
} from "../types/api";

export async function fetchRecords(params?: {
  project_id?: string;
  template_id?: string;
  status?: string;
}): Promise<ExperimentRecordSummary[]> {
  const { data } = await http.get("/records", { params });
  return data;
}

export async function fetchRecordDetail(recordId: string): Promise<ExperimentRecordDetail> {
  const { data } = await http.get(`/records/${recordId}`);
  return data;
}

export async function createRecord(payload: RecordCreatePayload): Promise<ExperimentRecordDetail> {
  const { data } = await http.post("/records", payload);
  return data;
}

export async function updateRecord(recordId: string, payload: RecordUpdatePayload): Promise<ExperimentRecordDetail> {
  const { data } = await http.put(`/records/${recordId}`, payload);
  return data;
}

export async function deleteRecord(recordId: string): Promise<void> {
  await http.delete(`/records/${recordId}`);
}

export async function fetchRecordVersions(recordId: string): Promise<RecordVersionSummary[]> {
  const { data } = await http.get(`/records/${recordId}/versions`);
  return data;
}

export async function fetchRecordVersionDetail(recordId: string, versionId: string): Promise<RecordVersionDetail> {
  const { data } = await http.get(`/records/${recordId}/versions/${versionId}`);
  return data;
}

export async function compareRecordVersions(
  recordId: string,
  fromVersionId: string,
  toVersionId: string,
): Promise<RecordVersionCompareResult> {
  const { data } = await http.get(`/records/${recordId}/versions/compare`, {
    params: { from_version_id: fromVersionId, to_version_id: toVersionId },
  });
  return data;
}

export async function createManualSnapshot(
  recordId: string,
  payload: SnapshotCreatePayload,
): Promise<RecordVersionDetail> {
  const { data } = await http.post(`/records/${recordId}/versions/snapshot`, payload);
  return data;
}
