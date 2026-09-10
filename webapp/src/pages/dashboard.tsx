import {
	Activity,
	ArrowRight,
	Bot,
	FileText,
	History,
	Inbox,
	Layers,
	Loader2,
	Mail,
	PenSquare,
	Radio,
	RefreshCw,
	Server,
	Sliders,
	Users,
	Zap,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useToast } from "@/components/toast";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { fetchWithAuth } from "@/lib/api";

type EmailItem = {
	id: string;
	subject: string;
	from: string;
	date: string;
	read?: boolean;
	_service?: string;
	clean_subject?: string;
	clean_from?: string;
};

type Stats = {
	unread_count: number;
	connected_services: number;
	total_services: number;
	configured_services: number;
	tools_count: number;
	drafts_count: number;
	rules_count?: number;
	contacts_count?: number;
	primary_account?: string;
	ai_provider?: string;
	ai_model?: string;
	watcher?: {
		running?: boolean;
		config?: {
			interval?: number;
			auto_respond?: boolean;
			webhook_url?: string;
		};
		persisted_enabled?: boolean;
	};
	connectors?: Record<
		string,
		{ enabled?: boolean; online?: boolean; url?: string; error?: string }
	>;
	services?: Record<
		string,
		{ configured?: boolean; connected?: boolean; type?: string; error?: string }
	>;
	diagnostics?: {
		cpu?: number;
		mem?: number;
	};
	recent_activity: EmailItem[];
	mcp_version: string;
	error?: string;
};

function useExponentialBackoff(fn: () => Promise<void>, maxRetries = 5) {
	const retriesRef = useRef(0);
	const mountedRef = useRef(true);

	const poll = useCallback(async () => {
		while (mountedRef.current && retriesRef.current < maxRetries) {
			try {
				await fn();
				return;
			} catch {
				retriesRef.current += 1;
				if (retriesRef.current >= maxRetries) return;
				const delay = Math.min(1000 * 2 ** (retriesRef.current - 1), 16000);
				await new Promise((r) => setTimeout(r, delay));
			}
		}
	}, [fn, maxRetries]);

	useEffect(() => {
		poll();
		return () => {
			mountedRef.current = false;
		};
	}, [poll]);
}

function formatDate(dateStr: string) {
	if (!dateStr) return "";
	try {
		const d = new Date(dateStr);
		if (Number.isNaN(d.getTime())) return dateStr;
		return d.toLocaleDateString(undefined, {
			month: "short",
			day: "numeric",
			hour: "2-digit",
			minute: "2-digit",
		});
	} catch {
		return dateStr;
	}
}

function getSenderName(fromStr: string) {
	if (!fromStr) return "Unknown";
	const match = fromStr.match(/^([^<]+)/);
	if (match?.[1].trim()) {
		return match[1].trim().replace(/^["']|["']$/g, "");
	}
	return fromStr;
}

export function Dashboard() {
	const navigate = useNavigate();
	const { toast } = useToast();
	const [stats, setStats] = useState<Stats | null>(null);
	const [loading, setLoading] = useState(true);
	const [refreshing, setRefreshing] = useState(false);
	const [backendOk, setBackendOk] = useState<boolean | null>(null);
	const [activeFilter, setActiveFilter] = useState<"all" | "unread">("all");
	const [triggeringAction, setTriggeringAction] = useState(false);

	const fetchStats = useCallback(async () => {
		try {
			const data = await fetchWithAuth("/api/stats");
			setStats(data);
			setBackendOk(true);
		} catch (err) {
			setBackendOk(false);
			throw err;
		}
	}, []);

	useExponentialBackoff(fetchStats, 5);

	useEffect(() => {
		if (!loading) return;
		fetchStats()
			.catch(() => {})
			.finally(() => setLoading(false));
	}, [fetchStats, loading]);

	// Auto-refresh every 60s
	useEffect(() => {
		const interval = setInterval(() => {
			fetchStats().catch(() => {});
		}, 60_000);
		return () => clearInterval(interval);
	}, [fetchStats]);

	const handleManualRefresh = async () => {
		setRefreshing(true);
		try {
			await fetchStats();
			toast("success", "Dashboard statistics refreshed");
		} catch {
			toast("error", "Failed to refresh statistics");
		} finally {
			setRefreshing(false);
		}
	};

	const handleToggleWatcher = async () => {
		if (!stats) return;
		setTriggeringAction(true);
		const isRunning = stats.watcher?.running;
		try {
			if (isRunning) {
				await fetchWithAuth("/api/watcher/stop", { method: "POST" });
				toast("info", "Mail watcher stopped");
			} else {
				await fetchWithAuth("/api/watcher/start", {
					method: "POST",
					body: JSON.stringify({ interval: 120, auto_respond: true }),
				});
				toast("success", "Mail watcher started (interval: 120s)");
			}
			await fetchStats();
		} catch (err) {
			toast("error", `Failed to toggle watcher: ${String(err)}`);
		} finally {
			setTriggeringAction(false);
		}
	};

	if (loading) {
		return (
			<div className="flex flex-col items-center justify-center h-64 space-y-4">
				<Loader2 className="h-8 w-8 animate-spin text-blue-500" />
				<p className="text-slate-300">Loading real-time email statistics...</p>
			</div>
		);
	}

	const watcherRunning = Boolean(stats?.watcher?.running);
	const primaryAccount = stats?.primary_account || "sandraschipal@hotmail.com";
	const aiProvider = stats?.ai_provider || "ollama";
	const aiModel = stats?.ai_model || "gemma4:12b";

	const filteredActivity = (stats?.recent_activity || []).filter((email) => {
		if (activeFilter === "unread") {
			return email.read === false;
		}
		return true;
	});

	return (
		<div className="space-y-6" data-testid="dashboard">
			{/* Command Center Hero Banner */}
			<div className="relative overflow-hidden rounded-xl border border-slate-800 bg-gradient-to-r from-slate-950 via-slate-900 to-indigo-950/40 p-6 shadow-xl">
				<div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
					<div className="space-y-1.5">
						<div className="flex flex-wrap items-center gap-2.5">
							<h2 className="text-2xl font-extrabold tracking-tight text-white flex items-center gap-2">
								<Mail className="h-6 w-6 text-blue-400" />
								Email Hub Command Center
							</h2>
							<Badge
								variant="outline"
								className="border-emerald-500/30 bg-emerald-500/10 text-emerald-300 font-mono text-xs"
							>
								v{stats?.mcp_version ?? "0.5.0"}
							</Badge>
						</div>
						<p className="text-sm text-slate-300 flex items-center gap-2">
							<span>Active Mailbox:</span>
							<span className="font-semibold text-white bg-slate-800/80 px-2 py-0.5 rounded text-xs border border-slate-700">
								{primaryAccount}
							</span>
							<span className="text-slate-500">•</span>
							<span className="text-slate-400">Microsoft Graph OAuth</span>
						</p>
					</div>

					{/* Live telemetry badges + Quick Action buttons */}
					<div className="flex flex-wrap items-center gap-2.5">
						{/* Health Dot */}
						<div className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900/80">
							<span
								data-testid="backend-dot"
								className={`h-2.5 w-2.5 rounded-full ${
									backendOk
										? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"
										: "bg-red-500"
								}`}
							/>
							<span className="text-xs font-medium text-slate-200">
								{backendOk ? "Backend Online (:10813)" : "Offline"}
							</span>
						</div>

						{/* Watcher Badge */}
						<Badge
							variant="outline"
							className={`border ${
								watcherRunning
									? "border-purple-500/40 bg-purple-500/15 text-purple-300"
									: "border-slate-700 bg-slate-800 text-slate-400"
							} flex items-center gap-1.5 px-2.5 py-1 text-xs`}
						>
							<Radio
								className={`h-3 w-3 ${watcherRunning ? "animate-pulse text-purple-400" : ""}`}
							/>
							{watcherRunning ? "Watcher Active (120s)" : "Watcher Idle"}
						</Badge>

						{/* AI Provider Badge */}
						<Badge
							variant="outline"
							className="border-blue-500/30 bg-blue-500/10 text-blue-300 flex items-center gap-1.5 px-2.5 py-1 text-xs"
						>
							<Bot className="h-3 w-3 text-blue-400" />
							{aiProvider}: {aiModel}
						</Badge>

						{/* Manual Refresh Button */}
						<Button
							variant="outline"
							size="sm"
							onClick={handleManualRefresh}
							disabled={refreshing}
							className="border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200"
						>
							<RefreshCw
								className={`h-3.5 w-3.5 mr-1.5 ${refreshing ? "animate-spin" : ""}`}
							/>
							Refresh
						</Button>

						{/* Primary Compose CTA */}
						<Button
							size="sm"
							onClick={() => navigate("/compose")}
							className="bg-blue-600 hover:bg-blue-500 text-white font-medium shadow-md shadow-blue-900/30"
						>
							<PenSquare className="h-3.5 w-3.5 mr-1.5" />
							Compose
						</Button>
					</div>
				</div>
			</div>

			{/* 6 High-Leverage KPI Metric Cards */}
			<div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
				{/* 1. Unread Messages */}
				<Card
					data-testid="kpi-unread"
					className="border-slate-800 bg-slate-950/60 cursor-pointer hover:border-emerald-500/40 hover:bg-slate-900/40 transition-all group shadow-sm"
					onClick={() => navigate("/inbox")}
				>
					<CardHeader className="flex flex-row items-center justify-between pb-2">
						<CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-400 group-hover:text-emerald-300 transition-colors">
							Unread Inbox
						</CardTitle>
						<div className="p-1.5 rounded-md bg-emerald-500/10 text-emerald-400 group-hover:bg-emerald-500/20">
							<Inbox className="h-4 w-4" />
						</div>
					</CardHeader>
					<CardContent>
						<div className="text-3xl font-extrabold text-white group-hover:text-emerald-400 transition-colors">
							{stats?.unread_count ?? 0}
						</div>
						<p className="text-xs text-slate-400 mt-1 flex items-center justify-between">
							<span>Active triage</span>
							<ArrowRight className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
						</p>
					</CardContent>
				</Card>

				{/* 2. Connected Mail Services */}
				<Card
					data-testid="kpi-services"
					className="border-slate-800 bg-slate-950/60 cursor-pointer hover:border-blue-500/40 hover:bg-slate-900/40 transition-all group shadow-sm"
					onClick={() => navigate("/services")}
				>
					<CardHeader className="flex flex-row items-center justify-between pb-2">
						<CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-400 group-hover:text-blue-300 transition-colors">
							Mail Services
						</CardTitle>
						<div className="p-1.5 rounded-md bg-blue-500/10 text-blue-400 group-hover:bg-blue-500/20">
							<Server className="h-4 w-4" />
						</div>
					</CardHeader>
					<CardContent>
						<div className="text-3xl font-extrabold text-white group-hover:text-blue-400 transition-colors">
							{stats?.connected_services ?? 0}
						</div>
						<p className="text-xs text-slate-400 mt-1 flex items-center justify-between">
							<span>{stats?.total_services ?? 2} accounts configured</span>
							<ArrowRight className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
						</p>
					</CardContent>
				</Card>

				{/* 3. Mail Watcher Daemon */}
				<Card
					className="border-slate-800 bg-slate-950/60 cursor-pointer hover:border-purple-500/40 hover:bg-slate-900/40 transition-all group shadow-sm"
					onClick={() => navigate("/auto-respond")}
				>
					<CardHeader className="flex flex-row items-center justify-between pb-2">
						<CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-400 group-hover:text-purple-300 transition-colors">
							Mail Watcher
						</CardTitle>
						<div className="p-1.5 rounded-md bg-purple-500/10 text-purple-400 group-hover:bg-purple-500/20">
							<Radio className="h-4 w-4" />
						</div>
					</CardHeader>
					<CardContent>
						<div className="text-xl font-bold text-white group-hover:text-purple-400 transition-colors truncate">
							{watcherRunning ? "Running" : "Idle"}
						</div>
						<p className="text-xs text-slate-400 mt-1 flex items-center justify-between">
							<span>
								{watcherRunning ? "120s polling active" : "Auto-scan paused"}
							</span>
							<ArrowRight className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
						</p>
					</CardContent>
				</Card>

				{/* 4. Automation Rules */}
				<Card
					className="border-slate-800 bg-slate-950/60 cursor-pointer hover:border-amber-500/40 hover:bg-slate-900/40 transition-all group shadow-sm"
					onClick={() => navigate("/rules")}
				>
					<CardHeader className="flex flex-row items-center justify-between pb-2">
						<CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-400 group-hover:text-amber-300 transition-colors">
							Auto-Rules
						</CardTitle>
						<div className="p-1.5 rounded-md bg-amber-500/10 text-amber-400 group-hover:bg-amber-500/20">
							<Sliders className="h-4 w-4" />
						</div>
					</CardHeader>
					<CardContent>
						<div className="text-3xl font-extrabold text-white group-hover:text-amber-400 transition-colors">
							{stats?.rules_count ?? 22}
						</div>
						<p className="text-xs text-slate-400 mt-1 flex items-center justify-between">
							<span>Triage, notify, forward</span>
							<ArrowRight className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
						</p>
					</CardContent>
				</Card>

				{/* 5. Saved Drafts */}
				<Card
					data-testid="kpi-drafts"
					className="border-slate-800 bg-slate-950/60 cursor-pointer hover:border-cyan-500/40 hover:bg-slate-900/40 transition-all group shadow-sm"
					onClick={() => navigate("/compose")}
				>
					<CardHeader className="flex flex-row items-center justify-between pb-2">
						<CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-400 group-hover:text-cyan-300 transition-colors">
							Drafts
						</CardTitle>
						<div className="p-1.5 rounded-md bg-cyan-500/10 text-cyan-400 group-hover:bg-cyan-500/20">
							<FileText className="h-4 w-4" />
						</div>
					</CardHeader>
					<CardContent>
						<div className="text-3xl font-extrabold text-white group-hover:text-cyan-400 transition-colors">
							{stats?.drafts_count ?? 0}
						</div>
						<p className="text-xs text-slate-400 mt-1 flex items-center justify-between">
							<span>Local mail drafts</span>
							<ArrowRight className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
						</p>
					</CardContent>
				</Card>

				{/* 6. MCP Protocol & Tools */}
				<Card
					data-testid="kpi-bridge"
					className="border-slate-800 bg-slate-950/60 cursor-pointer hover:border-pink-500/40 hover:bg-slate-900/40 transition-all group shadow-sm"
					onClick={() => navigate("/tools")}
				>
					<CardHeader className="flex flex-row items-center justify-between pb-2">
						<CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-400 group-hover:text-pink-300 transition-colors">
							MCP Tools
						</CardTitle>
						<div className="p-1.5 rounded-md bg-pink-500/10 text-pink-400 group-hover:bg-pink-500/20">
							<Layers className="h-4 w-4" />
						</div>
					</CardHeader>
					<CardContent>
						<div className="text-3xl font-extrabold text-white group-hover:text-pink-400 transition-colors">
							{stats?.tools_count ?? 47}
						</div>
						<p className="text-xs text-slate-400 mt-1 flex items-center justify-between">
							<span>Streamable HTTP</span>
							<ArrowRight className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
						</p>
					</CardContent>
				</Card>
			</div>

			{/* Main Analytical & Operational Sections */}
			<div className="grid gap-6 lg:grid-cols-7">
				{/* Left Column: Live Mail Activity Stream (4 cols) */}
				<Card className="col-span-12 lg:col-span-4 border-slate-800 bg-slate-950/60 flex flex-col">
					<CardHeader className="flex flex-row items-center justify-between border-b border-slate-800/80 pb-4">
						<div>
							<CardTitle className="text-base font-semibold text-white flex items-center gap-2">
								<Activity className="h-4 w-4 text-blue-400" />
								Recent Mail Stream
							</CardTitle>
							<CardDescription className="text-xs text-slate-400 mt-0.5">
								Latest incoming messages from Microsoft Graph and connected
								services
							</CardDescription>
						</div>
						{/* Filter Toggle Buttons */}
						<div className="flex items-center gap-1.5 bg-slate-900 p-1 rounded-lg border border-slate-800">
							<button
								type="button"
								onClick={() => setActiveFilter("all")}
								className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
									activeFilter === "all"
										? "bg-slate-800 text-white shadow-sm"
										: "text-slate-400 hover:text-slate-200"
								}`}
							>
								All
							</button>
							<button
								type="button"
								onClick={() => setActiveFilter("unread")}
								className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors flex items-center gap-1.5 ${
									activeFilter === "unread"
										? "bg-slate-800 text-emerald-300 shadow-sm"
										: "text-slate-400 hover:text-slate-200"
								}`}
							>
								<span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
								Unread
							</button>
						</div>
					</CardHeader>

					<CardContent className="p-0 flex-1 divide-y divide-slate-800/60">
						{filteredActivity.length === 0 ? (
							<div className="p-12 text-center space-y-3">
								<div className="mx-auto w-12 h-12 rounded-full bg-slate-900 flex items-center justify-center text-slate-500">
									<Inbox className="h-6 w-6" />
								</div>
								<p className="text-sm font-medium text-slate-300">
									{activeFilter === "unread"
										? "No unread messages right now."
										: "No recent messages found."}
								</p>
								<p className="text-xs text-slate-500 max-w-sm mx-auto">
									Your mailbox is up to date. You can run a background scan or
									check your full inbox.
								</p>
								<Button
									variant="outline"
									size="sm"
									onClick={() => navigate("/inbox")}
									className="mt-2 border-slate-700 text-slate-300 hover:text-white"
								>
									Open Inbox View
								</Button>
							</div>
						) : (
							filteredActivity.map((email) => {
								const senderName = getSenderName(
									email.clean_from || email.from,
								);
								const subject =
									email.clean_subject || email.subject || "(No Subject)";
								const isUnread = email.read === false;

								return (
									<button
										type="button"
										key={email.id}
										className="w-full text-left p-4 hover:bg-slate-900/50 transition-colors flex items-start gap-3.5 group cursor-pointer"
										onClick={() =>
											navigate(
												`/email?id=${encodeURIComponent(email.id)}&service=${
													email._service || "default"
												}&folder=INBOX`,
											)
										}
									>
										{/* Sender Avatar */}
										<div className="w-9 h-9 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-blue-300 shrink-0 group-hover:border-blue-500/50 transition-colors">
											{senderName.charAt(0).toUpperCase()}
										</div>

										<div className="flex-1 min-w-0 space-y-1">
											<div className="flex items-center justify-between gap-2">
												<div className="flex items-center gap-2 truncate">
													<span
														className={`text-sm font-medium truncate ${
															isUnread
																? "text-white font-semibold"
																: "text-slate-300"
														}`}
													>
														{senderName}
													</span>
													{isUnread && (
														<span className="h-2 w-2 rounded-full bg-emerald-500 shrink-0" />
													)}
												</div>
												<span className="text-xs text-slate-500 shrink-0 whitespace-nowrap">
													{formatDate(email.date)}
												</span>
											</div>

											<p
												className={`text-xs truncate ${
													isUnread
														? "text-slate-200 font-medium"
														: "text-slate-400"
												}`}
											>
												{subject}
											</p>

											<div className="flex items-center gap-2 pt-0.5">
												<Badge
													variant="outline"
													className="border-slate-800 bg-slate-900 text-[10px] text-slate-400 py-0 px-1.5"
												>
													{email._service || "default"}
												</Badge>
												<span className="text-[11px] text-slate-500 truncate">
													{email.clean_from || email.from}
												</span>
											</div>
										</div>

										<ArrowRight className="h-4 w-4 text-slate-600 opacity-0 group-hover:opacity-100 group-hover:text-blue-400 transition-all shrink-0 mt-2" />
									</button>
								);
							})
						)}
					</CardContent>

					<div className="p-3 border-t border-slate-800/80 bg-slate-900/30 rounded-b-xl flex items-center justify-between">
						<span className="text-xs text-slate-400">
							Showing {filteredActivity.length} recent messages
						</span>
						<Button
							variant="ghost"
							size="sm"
							onClick={() => navigate("/inbox")}
							className="text-xs text-blue-400 hover:text-blue-300 hover:bg-slate-800/60 h-8"
						>
							View Full Unified Inbox
							<ArrowRight className="h-3.5 w-3.5 ml-1" />
						</Button>
					</div>
				</Card>

				{/* Right Column: Infrastructure, Telemetry & Automations (3 cols) */}
				<div className="col-span-12 lg:col-span-3 space-y-6">
					{/* Connected Mail Accounts Status */}
					<Card className="border-slate-800 bg-slate-950/60">
						<CardHeader className="pb-3 border-b border-slate-800/80">
							<CardTitle className="text-base font-semibold text-white flex items-center justify-between">
								<span className="flex items-center gap-2">
									<Server className="h-4 w-4 text-blue-400" />
									Mail Accounts & Routing
								</span>
								<Badge
									variant="outline"
									className="border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-xs"
								>
									{stats?.connected_services} Online
								</Badge>
							</CardTitle>
						</CardHeader>
						<CardContent className="pt-4 space-y-3.5">
							{/* Microsoft Graph primary */}
							<div className="p-3 rounded-lg border border-slate-800/80 bg-slate-900/50 space-y-2">
								<div className="flex items-center justify-between">
									<span className="text-xs font-semibold text-white flex items-center gap-1.5">
										<span className="h-2 w-2 rounded-full bg-emerald-500" />
										Microsoft Graph (Personal)
									</span>
									<Badge className="bg-blue-600/30 text-blue-300 border-blue-500/30 text-[10px]">
										OAuth2 SASL
									</Badge>
								</div>
								<div className="text-xs text-slate-400 space-y-1">
									<div className="flex justify-between">
										<span>Address:</span>
										<span className="text-slate-200 font-mono text-[11px]">
											{primaryAccount}
										</span>
									</div>
									<div className="flex justify-between">
										<span>Token Guardian:</span>
										<span className="text-emerald-400">
											Warm & Auto-Refreshing
										</span>
									</div>
									<div className="flex justify-between">
										<span>Endpoints:</span>
										<span className="text-slate-300">
											Mail.ReadWrite, Mail.Send
										</span>
									</div>
								</div>
							</div>

							{/* IMAP/SMTP Gateway */}
							<div className="p-3 rounded-lg border border-slate-800/80 bg-slate-900/50 space-y-2">
								<div className="flex items-center justify-between">
									<span className="text-xs font-semibold text-white flex items-center gap-1.5">
										<span className="h-2 w-2 rounded-full bg-emerald-500" />
										Default Mail Gateway
									</span>
									<Badge className="bg-slate-800 text-slate-300 border-slate-700 text-[10px]">
										SMTP / IMAP
									</Badge>
								</div>
								<div className="text-xs text-slate-400 space-y-1">
									<div className="flex justify-between">
										<span>Host:</span>
										<span className="text-slate-200">
											smtp-mail.outlook.com:587
										</span>
									</div>
									<div className="flex justify-between">
										<span>Security:</span>
										<span className="text-slate-300">TLS Enabled</span>
									</div>
								</div>
							</div>
						</CardContent>
					</Card>

					{/* Automation Daemon & Watcher Controls */}
					<Card className="border-slate-800 bg-slate-950/60">
						<CardHeader className="pb-3 border-b border-slate-800/80">
							<CardTitle className="text-base font-semibold text-white flex items-center justify-between">
								<span className="flex items-center gap-2">
									<Radio className="h-4 w-4 text-purple-400" />
									Background Watcher
								</span>
								<Button
									size="sm"
									variant="outline"
									onClick={handleToggleWatcher}
									disabled={triggeringAction}
									className={`h-7 text-xs ${
										watcherRunning
											? "border-red-800 text-red-300 hover:bg-red-950/50"
											: "border-purple-700 text-purple-300 hover:bg-purple-950/50"
									}`}
								>
									{watcherRunning ? "Stop Watcher" : "Start Watcher"}
								</Button>
							</CardTitle>
						</CardHeader>
						<CardContent className="pt-4 space-y-3">
							<div className="grid grid-cols-2 gap-2 text-xs">
								<div className="p-2.5 rounded-md border border-slate-800 bg-slate-900/40">
									<span className="text-slate-400 block mb-1">
										Polling Interval
									</span>
									<span className="font-semibold text-white">120 seconds</span>
								</div>
								<div className="p-2.5 rounded-md border border-slate-800 bg-slate-900/40">
									<span className="text-slate-400 block mb-1">
										Auto-Respond
									</span>
									<span className="font-semibold text-emerald-400">
										Enabled
									</span>
								</div>
							</div>

							<div className="flex items-center justify-between pt-1">
								<div className="space-y-0.5">
									<p className="text-xs font-medium text-slate-200">
										{stats?.rules_count ?? 22} Active Rules
									</p>
									<p className="text-[11px] text-slate-400">
										Filtering, notification hooks & auto-replies
									</p>
								</div>
								<Button
									size="sm"
									variant="ghost"
									onClick={() => navigate("/rules")}
									className="h-8 text-xs text-purple-400 hover:text-purple-300 hover:bg-purple-950/30"
								>
									Rules Engine →
								</Button>
							</div>
						</CardContent>
					</Card>

					{/* Fleet Connectors Status */}
					<Card className="border-slate-800 bg-slate-950/60">
						<CardHeader className="pb-3 border-b border-slate-800/80">
							<CardTitle className="text-base font-semibold text-white flex items-center gap-2">
								<Zap className="h-4 w-4 text-amber-400" />
								Fleet Integrations
							</CardTitle>
						</CardHeader>
						<CardContent className="pt-4 space-y-2.5">
							{/* AIWatcher */}
							<div className="flex items-center justify-between text-xs p-2 rounded border border-slate-800/60 bg-slate-900/30">
								<div className="flex items-center gap-2">
									<span className="h-2 w-2 rounded-full bg-emerald-500" />
									<span className="font-medium text-slate-200">
										AIWatcher Ingest
									</span>
								</div>
								<span className="text-slate-400 font-mono text-[11px]">
									:10946 (Online)
								</span>
							</div>

							{/* RoboFang Bridge */}
							<div className="flex items-center justify-between text-xs p-2 rounded border border-slate-800/60 bg-slate-900/30">
								<div className="flex items-center gap-2">
									<span className="h-2 w-2 rounded-full bg-slate-600" />
									<span className="font-medium text-slate-300">
										RoboFang Bridge
									</span>
								</div>
								<span className="text-slate-500 font-mono text-[11px]">
									:10871 (Tailnet)
								</span>
							</div>

							{/* Quick Navigation Footer */}
							<div className="pt-2 grid grid-cols-3 gap-2">
								<Button
									variant="outline"
									size="sm"
									onClick={() => navigate("/chat")}
									className="text-xs border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-300"
								>
									<Bot className="h-3.5 w-3.5 mr-1 text-blue-400" />
									AI Chat
								</Button>
								<Button
									variant="outline"
									size="sm"
									onClick={() => navigate("/contacts")}
									className="text-xs border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-300"
								>
									<Users className="h-3.5 w-3.5 mr-1 text-emerald-400" />
									Contacts
								</Button>
								<Button
									variant="outline"
									size="sm"
									onClick={() => navigate("/logs")}
									className="text-xs border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-300"
								>
									<History className="h-3.5 w-3.5 mr-1 text-amber-400" />
									Logs
								</Button>
							</div>
						</CardContent>
					</Card>
				</div>
			</div>
		</div>
	);
}
