export const RECORD_STATUS_LABELS: Record<string, string> = {
  draft: "草稿",
  submitted: "待审核",
  approved: "已通过",
};

export function getRecordStatusLabel(status: string): string {
  return RECORD_STATUS_LABELS[status] || status;
}
