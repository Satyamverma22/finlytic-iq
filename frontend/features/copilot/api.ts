import { apiFetch } from "@/lib/api-client";

export const sendChat = (payload: { message: string; conversation_id?: string | null }) =>
  apiFetch<{ conversation_id: string; reply: string }>("/api/copilot/chat", {
    method: "POST",
    body: JSON.stringify(payload),
  });