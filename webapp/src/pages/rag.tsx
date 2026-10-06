import {
	Activity,
	ArrowRight,
	Brain,
	CheckCircle2,
	Clock,
	Database,
	FolderSync,
	Layers,
	Loader2,
	Mail,
	Play,
	RefreshCw,
	Search,
	Sparkles,
	Zap,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { fetchWithAuth } from "@/lib/api";

interface RagStats {
	total_chunks: number;
	storage_mb: number;
	indexed_services: string[];
	embedding_model: string;
	gpu_accelerated: boolean;
	status: string;
}

interface RagJobStatus {
	job_id: string;
	status: "queued" | "running" | "complete" | "error";
	phase: string;
	chunks: number;
	emails_processed: number;
	current: number;
	total: number;
	elapsed_seconds: number;
	error: string | null;
	message: string | null;
}

interface SearchResultItem {
	id: string;
	email_id: string;
	service: string;
	folder: string;
	subject: string;
	from: string;
	to: string;
	date: string;
	snippet: string;
	score: number;
	content?: string;
}

export function RagPage() {
	const navigate = useNavigate();

	// Stats
	const [stats, setStats] = useState<RagStats | null>(null);
	const [loadingStats, setLoadingStats] = useState(true);

	// Sweep controls
	const [service, setService] = useState("default");
	const [folder, setFolder] = useState("INBOX");
	const [limit, setLimit] = useState(100);
	const [isSweeping, setIsSweeping] = useState(false);
	const [activeJob, setActiveJob] = useState<RagJobStatus | null>(null);

	// Search console
	const [searchQuery, setSearchQuery] = useState("");
	const [searching, setSearching] = useState(false);
	const [minScore, setMinScore] = useState(0.35);
	const [searchResults, setSearchResults] = useState<SearchResultItem[]>([]);
	const [searchExecuted, setSearchExecuted] = useState(false);

	const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

	const loadStats = useCallback(async () => {
		try {
			setLoadingStats(true);
			const data = await fetchWithAuth("/api/rag/stats");
			if (data.success) {
				setStats(data);
			}
		} catch {
			// silently ignore on initial render
		} finally {
			setLoadingStats(false);
		}
	}, []);

	useEffect(() => {
		loadStats();
		return () => {
			if (pollIntervalRef.current) {
				clearInterval(pollIntervalRef.current);
			}
		};
	}, [loadStats]);

	const openEmail = (item: SearchResultItem) =>
		navigate(
			`/email?id=${encodeURIComponent(item.email_id)}&service=${item.service}&folder=${item.folder}`,
		);

	const triggerSweep = async (fullReindex: boolean) => {
		setIsSweeping(true);
		try {
			const res = await fetchWithAuth("/api/rag/sweep", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					service,
					folder,
					limit,
					full_reindex: fullReindex,
				}),
			});

			if (!res.success || !res.job_id) {
				setIsSweeping(false);
				return;
			}

			const jobId = res.job_id;
			pollJob(jobId);
		} catch {
			setIsSweeping(false);
		}
	};

	const pollJob = (jobId: string) => {
		if (pollIntervalRef.current) {
			clearInterval(pollIntervalRef.current);
		}

		pollIntervalRef.current = setInterval(async () => {
			try {
				const statusData: RagJobStatus = await fetchWithAuth(
					`/api/rag/status/${jobId}`,
				);
				setActiveJob(statusData);

				if (statusData.status === "complete" || statusData.status === "error") {
					if (pollIntervalRef.current) {
						clearInterval(pollIntervalRef.current);
						pollIntervalRef.current = null;
					}
					setIsSweeping(false);
					loadStats();
				}
			} catch {
				// retry on next tick
			}
		}, 1000);
	};

	const handleSearch = async () => {
		if (!searchQuery.trim()) return;
		setSearching(true);
		setSearchExecuted(true);
		try {
			const params = new URLSearchParams({
				q: searchQuery.trim(),
				service: service === "all" ? "" : service,
				folder: folder === "all" ? "" : folder,
				min_score: minScore.toString(),
				limit: "15",
			});
			const res = await fetchWithAuth(`/api/rag/search?${params}`);
			if (res.success) {
				setSearchResults(res.results || []);
			} else {
				setSearchResults([]);
			}
		} catch {
			setSearchResults([]);
		} finally {
			setSearching(false);
		}
	};

	return (
		<div className="space-y-6" data-testid="rag-operations-page">
			{/* Page Header */}
			<div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
				<div>
					<div className="flex items-center gap-2">
						<Brain className="h-6 w-6 text-purple-400" />
						<h1 className="text-2xl font-bold tracking-tight text-white">
							Email RAG Operations & Vector Store
						</h1>
					</div>
					<p className="text-sm text-slate-400 mt-1">
						Local LanceDB vector repository and FastEmbed semantic retrieval
						engine
					</p>
				</div>
				<Button
					variant="outline"
					size="sm"
					onClick={loadStats}
					disabled={loadingStats}
					className="border-slate-700 text-slate-300 hover:bg-slate-800"
				>
					<RefreshCw
						className={`h-4 w-4 mr-2 ${loadingStats ? "animate-spin" : ""}`}
					/>
					Refresh Telemetry
				</Button>
			</div>

			{/* KPI Header Cards */}
			<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
				<Card className="border-slate-800 bg-slate-950/60">
					<CardContent className="pt-5">
						<div className="flex items-center justify-between">
							<span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
								Indexed Chunks
							</span>
							<Layers className="h-4 w-4 text-purple-400" />
						</div>
						<div className="text-2xl font-bold text-white mt-2">
							{loadingStats
								? "..."
								: (stats?.total_chunks ?? 0).toLocaleString()}
						</div>
						<span className="text-xs text-slate-400 mt-1 block">
							LanceDB neural passages
						</span>
					</CardContent>
				</Card>

				<Card className="border-slate-800 bg-slate-950/60">
					<CardContent className="pt-5">
						<div className="flex items-center justify-between">
							<span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
								Embedding Model
							</span>
							<Sparkles className="h-4 w-4 text-blue-400" />
						</div>
						<div className="text-base font-bold text-white mt-2 truncate">
							{stats?.embedding_model
								? stats.embedding_model.split("/").pop()
								: "bge-small-en-v1.5"}
						</div>
						<span className="text-xs text-slate-400 mt-1 block">
							384 dimensions (FastEmbed)
						</span>
					</CardContent>
				</Card>

				<Card className="border-slate-800 bg-slate-950/60">
					<CardContent className="pt-5">
						<div className="flex items-center justify-between">
							<span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
								Hardware Accelerator
							</span>
							<Zap className="h-4 w-4 text-amber-400" />
						</div>
						<div className="flex items-center gap-2 mt-2">
							<span
								className={`inline-block h-2 w-2 rounded-full ${stats?.gpu_accelerated ? "bg-emerald-400" : "bg-blue-400"}`}
							/>
							<span className="text-lg font-bold text-white">
								{stats?.gpu_accelerated ? "CUDA (GPU)" : "CPU (Optimized)"}
							</span>
						</div>
						<span className="text-xs text-slate-400 mt-1 block">
							{stats?.gpu_accelerated
								? "CUDAExecutionProvider"
								: "ONNX Runtime fallback"}
						</span>
					</CardContent>
				</Card>

				<Card className="border-slate-800 bg-slate-950/60">
					<CardContent className="pt-5">
						<div className="flex items-center justify-between">
							<span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
								Vector Footprint
							</span>
							<Database className="h-4 w-4 text-emerald-400" />
						</div>
						<div className="text-2xl font-bold text-white mt-2">
							{loadingStats ? "..." : `${stats?.storage_mb ?? 0} MB`}
						</div>
						<span className="text-xs text-slate-400 mt-1 block">
							LanceDB on-disk storage
						</span>
					</CardContent>
				</Card>
			</div>

			{/* Sweep Control Plane */}
			<Card className="border-slate-800 bg-slate-950/50">
				<CardHeader className="pb-3">
					<CardTitle className="text-base font-semibold text-white flex items-center gap-2">
						<FolderSync className="h-5 w-5 text-purple-400" />
						Index Synchronization & Sweeps
					</CardTitle>
				</CardHeader>
				<CardContent className="space-y-4">
					<div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
						<div>
							<label
								htmlFor="rag-service"
								className="text-xs text-slate-400 block mb-1"
							>
								Email Service
							</label>
							<select
								id="rag-service"
								value={service}
								onChange={(e) => setService(e.target.value)}
								className="w-full bg-slate-900 border border-slate-700 text-white text-sm rounded px-3 py-2"
							>
								<option value="default">default</option>
								{stats?.indexed_services?.map(
									(s) =>
										s !== "default" && (
											<option key={s} value={s}>
												{s}
											</option>
										),
								)}
							</select>
						</div>

						<div>
							<label
								htmlFor="rag-folder"
								className="text-xs text-slate-400 block mb-1"
							>
								Mailbox Folder
							</label>
							<select
								id="rag-folder"
								value={folder}
								onChange={(e) => setFolder(e.target.value)}
								className="w-full bg-slate-900 border border-slate-700 text-white text-sm rounded px-3 py-2"
							>
								{["INBOX", "Sent", "Archive", "Drafts", "Trash"].map((f) => (
									<option key={f} value={f}>
										{f}
									</option>
								))}
							</select>
						</div>

						<div>
							<label
								htmlFor="rag-limit"
								className="text-xs text-slate-400 block mb-1"
							>
								Message Scan Limit
							</label>
							<Input
								id="rag-limit"
								type="number"
								value={limit}
								onChange={(e) =>
									setLimit(
										Math.max(
											1,
											Math.min(1000, parseInt(e.target.value, 10) || 10),
										),
									)
								}
								className="bg-slate-900 border-slate-700 text-white"
								min={1}
								max={1000}
							/>
						</div>
					</div>

					<div className="flex flex-wrap items-center gap-3 pt-2">
						<Button
							onClick={() => triggerSweep(false)}
							disabled={isSweeping}
							className="bg-purple-600 hover:bg-purple-700 text-white"
						>
							{isSweeping && !activeJob?.phase.includes("reindex") ? (
								<Loader2 className="h-4 w-4 mr-2 animate-spin" />
							) : (
								<Play className="h-4 w-4 mr-2" />
							)}
							Incremental Sweep (Scan New)
						</Button>

						<Button
							variant="outline"
							onClick={() => triggerSweep(true)}
							disabled={isSweeping}
							className="border-slate-700 text-slate-300 hover:bg-slate-800"
						>
							{isSweeping && activeJob?.phase.includes("reindex") ? (
								<Loader2 className="h-4 w-4 mr-2 animate-spin" />
							) : (
								<RefreshCw className="h-4 w-4 mr-2" />
							)}
							Full Rebuild (Wipe & Re-embed)
						</Button>
					</div>

					{/* Active Job Terminal & Running Progress */}
					{activeJob && (
						<div className="mt-4 p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3">
							<div className="flex items-center justify-between">
								<div className="flex items-center gap-2">
									{activeJob.status === "running" && (
										<Loader2 className="h-4 w-4 text-purple-400 animate-spin" />
									)}
									{activeJob.status === "complete" && (
										<CheckCircle2 className="h-4 w-4 text-emerald-400" />
									)}
									{activeJob.status === "error" && (
										<Activity className="h-4 w-4 text-red-400" />
									)}
									<span className="text-sm font-semibold text-white capitalize">
										{activeJob.phase}
									</span>
								</div>
								<div className="flex items-center gap-3 text-xs text-slate-400">
									<span className="flex items-center gap-1">
										<Clock className="h-3.5 w-3.5" />
										T+{activeJob.elapsed_seconds}s
									</span>
									<span className="text-slate-400">|</span>
									<span>Job: {activeJob.job_id.slice(0, 8)}</span>
								</div>
							</div>

							{activeJob.total > 0 && (
								<div className="space-y-1">
									<div className="flex justify-between text-xs text-slate-400">
										<span>Processing items...</span>
										<span>
											{activeJob.current} / {activeJob.total} (
											{Math.round((activeJob.current / activeJob.total) * 100)}
											%)
										</span>
									</div>
									<div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
										<div
											className="bg-purple-500 h-2 rounded-full transition-all duration-300"
											style={{
												width: `${Math.min(100, Math.round((activeJob.current / activeJob.total) * 100))}%`,
											}}
										/>
									</div>
								</div>
							)}

							<div className="text-xs text-slate-400 flex items-center justify-between">
								<span>
									Indexed:{" "}
									<strong className="text-white">
										{activeJob.chunks} chunks
									</strong>{" "}
									across{" "}
									<strong className="text-white">
										{activeJob.emails_processed} emails
									</strong>
								</span>
								{activeJob.message && (
									<span className="text-slate-300">{activeJob.message}</span>
								)}
								{activeJob.error && (
									<span className="text-red-400 font-medium">
										{activeJob.error}
									</span>
								)}
							</div>
						</div>
					)}
				</CardContent>
			</Card>

			{/* Neural Search Console */}
			<Card className="border-slate-800 bg-slate-950/50">
				<CardHeader className="pb-3">
					<CardTitle className="text-base font-semibold text-white flex items-center gap-2">
						<Search className="h-5 w-5 text-blue-400" />
						Interactive Neural Retrieval Console
					</CardTitle>
				</CardHeader>
				<CardContent className="space-y-4">
					<div className="flex flex-col sm:flex-row gap-3">
						<div className="flex-1">
							<Input
								value={searchQuery}
								onChange={(e) => setSearchQuery(e.target.value)}
								onKeyDown={(e) => e.key === "Enter" && handleSearch()}
								placeholder="Ask questions or search topics across emails (e.g. 'flight confirmations', 'Q3 budget notes')..."
								className="bg-slate-900 border-slate-700 text-white"
							/>
						</div>
						<div className="flex items-center gap-2">
							<span className="text-xs text-slate-400 whitespace-nowrap">
								Min Score:
							</span>
							<select
								value={minScore}
								onChange={(e) => setMinScore(parseFloat(e.target.value))}
								className="bg-slate-900 border border-slate-700 text-white text-xs rounded px-2 py-2"
							>
								<option value="0.25">0.25 (Loose)</option>
								<option value="0.35">0.35 (Default)</option>
								<option value="0.45">0.45 (Strict)</option>
								<option value="0.55">0.55 (High Exactness)</option>
							</select>
							<Button
								onClick={handleSearch}
								disabled={searching || !searchQuery.trim()}
								className="bg-blue-600 hover:bg-blue-700 text-white shrink-0"
							>
								{searching ? (
									<Loader2 className="h-4 w-4 mr-1 animate-spin" />
								) : (
									<Search className="h-4 w-4 mr-1" />
								)}
								Neural Match
							</Button>
						</div>
					</div>

					{/* Results list */}
					{searchExecuted && (
						<div className="space-y-3 pt-2">
							<div className="text-xs text-slate-400 flex items-center justify-between">
								<span>
									Showing <strong>{searchResults.length}</strong> semantic
									match(es)
								</span>
							</div>

							{searchResults.length === 0 && !searching && (
								<p className="text-sm text-slate-400 italic py-6 text-center">
									No vector passages met the relevance threshold ({minScore})
									for "{searchQuery}". Try performing an Incremental Sweep
									above.
								</p>
							)}

							<div className="space-y-2">
								{searchResults.map((item) => (
									// biome-ignore lint/a11y/useSemanticElements: the row holds block-level content (div/h4/p), which a <button> cannot validly contain; role, tab stop and Enter/Space handling are provided
									<div
										key={item.id}
										role="button"
										tabIndex={0}
										className="p-3.5 rounded-lg border border-slate-800 bg-slate-900/40 hover:bg-slate-900/70 transition-colors cursor-pointer"
										onClick={() => openEmail(item)}
										onKeyDown={(e) => {
											if (e.key === "Enter" || e.key === " ") {
												e.preventDefault();
												openEmail(item);
											}
										}}
									>
										<div className="flex items-start justify-between gap-3">
											<div className="flex items-center gap-2">
												<Mail className="h-4 w-4 text-blue-400 shrink-0" />
												<h4 className="text-sm font-semibold text-white truncate">
													{item.subject || "(No Subject)"}
												</h4>
											</div>
											<div className="flex items-center gap-2 shrink-0">
												<span className="text-xs px-2 py-0.5 rounded-full bg-purple-950/80 text-purple-300 border border-purple-800 font-mono">
													score: {item.score.toFixed(3)}
												</span>
												<ArrowRight className="h-3.5 w-3.5 text-slate-400" />
											</div>
										</div>

										<p className="text-xs text-slate-400 mt-1">
											From: <span className="text-slate-300">{item.from}</span>{" "}
											&nbsp;·&nbsp; {item.date} &nbsp;·&nbsp; Folder:{" "}
											<span className="text-slate-300">{item.folder}</span>
										</p>

										<div className="mt-2 text-xs text-slate-300 bg-slate-950/50 p-2.5 rounded border border-slate-800/80 font-sans leading-relaxed">
											{item.snippet}
										</div>
									</div>
								))}
							</div>
						</div>
					)}
				</CardContent>
			</Card>
		</div>
	);
}
