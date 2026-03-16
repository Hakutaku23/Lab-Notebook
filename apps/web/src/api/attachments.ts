import { http } from "./http";
import type { AttachmentItem } from "../types/api";

export async function fetchAttachments(recordId: string): Promise<AttachmentItem[]> {
  const { data } = await http.get<AttachmentItem[]>(
    `/records/${recordId}/attachments`,
  );
  return data;
}

export async function uploadAttachment(
  recordId: string,
  file: File,
  description?: string,
  uploadedBy?: string,
): Promise<AttachmentItem> {
  const form = new FormData();
  form.append("file", file);
  if (description) {
    form.append("description", description);
  }
  if (uploadedBy) {
    form.append("uploaded_by", uploadedBy);
  }

  const { data } = await http.post<AttachmentItem>(
    `/records/${recordId}/attachments`,
    form,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    },
  );
  return data;
}

export async function deleteAttachment(attachmentId: string): Promise<void> {
  await http.delete(`/attachments/${attachmentId}`);
}