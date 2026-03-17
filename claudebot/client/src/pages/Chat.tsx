import React, { useState, useEffect, useRef } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { motion } from "framer-motion";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
}

interface Conversation {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
}

export function Chat() {
  const [currentConv, setCurrentConv] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const ws = useRef<WebSocket | null>(null);

  // Fetch conversations
  const { data: conversations, refetch: refetchConvs } = useQuery({
    queryKey: ["conversations"],
    queryFn: async () => {
      const res = await fetch("/api/conversations");
      return res.json() as Promise<Conversation[]>;
    },
  });

  // Fetch messages for current conversation
  const { data: messages, refetch: refetchMsgs } = useQuery({
    queryKey: ["messages", currentConv],
    queryFn: async () => {
      if (!currentConv) return [];
      const res = await fetch(`/api/conversations/${currentConv}/messages`);
      return res.json() as Promise<Message[]>;
    },
    enabled: !!currentConv,
  });

  // Create new conversation
  const createConv = useMutation({
    mutationFn: async () => {
      const res = await fetch("/api/conversations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: "New Conversation" }),
      });
      return res.json() as Promise<Conversation>;
    },
    onSuccess: (conv) => {
      setCurrentConv(conv.id);
      refetchConvs();
    },
  });

  // Send message
  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !currentConv) return;

    const content = input;
    setInput("");

    try {
      const res = await fetch(`/api/conversations/${currentConv}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      });
      const msg = await res.json();
      refetchMsgs();
    } catch (err) {
      console.error("Error sending message:", err);
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Initialize first conversation if none exists
  useEffect(() => {
    if (conversations && conversations.length === 0) {
      createConv.mutate();
    } else if (conversations && conversations.length > 0 && !currentConv) {
      setCurrentConv(conversations[0].id);
    }
  }, [conversations]);

  return (
    <div className="h-screen bg-black text-green-400 font-mono flex flex-col">
      {/* Header */}
      <div className="border-b border-green-400 p-4 bg-black/50 backdrop-blur">
        <h1 className="text-2xl font-bold neon-text">
          &gt; CLAUDEBOT GATEWAY
        </h1>
        <p className="text-xs text-green-300 opacity-75">v1.0 | OPERATIONAL</p>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <div className="w-64 border-r border-green-400 p-4 overflow-y-auto bg-black/30">
          <button
            onClick={() => createConv.mutate()}
            className="w-full mb-4 px-4 py-2 bg-green-400 text-black font-bold hover:bg-green-300 transition"
          >
            + NEW CHAT
          </button>

          <div className="space-y-2">
            {conversations?.map((conv) => (
              <button
                key={conv.id}
                onClick={() => setCurrentConv(conv.id)}
                className={`w-full text-left p-2 text-sm truncate ${
                  currentConv === conv.id
                    ? "bg-green-400 text-black font-bold"
                    : "hover:bg-green-400/20"
                }`}
              >
                {conv.title}
              </button>
            ))}
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages?.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-md px-4 py-2 ${
                    msg.role === "user"
                      ? "bg-blue-600 text-white rounded-l-lg rounded-tr-lg"
                      : "bg-green-400/20 text-green-400 rounded-r-lg rounded-tl-lg border border-green-400"
                  }`}
                >
                  <p className="text-sm">{msg.content}</p>
                </div>
              </motion.div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form onSubmit={sendMessage} className="border-t border-green-400 p-4 bg-black/50">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="&gt; INPUT MESSAGE"
                className="flex-1 bg-black border border-green-400 text-green-400 px-4 py-2 font-mono focus:outline-none placeholder-green-600"
              />
              <button
                type="submit"
                className="px-6 py-2 bg-green-400 text-black font-bold hover:bg-green-300 transition"
              >
                SEND
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
