import { ArrowLeft, Loader2, Mail, Search } from "lucide-react";
import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { fetchWithAuth } from "@/lib/api";

type Email = { id: string; subject: string; from: string; date: string };

export function SearchPage() {
	const [searchParams] = useSearchParams();
	const navigate = useNavigate();

	const [query, setQuery] = useState("");
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
		} catch (err: unknown) {
			setError(err instanceof Error ? err.message : "Search failed");
		} finally {
			setLoading(false);
		}
	};

	return (
		<div className="space-y-4">
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
					<h2 className="text-2xl font-bold tracking-tight text-white">
						Search Emails
					</h2>
					<p className="text-slate-400">Full-text search via IMAP</p>
				</div>
			</div>

			<Card className="border-slate-800 bg-slate-950/50">
				<CardContent className="pt-4 pb-4">
					<div className="flex gap-3 flex-wrap items-end">
						<div className="flex-1 min-w-[200px]">
							<label className="text-xs text-slate-400 block mb-1">
								Search
							</label>
							<Input
								className="bg-slate-900 border-slate-700 text-white"
								placeholder="Keywords in subject or body..."
								value={query}
								onChange={(e) => setQuery(e.target.value)}
								onKeyDown={(e) => e.key === "Enter" && handleSearch()}
							/>
						</div>
						<div>
							<label className="text-xs text-slate-400 block mb-1">
								Service
							</label>
							<select
								className="bg-slate-900 border border-slate-700 text-white text-sm rounded px-2 py-1.5"
								value={service}
								onChange={(e) => setService(e.target.value)}
							>
								<option value="default">default</option>
							</select>
						</div>
						<div>
							<label className="text-xs text-slate-400 block mb-1">
								Folder
							</label>
							<select
								className="bg-slate-900 border border-slate-700 text-white text-sm rounded px-2 py-1.5"
								value={folder}
								onChange={(e) => setFolder(e.target.value)}
							>
								{["INBOX", "Sent", "Drafts", "Trash", "Spam"].map((f) => (
									<option key={f}>{f}</option>
								))}
							</select>
						</div>
						<Button
							className="bg-blue-600 hover:bg-blue-700"
							onClick={handleSearch}
							disabled={loading || !query.trim()}
						>
							{loading ? (
								<Loader2 className="h-4 w-4 mr-1 animate-spin" />
							) : (
								<Search className="h-4 w-4 mr-1" />
							)}
							Search
						</Button>
					</div>
				</CardContent>
			</Card>

			{searched && (
				<Card className="border-slate-800 bg-slate-950/50">
					<CardHeader className="pb-2">
						<CardTitle className="text-white text-base">
							{results.length} result{results.length !== 1 ? "s" : ""} for "
							{query}"
						</CardTitle>
					</CardHeader>
					<CardContent>
						{loading && (
							<div className="flex items-center gap-2 text-slate-500 py-8 justify-center">
								<Loader2 className="h-5 w-5 animate-spin" />
								Searching...
							</div>
						)}
						{error && <p className="text-red-400 text-sm py-4">{error}</p>}
						{!loading && !error && results.length === 0 && (
							<p className="text-slate-500 text-sm italic py-8 text-center">
								No results found.
							</p>
						)}
						{results.map((email, i) => (
							<div
								key={email.id || i}
								className="flex items-start gap-3 py-3 border-b border-slate-800 last:border-0 hover:bg-slate-900/30 px-2 rounded transition-colors cursor-pointer"
								onClick={() =>
									navigate(
										`/email?id=${encodeURIComponent(email.id)}&service=${service}&folder=${folder}`,
									)
								}
							>
								<div className="mt-0.5 p-1.5 bg-slate-900 rounded shrink-0">
									<Mail className="h-3.5 w-3.5 text-blue-400" />
								</div>
								<div className="flex-1 min-w-0">
									<p className="text-sm truncate text-white font-medium">
										{email.subject || "(No Subject)"}
									</p>
									<p className="text-xs text-slate-500 truncate">
										{email.from} &nbsp;·&nbsp; {email.date}
									</p>
								</div>
							</div>
						))}
					</CardContent>
				</Card>
			)}
		</div>
	);
}
