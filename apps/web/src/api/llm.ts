import { http } from "./http";
import type { LLMStatus } from "../types/api";

export async function fetchLLMStatus(): Promise<LLMStatus> {
  const { data } = await http.get("/llm/status");
  return data;
}
