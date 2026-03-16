import { http } from "./http";
import type { AuditLogItem, AuditLogQuery } from "../types/api";

export async function fetchAuditLogs(
  params: AuditLogQuery = {},
): Promise<AuditLogItem[]> {
  const cleanedParams = Object.fromEntries(
    Object.entries(params).filter(([, value]) => {
      return value !== undefined && value !== null && value !== "";
    }),
  );

  const { data } = await http.get("/audit-logs", {
    params: cleanedParams,
  });

  return data;
}