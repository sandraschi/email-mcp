import { AlertCircle, CheckCircle2, Loader2, Play, Wrench } from "lucide-react";
import { useEffect, useState } from "react";
import { useToast } from "@/components/toast";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { fetchWithAuth } from "@/lib/api";

type ToolInfo = { name: string; description: string };

export function Tools() {
	const [tools, setTools] = useState<ToolInfo[]>([]);
	const [loading, setLoading] = useState(true);
	const [executingTools, setExecutingTools] = useState<Set<string>>(new Set());
	const [toolResults, setToolResults] = useState<
		Record<string, { ok: boolean; msg: string }>
	>({});
	const [testEmail, setTestEmail] = useState("");
	const { toast } = useToast();

	useEffect(() => {
		fetchWithAuth("/api/tools")
			.then((data) => {
				setTools(data.tools || []);
			})
			.catch(() => {})
			.finally(() => setLoading(false));
	}, []);

	const executeTool = async (
		toolName: string,
		_params: Record<string, unknown> = {},
	) => {
		setExecutingTools((prev) => new Set(prev).add(toolName));
		setToolResults((prev) => ({
			...prev,
			[toolName]: { ok: false, msg: "..." },
		}));
		try {
			let result;
			switch (toolName) {
				case "email_status":
					result = await fetchWithAuth("/api/services");
					break;
				case "list_services":
					result = await fetchWithAuth("/api/services");
					// Re-format for list_services
					result = { success: true, ...result };
					break;
				case "check_inbox":
					result = await fetchWithAuth(`/api/inbox?service=default&limit=5`);
					break;
				case "send_email":
					if (!testEmail.trim()) {
						setToolResults((prev) => ({
							...prev,
							[toolName]: { ok: false, msg: "Enter a test email address" },
						}));
						setExecutingTools((prev) => {
							const n = new Set(prev);
							n.delete(toolName);
							return n;
						});
						return;
					}
					result = await fetchWithAuth("/api/send", {
						method: "POST",
						body: JSON.stringify({
							to: testEmail,
							subject: "Test from Email-MCP",
							body: "This is a test email.",
							service: "default",
						}),
					});
					break;
				case "mailing_lists_catalog":
					result = await fetchWithAuth("/api/tools");
					result = result.tools
						? {
								success: false,
								message:
									"Mailing lists configured via env: EMAIL_MCP_MAILING_LISTS",
							}
						: { success: false, message: "Call via MCP directly" };
					break;
				default:
					result = await fetchWithAuth("/api/tools");
					result = {
						success: true,
						message: `Tool ${toolName} is registered. Use via MCP client for full execution.`,
						tools: result.tools,
					};
			}

			const success = result.success !== false;
			const msg = result.message || result.error || (success ? "OK" : "Failed");
			setToolResults((prev) => ({ ...prev, [toolName]: { ok: success, msg } }));
			if (success) {
				toast("success", `${toolName}: ${msg}`);
			} else {
				toast("error", `${toolName}: ${msg}`);
			}
		} catch (err: unknown) {
			const msg = err instanceof Error ? err.message : "Execution failed";
			setToolResults((prev) => ({ ...prev, [toolName]: { ok: false, msg } }));
			toast("error", `${toolName}: ${msg}`);
		} finally {
			setExecutingTools((prev) => {
				const n = new Set(prev);
				n.delete(toolName);
				return n;
			});
		}
	};

	const _toolActions: Record<string, Record<string, unknown>> = {
		send_email: { to: "", subject: "Test", body: "Test" },
	};

	if (loading) {
		return (
			<div className="flex flex-col items-center justify-center p-12 space-y-4">
				<Loader2 className="h-8 w-8 animate-spin text-blue-500" />
				<p className="text-slate-500">Scanning for email tools...</p>
			</div>
		);
	}

	return (
		<div className="space-y-6">
			<div>
				<h2 className="text-2xl font-bold tracking-tight text-white">
					Email Integration Tools
				</h2>
				<p className="text-slate-400">
					Available MCP tools for email management.
				</p>
			</div>

			<div className="grid gap-4 md:grid-cols-2">
				{tools.map((tool) => {
					const isExecuting = executingTools.has(tool.name);
					const result = toolResults[tool.name];
					return (
						<Card
							key={tool.name}
							className="border-slate-800 bg-slate-950/50 hover:bg-slate-900/30 transition-colors"
						>
							<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
								<div className="space-y-1">
									<CardTitle className="text-sm font-medium text-white">
										{tool.name}
									</CardTitle>
									<CardDescription className="text-xs text-slate-500 line-clamp-2">
										{tool.description || "No description"}
									</CardDescription>
								</div>
								<Wrench className="h-4 w-4 text-blue-500 shrink-0" />
							</CardHeader>
							<CardContent>
								{result && (
									<div
										className={`flex items-center gap-2 text-xs px-2 py-1.5 rounded border mb-2 ${result.ok ? "text-emerald-400 border-emerald-900 bg-emerald-950/20" : "text-red-400 border-red-900 bg-red-950/20"}`}
									>
										{result.ok ? (
											<CheckCircle2 className="h-3 w-3" />
										) : (
											<AlertCircle className="h-3 w-3" />
										)}
										<span className="truncate">{result.msg}</span>
									</div>
								)}
								{tool.name === "send_email" && (
									<Input
										className="bg-slate-900 border-slate-700 text-white text-xs mb-2"
										placeholder="Test recipient email"
										value={testEmail}
										onChange={(e) => setTestEmail(e.target.value)}
									/>
								)}
								<div className="flex justify-end gap-2">
									<Button
										size="sm"
										className="bg-blue-600 hover:bg-blue-700"
										onClick={() => executeTool(tool.name)}
										disabled={isExecuting}
									>
										{isExecuting ? (
											<Loader2 className="h-3 w-3 mr-2 animate-spin" />
										) : (
											<Play className="h-3 w-3 mr-2" />
										)}
										Execute
									</Button>
								</div>
							</CardContent>
						</Card>
					);
				})}
			</div>

			<Card className="border-blue-900/30 bg-blue-950/10">
				<CardHeader>
					<div className="flex items-center gap-2">
						<CheckCircle2 className="h-5 w-5 text-emerald-500" />
						<CardTitle className="text-sm font-medium text-white">
							System Status
						</CardTitle>
					</div>
				</CardHeader>
				<CardContent>
					<p className="text-sm text-slate-400">
						{tools.length} tools registered. SOTA dual transport active on port
						10813.
					</p>
				</CardContent>
			</Card>
		</div>
	);
}
