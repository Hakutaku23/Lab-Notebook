import { http } from "./http";
import type { AuditLogItem } from "../types/api";

export async function fetchAuditLogs(params: {
  resource_type: string;
  resource_id: string;
  limit?: number;
}): Promise<AuditLogItem[]> {
  const { data } = await http.get("/audit-logs", { params });
  return data;
}
