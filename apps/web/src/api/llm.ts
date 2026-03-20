import { http } from "./http";
import type {
  LLMGeneratePayload,
  LLMGenerateResult,
  LLMStatus,
  LLMStatusCheckPayload,
} from "../types/api";

export async function fetchLLMStatus(): Promise<LLMStatus> {
  const { data } = await http.get("/llm/status");
  return data;
}

export async function checkLLMStatus(payload: LLMStatusCheckPayload): Promise<LLMStatus> {
  const { data } = await http.post("/llm/status/check", payload);
  return data;
}

export async function generateLLMContent(payload: LLMGeneratePayload): Promise<LLMGenerateResult> {
  const { data } = await http.post("/llm/generate", payload);
  return data;
}
