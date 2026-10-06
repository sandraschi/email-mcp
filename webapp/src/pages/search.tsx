import {
	ArrowLeft,
	Brain,
	Loader2,
	Mail,
	Search,
	Sparkles,
} from "lucide-react";
import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { fetchWithAuth } from "@/lib/api";

type Email = {
	id: string;
	subject: string;
	from: string;
	date: string;
	score?: number;
	snippet?: string;
	folder?: string;
};

export function SearchPage() {
	const [searchParams] = useSearchParams();
	const navigate = useNavigate();

	const [query, setQuery] = useState("");
	const [searchMode, setSearchMode] = useState<"imap" | "rag">("rag");
	const [service, setService] = useState(
		searchParams.get("service") || "default",
	);
	const [folder, setFolder] = useState(searchParams.get("folder") || "INBOX");
	const [results, setResults] = useState<Email[]>([]);
	const [loading, setLoading] = useState(false);
	const [searched, setSearched] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const handleSearch = async () => {
		if (!query.trim()) return;
		setLoading(true);
		setSearched(true);
		setError(null);
		try {
			if (searchMode === "rag") {
				const params = new URLSearchParams({
					q: query.trim(),
					service: service === "all" ? "" : service,
					folder: folder === "all" ? "" : folder,
					limit: "50",
					min_score: "0.30",
				});
				const data = await fetchWithAuth(`/api/rag/search?${params}`);
				if (data.success) {
					const mapped: Email[] = (data.results || []).map(
						(r: {
							email_id: string;
							subject: string;
							from: string;
							date: string;
							score: number;
							snippet: string;
							folder: string;
						}) => ({
							id: r.email_id,
							subject: r.subject,
							from: r.from,
							date: r.date,
							score: r.score,
							snippet: r.snippet,
							folder: r.folder || folder,
						}),
					);
					setResults(mapped);
				} else {
					setError(data.error || "Neural search failed");
					setResults([]);
				}
			} else {
				const params = new URLSearchParams({
					q: query,
					service,
					folder,
					limit: "50",
				});
				const data = await fetchWithAuth(`/api/search?${params}`);
				if (data.success) {
					setResults(data.emails || []);
				} else {
					setError(data.error || "Search failed");
					setResults([]);
				}
			}
		} catch (err: unknown) {
			setError(err instanceof Error ? err.message : "Search failed");
		} finally {
			setLoading(false);
		}
	};

	return (
		<div className="space-y-4" data-testid="search-page">
			<div className="flex items-center justify-between gap-4">
				<div className="flex items-center gap-4">
					<Button
						variant="outline"
						size="sm"
						className="border-slate-700 text-slate-300 hover:bg-slate-800"
						onClick={() => navigate("/inbox")}
					>
						<ArrowLeft className="h-4 w-4 mr-1" /> Inbox
					</Button>
					<div>
						<h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
							Search Emails
						</h2>
						<p className="text-slate-400">
							{searchMode === "rag"
								? "Neural semantic matching via FastEmbed & LanceDB"
								: "Literal keyword search via IMAP protocol"}
						</p>
					</div>
				</div>

				<div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-1">
					<button
						type="button"
						onClick={() => setSearchMode("rag")}
						className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
							searchMode === "rag"
								? "bg-purple-600 text-white shadow"
								: "text-slate-400 hover:text-white"
						}`}
					>
						<Brain className="h-3.5 w-3.5" />
						Neural RAG
					</button>
					<button
						type="button"
						onClick={() => setSearchMode("imap")}
						className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
							searchMode === "imap"
								? "bg-blue-600 text-white shadow"
								: "text-slate-400 hover:text-white"
						}`}
					>
						<Search className="h-3.5 w-3.5" />
						IMAP Keyword
					</button>
				</div>
			</div>

			<Card className="border-slate-800 bg-slate-950/50">
				<CardContent className="pt-4 pb-4">
					<div className="flex gap-3 flex-wrap items-end">
						<div className="flex-1 min-w-[200px]">
							<label
								htmlFor="search-query"
								className="text-xs text-slate-400 block mb-1"
							>
								{searchMode === "rag"
									? "Semantic Question or Topic"
									: "Keywords"}
							</label>
							<Input
								id="search-query"
								data-testid="search-input"
								className="bg-slate-900 border-slate-700 text-white"
								placeholder={
									searchMode === "rag"
										? "e.g. flight confirmation for San Francisco, payment invoice last month..."
										: "Keywords in subject or body..."
								}
								value={query}
								onChange={(e) => setQuery(e.target.value)}
								onKeyDown={(e) => e.key === "Enter" && handleSearch()}
							/>
						</div>
						<div>
							<label
								htmlFor="search-service"
								className="text-xs text-slate-400 block mb-1"
							>
								Service
							</label>
							<select
								id="search-service"
								data-testid="search-service"
								className="bg-slate-900 border border-slate-700 text-white text-sm rounded px-2 py-1.5"
								value={service}
								onChange={(e) => setService(e.target.value)}
							>
								<option value="default">default</option>
								{searchMode === "rag" && (
									<option value="all">All Services</option>
								)}
							</select>
						</div>
						<div>
							<label
								htmlFor="search-folder"
								className="text-xs text-slate-400 block mb-1"
							>
								Folder
							</label>
							<select
								id="search-folder"
								className="bg-slate-900 border border-slate-700 text-white text-sm rounded px-2 py-1.5"
								value={folder}
								onChange={(e) => setFolder(e.target.value)}
							>
								{searchMode === "rag" && (
									<option value="all">All Folders</option>
								)}
								{["INBOX", "Sent", "Drafts", "Trash", "Spam"].map((f) => (
									<option key={f}>{f}</option>
								))}
							</select>
						</div>
						<Button
							className={
								searchMode === "rag"
									? "bg-purple-600 hover:bg-purple-700"
									: "bg-blue-600 hover:bg-blue-700"
							}
							onClick={handleSearch}
							disabled={loading || !query.trim()}
						>
							{loading ? (
								<Loader2 className="h-4 w-4 mr-1 animate-spin" />
							) : searchMode === "rag" ? (
								<Sparkles className="h-4 w-4 mr-1" />
							) : (
								<Search className="h-4 w-4 mr-1" />
							)}
							{searchMode === "rag" ? "Neural Match" : "Search"}
						</Button>
					</div>
				</CardContent>
			</Card>

			{searched && (
				<Card className="border-slate-800 bg-slate-950/50">
					<CardHeader className="pb-2">
						<CardTitle className="text-white text-base">
							{results.length} result{results.length !== 1 ? "s" : ""} for "
							{query}" {searchMode === "rag" && "(Semantic Matches)"}
						</CardTitle>
					</CardHeader>
					<CardContent>
						{loading && (
							<div className="flex items-center gap-2 text-slate-400 py-8 justify-center">
								<Loader2 className="h-5 w-5 animate-spin" />
								Searching...
							</div>
						)}
						{error && <p className="text-red-400 text-sm py-4">{error}</p>}
						{!loading && !error && results.length === 0 && (
							<p className="text-slate-400 text-sm italic py-8 text-center">
								No results found.{" "}
								{searchMode === "rag" &&
									"Try syncing your mailbox on the RAG / Vectors page."}
							</p>
						)}
						{results.map((email, i) => (
							<button
								type="button"
								key={email.id || i}
								className="flex w-full items-start gap-3 py-3 border-b border-slate-800 last:border-0 hover:bg-slate-900/30 px-2 rounded transition-colors cursor-pointer text-left"
								onClick={() =>
									navigate(
										`/email?id=${encodeURIComponent(email.id)}&service=${service === "all" ? "default" : service}&folder=${email.folder || folder}`,
									)
								}
							>
								<div className="mt-0.5 p-1.5 bg-slate-900 rounded shrink-0">
									<Mail className="h-3.5 w-3.5 text-blue-400" />
								</div>
								<div className="flex-1 min-w-0">
									<div className="flex items-center justify-between gap-2">
										<p className="text-sm truncate text-white font-medium">
											{email.subject || "(No Subject)"}
										</p>
										{email.score !== undefined && (
											<span className="text-xs px-2 py-0.5 rounded-full bg-purple-950/80 text-purple-300 border border-purple-800 font-mono shrink-0">
												score: {email.score.toFixed(3)}
											</span>
										)}
									</div>
									<p className="text-xs text-slate-400 truncate mt-0.5">
										{email.from} &nbsp;·&nbsp; {email.date}
										{email.folder && ` · ${email.folder}`}
									</p>
									{email.snippet && (
										<p className="text-xs text-slate-400 mt-1 line-clamp-2 bg-slate-900/40 p-1.5 rounded">
											{email.snippet}
										</p>
									)}
								</div>
							</button>
						))}
					</CardContent>
				</Card>
			)}
		</div>
	);
}
