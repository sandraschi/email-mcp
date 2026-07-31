import {
	AlertTriangle,
	BookOpen,
	Bot,
	ChevronDown,
	ChevronUp,
	Download,
	Eraser,
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
	Volume2,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { fetchWithAuth } from "@/lib/api";
import { speakText } from "@/lib/speech";
import { type Provider, useLlmStore } from "@/store/llm-store";

const STORAGE_KEY = "email-mcp-chat-history";
const PERSONALITY_KEY = "email-mcp-chat-personality";
const CUSTOM_PROMPT_KEY = "email-mcp-chat-custom-prompt";
const MAX_MESSAGES = 100;

type Message = {
	role: "user" | "assistant";
	content: string;
	ts: string;
};

type Personality = {
	id: string;
	label: string;
	prompt: string;
};

const PERSONALITIES: Personality[] = [
	{
		id: "research",
		label: "Research Assistant",
		prompt:
			"You are a thorough research assistant for email management. Answer in detail, cite specific email data, and suggest follow-up actions. Be precise and methodical.",
	},
	{
		id: "reviewer",
		label: "Expert Reviewer",
		prompt:
			"You are an expert email reviewer. Analyze emails critically — flag security concerns, check tone, verify completeness. Give structured feedback with pros/cons.",
	},
	{
		id: "summarizer",
		label: "Quick Summarizer",
		prompt:
			"You are a rapid summarizer. Keep responses under 3 sentences. Extract only the key information. Bullet points preferred. No fluff.",
	},
	{
		id: "custom",
		label: "Custom",
		prompt: "",
	},
];

const EXAMPLE_PROMPTS = [
	{
		group: "Reading",
		prompts: [
			"Show me my unread inbox",
			"Find emails from last week about project updates",
			"Search for anything from GitHub notifications",
		],
	},
	{
		group: "Writing",
		prompts: [
			"Draft a professional meeting request",
			"Help me compose a polite follow-up to a client",
			"Write a thank-you reply to an interview invitation",
		],
	},
	{
		group: "Managing",
		prompts: [
			"Summarize the last 10 emails from John",
			"What's the status of my email services?",
			"Create a mailing list for my team newsletter",
		],
	},
];

const WORKFLOWS = [
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

function loadHistory(): Message[] {
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		if (raw) return JSON.parse(raw);
	} catch {
		/* ignore */
	}
	return [];
}

function saveHistory(messages: Message[]) {
	const trimmed = messages.slice(-MAX_MESSAGES);
	localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
}

function loadPersonality(): string {
	try {
		return localStorage.getItem(PERSONALITY_KEY) || "research";
	} catch {
		return "research";
	}
}

function loadCustomPrompt(): string {
	try {
		return localStorage.getItem(CUSTOM_PROMPT_KEY) || "";
	} catch {
		return "";
	}
}

function buildSystemPrompt(
	skillContent: string,
	personality: Personality,
	customPrompt: string,
): string {
	if (personality.id === "custom") return customPrompt || skillContent;
	return `${skillContent}\n\n---\n\n## Role\n${personality.prompt}`;
}

export function Chat() {
	const [messages, setMessages] = useState<Message[]>(loadHistory);
	const [input, setInput] = useState("");
	const [loading, setLoading] = useState(false);
	const [skillContent, setSkillContent] = useState("");
	const [skillLoaded, setSkillLoaded] = useState(false);
	const [personalityId, setPersonalityId] = useState(loadPersonality);
	const [customPrompt, setCustomPrompt] = useState(loadCustomPrompt);
	const [showWorkflows, setShowWorkflows] = useState(false);
	const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);
	const [workflowRecipient, setWorkflowRecipient] = useState("Prince Charming");
	const [workflowTone, setWorkflowTone] = useState("romantic");
	const [workflowMood, setWorkflowMood] = useState("passionate");
	const [workflowFormat, setWorkflowFormat] = useState("text");
	const [executingWorkflow, setExecutingWorkflow] = useState(false);
	const scrollRef = useRef<HTMLDivElement>(null);
	const initialized = useRef(false);
	const inputRef = useRef<HTMLTextAreaElement>(null);

	const autoGrowInput = useCallback(() => {
		const el = inputRef.current;
		if (!el) return;
		el.style.height = "auto";
		el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
	}, []);

	const {
		providers,
		selectedProvider,
		selectedModel,
		setProviders,
		setSelectedProvider,
		setSelectedModel,
		setLoading: setStoreLoading,
	} = useLlmStore();
	const currentProvider = providers.find((p) => p.id === selectedProvider);

	// biome-ignore lint/correctness/useExhaustiveDependencies: init-once effect; zustand setters are stable (eslint parity)
	useEffect(() => {
		if (initialized.current) return;
		initialized.current = true;
		const init = async () => {
			let skillText = "";
			try {
				const skill = await fetchWithAuth("/api/skills/email-mcp");
				skillText =
					typeof skill === "object" && skill !== null
						? (skill as { content?: string }).content || ""
						: String(skill);
				setSkillLoaded(true);
				setSkillContent(skillText);
			} catch {
				/* no skill */
			}
			try {
				const data = await fetchWithAuth("/api/llm/models");
				const list = (data as { providers?: Provider[] }).providers || [];
				const gpuInfo = (data as { gpu?: { detected: boolean } }).gpu || {
					detected: false,
				};
				setProviders(list, gpuInfo);
				setStoreLoading(false);
				const firstAvail = list.find((p) => p.available === true);
				const storedProv = localStorage.getItem("llm_provider");
				const storedModel = localStorage.getItem("llm_model");
				if (storedProv && list.some((p) => p.id === storedProv)) {
					setSelectedProvider(storedProv);
					if (storedModel) setSelectedModel(storedModel);
				} else if (firstAvail) {
					setSelectedProvider(firstAvail.id);
					setSelectedModel(firstAvail.models?.[0] || "");
				}
			} catch {
				/* ignore */
			}
			if (messages.length === 0) {
				const expertise = skillText
					? `I am the Email-MCP AI expert.\n\n${skillText.replace(/^---[\s\S]*?---\n*/m, "").trim()}`
					: "I am the Email-MCP AI assistant. I can help you send, receive, search, and manage emails.";
				const greeting: Message = {
					role: "assistant",
					content: expertise,
					ts: new Date().toISOString(),
				};
				setMessages([greeting]);
				saveHistory([greeting]);
			}
		};
		init();
	}, []); // eslint-disable-line react-hooks/exhaustive-deps

	// biome-ignore lint/correctness/useExhaustiveDependencies: scroll-to-bottom on message change; scrollRef is a stable ref
	useEffect(() => {
		scrollRef.current?.scrollTo({
			top: scrollRef.current.scrollHeight,
			behavior: "smooth",
		});
	}, [messages]);

	useEffect(() => {
		localStorage.setItem(PERSONALITY_KEY, personalityId);
	}, [personalityId]);

	const personality =
		PERSONALITIES.find((p) => p.id === personalityId) || PERSONALITIES[0];

	const addMessage = useCallback(
		(role: "user" | "assistant", content: string) => {
			const msg: Message = { role, content, ts: new Date().toISOString() };
			setMessages((prev) => {
				const next = [...prev, msg];
				saveHistory(next);
				return next;
			});
		},
		[],
	);

	const handleSend = useCallback(
		async (query?: string) => {
			const q = query || input;
			if (!q.trim() || loading) return;
			setInput("");
			autoGrowInput();
			addMessage("user", q);
			setLoading(true);
			try {
				const system = buildSystemPrompt(
					skillContent,
					personality,
					customPrompt,
				);
				const data = await fetchWithAuth("/api/chat", {
					method: "POST",
					body: JSON.stringify({
						query: q,
						system_prompt: system,
						personality_id: personalityId,
					}),
				});
				addMessage(
					"assistant",
					(data as { response?: string }).response || "No response.",
				);
			} catch (err: unknown) {
				addMessage(
					"assistant",
					`Error: ${err instanceof Error ? err.message : String(err)}`,
				);
			} finally {
				setLoading(false);
			}
		},
		[
			input,
			loading,
			skillContent,
			personality,
			customPrompt,
			personalityId,
			addMessage,
			autoGrowInput,
		],
	);

	const handleExport = useCallback(() => {
		if (messages.length === 0) return;
		const lines = messages.map((m) => {
			const ts = m.ts ? new Date(m.ts).toLocaleString() : "?";
			const role = m.role === "user" ? "You" : "Assistant";
			return `[${ts}] ${role}:\n${m.content}\n`;
		});
		const blob = new Blob([lines.join("\n---\n")], { type: "text/plain" });
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = `email-mcp-chat-${new Date().toISOString().slice(0, 10)}.txt`;
		a.click();
		URL.revokeObjectURL(url);
	}, [messages]);

	const handleClear = useCallback(() => {
		setMessages([]);
		localStorage.removeItem(STORAGE_KEY);
		const greeting: Message = {
			role: "assistant",
			content: "Conversation cleared. How can I help you with your emails?",
			ts: new Date().toISOString(),
		};
		setMessages([greeting]);
		saveHistory([greeting]);
	}, []);

	const handleWorkflow = async (wf: (typeof WORKFLOWS)[number]) => {
		setExecutingWorkflow(true);
		const recipient = wf.id === "love-letter" ? workflowRecipient : "recipient";
		const userMsg = `${wf.label} to ${recipient} — make it ${workflowTone}, ${workflowMood}`;
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
			const d = data as {
				success?: boolean;
				response?: string;
				error?: string;
			};
			if (d.success)
				addMessage(
					"assistant",
					`**${wf.label} to ${recipient}**\n\n${d.response}`,
				);
			else
				addMessage(
					"assistant",
					`Workflow failed: ${d.error || "Unknown error"}`,
				);
		} catch (err: unknown) {
			addMessage(
				"assistant",
				`Error: ${err instanceof Error ? err.message : String(err)}`,
			);
		} finally {
			setExecutingWorkflow(false);
			setSelectedWorkflow(null);
		}
	};

	return (
		<div
			data-testid="chat-page"
			className="flex h-[calc(100vh-8rem)] flex-col space-y-4"
		>
			<div className="flex items-center justify-between">
				<div>
					<h2 className="text-2xl font-bold tracking-tight text-white">
						Email AI Expert
					</h2>
					<p className="text-slate-400">
						Natural language email management powered by your AI provider
					</p>
				</div>
				<div
					data-testid="chat-controls"
					className="flex items-center gap-2 text-xs"
				>
					<select
						data-testid="personality-select"
						className="bg-zinc-800 text-zinc-100 border border-zinc-600 rounded px-2 py-1 text-xs"
						value={personalityId}
						onChange={(e) => setPersonalityId(e.target.value)}
					>
						{PERSONALITIES.map((p) => (
							<option key={p.id} value={p.id}>
								{p.label}
							</option>
						))}
					</select>
					{skillLoaded && (
						<span className="flex items-center gap-1 text-emerald-400">
							<BookOpen className="h-3 w-3" /> skill:email-mcp
						</span>
					)}
					<select
						data-testid="chat-provider-select"
						className="bg-zinc-800 text-zinc-100 border border-zinc-600 rounded px-1.5 py-1 text-xs max-w-[110px]"
						value={selectedProvider}
						onChange={(e) => {
							setSelectedProvider(e.target.value);
							const p = providers.find((pr) => pr.id === e.target.value);
							if (p?.models?.length) setSelectedModel(p.models[0]);
						}}
					>
						{providers.map((p) => (
							<option key={p.id} value={p.id}>
								{p.available === true
									? "● "
									: p.available === false
										? "○ "
										: "☁ "}
								{p.name}
							</option>
						))}
					</select>
					{currentProvider?.models && currentProvider.models.length > 0 && (
						<select
							className="bg-zinc-800 text-zinc-100 border border-zinc-600 rounded px-1.5 py-1 text-xs max-w-[130px]"
							value={selectedModel}
							onChange={(e) => setSelectedModel(e.target.value)}
						>
							{currentProvider.models.map((m) => (
								<option key={m} value={m}>
									{m}
								</option>
							))}
						</select>
					)}
					<button
						type="button"
						data-testid="chat-export"
						className="p-1.5 rounded text-slate-400 hover:text-white disabled:opacity-30 transition-colors"
						title="Export chat"
						disabled={messages.length === 0}
						onClick={handleExport}
					>
						<Download className="h-3.5 w-3.5" />
					</button>
					<button
						type="button"
						data-testid="chat-clear"
						className="p-1.5 rounded text-slate-400 hover:text-white disabled:opacity-30 transition-colors"
						title="Clear conversation"
						disabled={messages.length === 0}
						onClick={handleClear}
					>
						<Eraser className="h-3.5 w-3.5" />
					</button>
				</div>
			</div>

			{personalityId === "custom" && (
				<div className="flex gap-2">
					<textarea
						className="flex-1 bg-zinc-900 border border-zinc-700 rounded px-3 py-1.5 text-xs text-zinc-300 resize-none"
						rows={2}
						placeholder="Enter your custom system prompt..."
						value={customPrompt}
						onChange={(e) => {
							setCustomPrompt(e.target.value);
							localStorage.setItem(CUSTOM_PROMPT_KEY, e.target.value);
						}}
					/>
				</div>
			)}

			<Card className="flex-1 min-h-0 border-slate-800 bg-slate-950/50 flex flex-col overflow-hidden">
				<CardContent
					ref={scrollRef}
					data-testid="chat-messages"
					className="flex-1 min-h-0 overflow-y-auto p-4 space-y-4 scroll-smooth"
				>
					{messages.map((msg) => (
						<div key={`${msg.ts}-${msg.role}`} className="flex gap-3">
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
										{msg.ts
											? new Date(msg.ts).toLocaleTimeString([], {
													hour: "2-digit",
													minute: "2-digit",
												})
											: ""}
									</span>
									{msg.role === "assistant" && (
										<button
											type="button"
											title="Read aloud"
											className="text-slate-500 hover:text-blue-300"
											onClick={() =>
												speakText(msg.content).catch((e) => console.error(e))
											}
										>
											<Volume2 className="h-3.5 w-3.5" />
										</button>
									)}
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
						type="button"
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
											type="button"
											key={wf.id}
											className={`flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-md border transition-colors ${isActive ? "bg-purple-950/30 border-purple-700 text-purple-200" : "border-slate-700 text-slate-400 hover:border-slate-500 hover:text-slate-200"}`}
											onClick={() =>
												setSelectedWorkflow(isActive ? null : wf.id)
											}
										>
											<Icon className="h-3 w-3" /> {wf.label}
										</button>
									);
								})}
							</div>
							{selectedWorkflow && (
								<div className="flex gap-2 items-end flex-wrap pt-1">
									<div className="min-w-[160px]">
										<label
											htmlFor="wf-recipient"
											className="text-xs text-slate-500 block mb-0.5"
										>
											Recipient
										</label>
										<select
											id="wf-recipient"
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
										<label
											htmlFor="wf-tone"
											className="text-xs text-slate-500 block mb-0.5"
										>
											Tone
										</label>
										<select
											id="wf-tone"
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
										<label
											htmlFor="wf-mood"
											className="text-xs text-slate-500 block mb-0.5"
										>
											Mood
										</label>
										<select
											id="wf-mood"
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
										<label
											htmlFor="wf-format"
											className="text-xs text-slate-500 block mb-0.5"
										>
											Format
										</label>
										<select
											id="wf-format"
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
										onClick={() => {
											const wf = WORKFLOWS.find(
												(w) => w.id === selectedWorkflow,
											);
											if (wf) handleWorkflow(wf);
										}}
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

				{/* Example prompts */}
				<div
					data-testid="example-prompts"
					className="border-t border-slate-800 bg-slate-900/20 px-4 py-2"
				>
					<div className="flex flex-wrap gap-1.5">
						{EXAMPLE_PROMPTS.flatMap((g) => g.prompts)
							.slice(0, 6)
							.map((p) => (
								<button
									type="button"
									key={p}
									className="text-xs px-2 py-1 rounded-full border border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-500 transition-colors"
									onClick={() => {
										setInput(p);
									}}
								>
									{p}
								</button>
							))}
					</div>
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
						<textarea
							ref={inputRef}
							data-testid="chat-input"
							rows={3}
							className="flex-1 bg-slate-950 border border-slate-800 rounded-md px-4 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none overflow-y-auto disabled:opacity-50 min-h-[76px] max-h-[160px]"
							placeholder="Ask me to search, draft, compose, or organize your emails..."
							value={input}
							onChange={(e) => {
								setInput(e.target.value);
								autoGrowInput();
							}}
							onKeyDown={(e) => {
								if (e.key === "Enter" && !e.shiftKey) {
									e.preventDefault();
									handleSend();
								}
							}}
							disabled={loading}
						/>
						<Button
							data-testid="chat-send"
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
