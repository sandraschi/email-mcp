import {
  AlertTriangle,
  BookOpen,
  Bot,
  ChevronDown,
  ChevronUp,
  Cpu,
  Frown,
  Heart,
  HeartHandshake,
  Loader2,
  Send,
  Skull,
  Sparkles,
  Star,
  ThumbsUp,
  User,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { fetchWithAuth } from "@/lib/api";

type Message = {
  role: "user" | "bot";
  content: string;
  timestamp: string;
};

type WorkflowDef = {
  id: string;
  label: string;
  icon: typeof Heart;
  tone?: string;
  recipientLabel?: string;
};

const WORKFLOWS: WorkflowDef[] = [
  { id: "love-letter", label: "Love Letter", icon: Heart, tone: "romantic" },
  { id: "breakup", label: "Breakup", icon: Frown, tone: "gentle" },
  { id: "thank-you", label: "Thank You", icon: ThumbsUp, tone: "warm" },
  { id: "complaint", label: "Complaint", icon: AlertTriangle, tone: "polite" },
  { id: "apology", label: "Apology", icon: HeartHandshake, tone: "humble" },
  { id: "fan-mail", label: "Fan Mail", icon: Star, tone: "enthusiastic" },
  { id: "hate-mail", label: "Hate Mail", icon: Skull, tone: "comedic" },
];

const RECIPIENTS = [
  "Prince Charming",
  "Princess",
  "Landlady",
  "Landlord",
  "My Cat",
  "The AI Overlord",
  "Pizza Delivery Person",
  "My Bank Account",
  "The Moon",
  "My Houseplants",
  "The WiFi Router",
  "My Future Self",
  "The Ceiling Fan",
  "Neighbor's Dog",
  "The 5AM Alarm Clock",
  "Roko's Basilisk (spare me!)",
];

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [skillLoaded, setSkillLoaded] = useState(false);
  const [providerInfo, setProviderInfo] = useState("");
  const [showWorkflows, setShowWorkflows] = useState(true);
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);
  const [workflowRecipient, setWorkflowRecipient] = useState("Prince Charming");
  const [workflowTone, setWorkflowTone] = useState("romantic");
  const [workflowMood, setWorkflowMood] = useState("passionate");
  const [workflowFormat, setWorkflowFormat] = useState("text");
  const [executingWorkflow, setExecutingWorkflow] = useState(false);
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
      } catch {
        /* no skill */
      }
      let provider = "local";
      try {
        const models = await fetchWithAuth("/api/llm/models");
        const firstAvail = (models.providers || []).find(
          (p: any) => p.available === true,
        );
        if (firstAvail) {
          provider = `${firstAvail.name} (${firstAvail.models[0] || "default"})`;
        } else {
          const first = (models.providers || [])[0];
          if (first) provider = first.name;
        }
      } catch {
        /* ignore */
      }
      setProviderInfo(provider);
      const expertise = skillText
        ? `I am the Email-MCP AI expert.\n\n${skillText.replace(/^---[\s\S]*?---\n*/m, "").trim()}`
        : "I am the Email-MCP AI assistant. I can help you send, receive, search, and manage emails.";
      setMessages([
        {
          role: "bot",
          content: expertise,
          timestamp: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        },
      ]);
    };
    init();
  }, []);

  useEffect(() => {
    if (scrollRef.current)
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, []);

  const addMessage = (role: "user" | "bot", content: string) => {
    setMessages((prev) => [
      ...prev,
      {
        role,
        content,
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      },
    ]);
  };

  const handleSend = async (query?: string) => {
    const q = query || input;
    if (!q.trim() || loading) return;
    addMessage("user", q);
    setInput("");
    setLoading(true);
    try {
      const data = await fetchWithAuth("/api/chat", {
        method: "POST",
        body: JSON.stringify({ query: q }),
      });
      addMessage("bot", data.response || "No response.");
    } catch (err: unknown) {
      addMessage(
        "bot",
        `Error: ${err instanceof Error ? err.message : String(err)}`,
      );
    } finally {
      setLoading(false);
    }
  };

  const handleWorkflow = async (wf: WorkflowDef) => {
    setExecutingWorkflow(true);
    const wfLabel = wf.label;
    const recipient = wf.id === "love-letter" ? workflowRecipient : "recipient";
    const userMsg = `${wfLabel} to ${recipient} — make it ${workflowTone}, ${workflowMood}`;
    addMessage("user", userMsg);
    try {
      const data = await fetchWithAuth("/api/workflow", {
        method: "POST",
        body: JSON.stringify({
          workflow: wf.id,
          recipient,
          tone: workflowTone,
          mood: workflowMood,
          format: workflowFormat,
        }),
      });
      if (data.success) {
        addMessage("bot", `**${wfLabel} to ${recipient}**\n\n${data.response}`);
      } else {
        addMessage("bot", `Workflow failed: ${data.error || "Unknown error"}`);
      }
    } catch (err: unknown) {
      addMessage(
        "bot",
        `Error: ${err instanceof Error ? err.message : String(err)}`,
      );
    } finally {
      setExecutingWorkflow(false);
      setSelectedWorkflow(null);
    }
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Email AI Expert
          </h2>
          <p className="text-slate-400">
            Natural language email management powered by your AI provider
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs">
          {skillLoaded && (
            <span className="flex items-center gap-1 text-emerald-400">
              <BookOpen className="h-3 w-3" /> Skill
            </span>
          )}
          {providerInfo && (
            <span className="flex items-center gap-1 text-slate-400">
              <Cpu className="h-3 w-3" /> {providerInfo}
            </span>
          )}
        </div>
      </div>

      <Card className="flex-1 border-slate-800 bg-slate-950/50 flex flex-col overflow-hidden">
        <CardContent
          ref={scrollRef}
          className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth"
        >
          {messages.map((msg, i) => (
            <div key={i} className="flex gap-3">
              <div
                className={`h-8 w-8 rounded-full flex items-center justify-center border shrink-0 ${msg.role === "user" ? "bg-slate-800 border-slate-700" : "bg-blue-900/20 border-blue-800"}`}
              >
                {msg.role === "user" ? (
                  <User className="h-4 w-4 text-slate-400" />
                ) : (
                  <Bot className="h-4 w-4 text-blue-400" />
                )}
              </div>
              <div className="flex-1 space-y-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-sm font-medium ${msg.role === "user" ? "text-slate-200" : "text-blue-400"}`}
                  >
                    {msg.role === "user" ? "You" : "Email Expert AI"}
                  </span>
                  <span className="text-xs text-slate-500">
                    {msg.timestamp}
                  </span>
                </div>
                <div
                  className={`text-sm text-slate-300 p-3 rounded-md border inline-block max-w-[90%] break-words ${msg.role === "user" ? "bg-slate-900/50 border-slate-800" : "bg-blue-950/10 border-blue-900/30"}`}
                >
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
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
                <Loader2 className="h-3 w-3 animate-spin" /> Thinking...
              </div>
            </div>
          )}
        </CardContent>

        {/* Workflow presets */}
        <div className="border-t border-slate-800 bg-slate-900/30">
          <button
            className="w-full flex items-center justify-between px-4 py-1.5 text-xs text-slate-500 hover:text-slate-300"
            onClick={() => setShowWorkflows(!showWorkflows)}
          >
            <span className="flex items-center gap-1">
              <Sparkles className="h-3 w-3" /> Creative Workflows
            </span>
            {showWorkflows ? (
              <ChevronUp className="h-3 w-3" />
            ) : (
              <ChevronDown className="h-3 w-3" />
            )}
          </button>
          {showWorkflows && (
            <div className="px-4 pb-3 space-y-2">
              <div className="flex gap-1.5 flex-wrap">
                {WORKFLOWS.map((wf) => {
                  const isActive = selectedWorkflow === wf.id;
                  const Icon = wf.icon;
                  return (
                    <button
                      key={wf.id}
                      className={`flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-md border transition-colors ${
                        isActive
                          ? "bg-purple-950/30 border-purple-700 text-purple-200"
                          : "border-slate-700 text-slate-400 hover:border-slate-500 hover:text-slate-200"
                      }`}
                      onClick={() =>
                        setSelectedWorkflow(isActive ? null : wf.id)
                      }
                    >
                      <Icon className="h-3 w-3" />
                      {wf.label}
                    </button>
                  );
                })}
              </div>
              {selectedWorkflow && (
                <div className="flex gap-2 items-end flex-wrap pt-1">
                  <div className="min-w-[160px]">
                    <label className="text-xs text-slate-500 block mb-0.5">
                      Recipient
                    </label>
                    <select
                      className="bg-slate-900 border border-slate-700 text-white text-xs rounded px-2 py-1.5 w-full"
                      value={workflowRecipient}
                      onChange={(e) => setWorkflowRecipient(e.target.value)}
                    >
                      {RECIPIENTS.map((r) => (
                        <option key={r}>{r}</option>
                      ))}
                    </select>
                  </div>
                  <div className="min-w-[120px]">
                    <label className="text-xs text-slate-500 block mb-0.5">
                      Tone
                    </label>
                    <select
                      className="bg-slate-900 border border-slate-700 text-white text-xs rounded px-2 py-1.5 w-full"
                      value={workflowTone}
                      onChange={(e) => setWorkflowTone(e.target.value)}
                    >
                      {[
                        "romantic",
                        "sincere",
                        "humble",
                        "enthusiastic",
                        "polite",
                        "comedic",
                        "dramatic",
                        "professional",
                      ].map((t) => (
                        <option key={t}>{t}</option>
                      ))}
                    </select>
                  </div>
                  <div className="min-w-[120px]">
                    <label className="text-xs text-slate-500 block mb-0.5">
                      Mood
                    </label>
                    <select
                      className="bg-slate-900 border border-slate-700 text-white text-xs rounded px-2 py-1.5 w-full"
                      value={workflowMood}
                      onChange={(e) => setWorkflowMood(e.target.value)}
                    >
                      {[
                        "passionate",
                        "warm",
                        "gentle",
                        "urgent",
                        "melancholic",
                        "absurd",
                        "cheerful",
                        "stoic",
                      ].map((m) => (
                        <option key={m}>{m}</option>
                      ))}
                    </select>
                  </div>
                  <div className="min-w-[100px]">
                    <label className="text-xs text-slate-500 block mb-0.5">
                      Format
                    </label>
                    <select
                      className="bg-slate-900 border border-slate-700 text-white text-xs rounded px-2 py-1.5 w-full"
                      value={workflowFormat}
                      onChange={(e) => setWorkflowFormat(e.target.value)}
                    >
                      <option value="text">Plain Text</option>
                      <option value="ascii">ASCII Art</option>
                      <option value="svg">SVG Card</option>
                    </select>
                  </div>
                  <Button
                    size="sm"
                    className="bg-purple-600 hover:bg-purple-700 h-7 text-xs"
                    onClick={() =>
                      handleWorkflow(
                        WORKFLOWS.find((w) => w.id === selectedWorkflow)!,
                      )
                    }
                    disabled={executingWorkflow}
                  >
                    {executingWorkflow ? (
                      <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                    ) : (
                      <Sparkles className="h-3 w-3 mr-1" />
                    )}
                    Generate
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Input */}
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
