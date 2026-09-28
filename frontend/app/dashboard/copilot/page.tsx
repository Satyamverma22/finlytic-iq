"use client";
import { useEffect, useRef, useState } from "react";
import { sendChat } from "@/features/copilot/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface ChatMessage {
  role: "user" | "model";
  content: string;
}

export default function CopilotPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const onSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setMessages((m) => [...m, { role: "user", content: text }]);
    setInput("");
    setLoading(true);

    try {
      const res = await sendChat({ message: text, conversation_id: conversationId });
      setConversationId(res.conversation_id);
      setMessages((m) => [...m, { role: "model", content: res.reply }]);
    } catch (e: any) {
      setMessages((m) => [...m, { role: "model", content: `Error: ${e.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl flex flex-col h-[calc(100vh-3rem)]">
      <div className="flex items-center justify-between mb-3">
        <h1 className="text-2xl font-semibold">AI Copilot</h1>
        <Button
          variant="outline"
          size="sm"
          onClick={() => { setMessages([]); setConversationId(null); }}
        >
          New chat
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto border rounded-md p-4 space-y-3">
        {messages.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Ask about your financial health, simulate a loan, find schemes, or check a suspicious message.
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
            <span
              className={`inline-block px-3 py-2 rounded-lg text-sm whitespace-pre-wrap max-w-[85%] ${
                m.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"
              }`}
            >
              {m.content}
            </span>
          </div>
        ))}
        {loading && <p className="text-sm text-muted-foreground">Thinking...</p>}
        <div ref={bottomRef} />
      </div>

      <div className="flex gap-2 mt-3">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onSend()}
          placeholder="Ask the Copilot..."
          maxLength={2000}
        />
        <Button onClick={onSend} disabled={loading || !input.trim()}>Send</Button>
      </div>
    </div>
  );
}