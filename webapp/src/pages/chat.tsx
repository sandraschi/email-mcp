import { useState, useEffect, useRef } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Send, Bot, User, Loader2, BookOpen, Cpu } from "lucide-react";
import { fetchWithAuth } from "@/lib/api";

type Message = {
    role: "user" | "bot";
    content: string;
    timestamp: string;
};

export function Chat() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [skillLoaded, setSkillLoaded] = useState(false);
    const [providerInfo, setProviderInfo] = useState("");
    const scrollRef = useRef<HTMLDivElement>(null);
    const initialized = useRef(false);

    useEffect(() => {
        if (initialized.current) return;
        initialized.current = true;

        const init = async () => {
            let skillText = "";
            try {
                const skill = await fetchWithAuth("/api/skills/email-mcp");
                skillText = skill.content || "";
                setSkillLoaded(true);
            } catch { /* no skill available */ }

            let provider = "local";
            try {
                const models = await fetchWithAuth("/api/llm/models");
                const firstAvail = (models.providers || []).find((p: any) => p.available === true);
                if (firstAvail) {
                    provider = `${firstAvail.name} (${(firstAvail.models[0] || "default")})`;
                } else {
                    const first = (models.providers || [])[0];
                    if (first) provider = first.name;
                }
            } catch { /* ignore */ }
            setProviderInfo(provider);

            const expertise = skillText
                ? `I am the Email-MCP AI expert. I have loaded the email skill which gives me expertise in:\n\n` +
                  skillText.replace(/^---[\s\S]*?---\n*/m, "").trim()
                : `I am the Email-MCP AI assistant. I can help you send, receive, search, and manage emails across multiple providers.`;

            setMessages([{
                role: "bot",
                content: expertise,
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            }]);
        };
        init();
    }, []);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userMsg: Message = {
            role: "user",
            content: input,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };

        setMessages(prev => [...prev, userMsg]);
        setInput("");
        setLoading(true);

        try {
            const data = await fetchWithAuth("/api/chat", {
                method: "POST",
                body: JSON.stringify({ query: input }),
            });

            const botMsg: Message = {
                role: "bot",
                content: data.response || "No response from AI.",
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            };
            setMessages(prev => [...prev, botMsg]);
        } catch (err: unknown) {
            const errorMessage = err instanceof Error ? err.message : String(err);
            const errorMsg: Message = {
                role: "bot",
                content: `Error: ${errorMessage}`,
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            };
            setMessages(prev => [...prev, errorMsg]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">Email AI Expert</h2>
                    <p className="text-slate-400">Natural language email management powered by your configured AI provider</p>
                </div>
                <div className="flex items-center gap-3 text-xs">
                    {skillLoaded && (
                        <span className="flex items-center gap-1 text-emerald-400">
                            <BookOpen className="h-3 w-3" /> Skill loaded
                        </span>
                    )}
                    {providerInfo && (
                        <span className="flex items-center gap-1 text-slate-400" title="AI provider & model">
                            <Cpu className="h-3 w-3" /> {providerInfo}
                        </span>
                    )}
                </div>
            </div>

            <Card className="flex-1 border-slate-800 bg-slate-950/50 flex flex-col overflow-hidden">
                <CardContent ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth">
                    {messages.map((msg, i) => (
                        <div key={i} className="flex gap-3">
                            <div className={`h-8 w-8 rounded-full flex items-center justify-center border shrink-0 ${
                                msg.role === "user"
                                    ? "bg-slate-800 border-slate-700"
                                    : "bg-blue-900/20 border-blue-800"
                            }`}>
                                {msg.role === "user" ? (
                                    <User className="h-4 w-4 text-slate-400" />
                                ) : (
                                    <Bot className="h-4 w-4 text-blue-400" />
                                )}
                            </div>
                            <div className="flex-1 space-y-1 min-w-0">
                                <div className="flex items-center gap-2">
                                    <span className={`text-sm font-medium ${msg.role === "user" ? "text-slate-200" : "text-blue-400"}`}>
                                        {msg.role === "user" ? "You" : "Email Expert AI"}
                                    </span>
                                    <span className="text-xs text-slate-500">{msg.timestamp}</span>
                                </div>
                                <div className={`text-sm text-slate-300 p-3 rounded-md border inline-block max-w-[90%] break-words ${
                                    msg.role === "user"
                                        ? "bg-slate-900/50 border-slate-800"
                                        : "bg-blue-950/10 border-blue-900/30"
                                }`}>
                                    <p className="whitespace-pre-wrap">{msg.content}</p>
                                </div>
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="flex gap-3">
                            <div className="h-8 w-8 rounded-full bg-blue-900/20 flex items-center justify-center border border-blue-800">
                                <Bot className="h-4 w-4 text-blue-400" />
                            </div>
                            <div className="flex items-center gap-2 text-slate-500 text-sm italic">
                                <Loader2 className="h-3 w-3 animate-spin" />
                                Thinking...
                            </div>
                        </div>
                    )}
                </CardContent>
                <div className="p-4 border-t border-slate-800 bg-slate-900/30">
                    <form
                        className="flex gap-2"
                        onSubmit={(e) => {
                            e.preventDefault();
                            handleSend();
                        }}
                    >
                        <input
                            className="flex-1 bg-slate-950 border border-slate-800 rounded-md px-4 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none disabled:opacity-50"
                            placeholder="Ask me to search, draft, compose, or organize your emails..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            disabled={loading}
                        />
                        <Button
                            type="submit"
                            size="icon"
                            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                            disabled={!input.trim() || loading}
                        >
                            <Send className="h-4 w-4" />
                        </Button>
                    </form>
                </div>
            </Card>
        </div>
    );
}
