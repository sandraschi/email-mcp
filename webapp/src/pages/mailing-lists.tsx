import {
	ArrowLeft,
	Loader2,
	Mail,
	Newspaper,
	Plus,
	RefreshCw,
	Send,
	Trash2,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { fetchWithAuth } from "@/lib/api";

type Preset = {
	id: string;
	service: string;
	folder: string;
	limit: number;
	unread_only: boolean;
	from_contains?: string | null;
	subject_contains?: string | null;
	description?: string;
	readonly?: boolean;
	source?: string;
};

type CrawlItem = {
	id: string;
	subject: string;
	from: string;
	date: string;
};

type DistillItem = CrawlItem & {
	summary: string;
	links: string[];
};

const EMPTY_FORM: Preset = {
	id: "",
	service: "default",
	folder: "AI",
	limit: 10,
	unread_only: false,
	from_contains: "",
	subject_contains: "",
	description: "",
};

export function MailingLists() {
	const navigate = useNavigate();
	const [lists, setLists] = useState<Preset[]>([]);
	const [selected, setSelected] = useState<string>("");
	const [form, setForm] = useState<Preset>(EMPTY_FORM);
	const [editing, setEditing] = useState(false);
	const [crawl, setCrawl] = useState<CrawlItem[]>([]);
	const [checked, setChecked] = useState<Set<string>>(new Set());
	const [days, setDays] = useState(3);
	const [report, setReport] = useState("");
	const [distilled, setDistilled] = useState<DistillItem[]>([]);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const loadLists = useCallback(async () => {
		try {
			const data = await fetchWithAuth("/api/mailing-lists");
			setLists(data.lists || []);
			if (data.lists?.length && !selected) setSelected(data.lists[0].id);
		} catch (err) {
			setError(err instanceof Error ? err.message : "Failed to load lists");
		}
	}, [selected]);

	useEffect(() => {
		void loadLists();
	}, [loadLists]);

	const handleSave = async () => {
		if (!form.id.trim()) {
			setError("id is required (e.g. alphasignal)");
			return;
		}
		setLoading(true);
		setError(null);
		try {
			const method = editing ? "PUT" : "POST";
			const url = editing
				? `/api/mailing-lists/${encodeURIComponent(form.id)}`
				: "/api/mailing-lists";
			await fetchWithAuth(url, { method, body: JSON.stringify(form) });
			setForm(EMPTY_FORM);
			setEditing(false);
			await loadLists();
			setSelected(form.id.trim());
		} catch (err) {
			setError(err instanceof Error ? err.message : "Save failed");
		} finally {
			setLoading(false);
		}
	};

	const handleDelete = async (id: string) => {
		if (!confirm(`Delete preset ${id}?`)) return;
		try {
			await fetchWithAuth(`/api/mailing-lists/${encodeURIComponent(id)}`, {
				method: "DELETE",
			});
			if (selected === id) {
				setSelected("");
				setCrawl([]);
			}
			await loadLists();
		} catch (err) {
			setError(err instanceof Error ? err.message : "Delete failed");
		}
	};

	const handleCrawl = async () => {
		if (!selected) return;
		setLoading(true);
		setError(null);
		setReport("");
		try {
			const data = await fetchWithAuth(
				`/api/mailing-lists/${encodeURIComponent(selected)}/crawl?days=${days}&limit=20`,
			);
			setCrawl(data.emails || []);
			setChecked(new Set((data.emails || []).map((e: CrawlItem) => e.id)));
		} catch (err) {
			setError(err instanceof Error ? err.message : "Crawl failed");
		} finally {
			setLoading(false);
		}
	};

	const handleDistill = async (push = false) => {
		if (!selected) return;
		setLoading(true);
		setError(null);
		try {
			const data = await fetchWithAuth(
				`/api/mailing-lists/${encodeURIComponent(selected)}/distill`,
				{
					method: "POST",
					body: JSON.stringify({
						email_ids: [...checked],
						days,
						push_aiwatcher: push,
						urgency_hint: 7.0,
					}),
				},
			);
			setDistilled(data.items || []);
			setReport(data.report_md || "");
			if (push && data.pushed && !data.pushed.success) {
				setError(`AIWatcher push failed: ${data.pushed.error || "unknown"}`);
			}
		} catch (err) {
			setError(err instanceof Error ? err.message : "Distill failed");
		} finally {
			setLoading(false);
		}
	};

	const seedAlpha = async () => {
		setForm({
			id: "alphasignal",
			service: "default",
			folder: "AI",
			limit: 10,
			unread_only: false,
			from_contains: "news@alphasignal.ai",
			subject_contains: "",
			description: "AlphaSignal daily AI news",
		});
		setEditing(false);
	};

	return (
		<div className="space-y-4" data-testid="mailing-lists-page">
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
						<Newspaper className="h-6 w-6 text-blue-400" /> Mailing Lists
					</h2>
					<p className="text-slate-400">
						Sender presets, 3-day crawl, distilled digest. In-page now,
						AIWatcher on push.
					</p>
				</div>
			</div>

			{error && (
				<div className="text-sm text-red-400 border border-red-900 rounded p-2">
					{error}
				</div>
			)}

			<div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
				<Card className="bg-slate-900 border-slate-800">
					<CardHeader>
						<CardTitle className="text-white text-sm">
							Presets ({lists.length})
						</CardTitle>
					</CardHeader>
					<CardContent className="space-y-2">
						{lists.map((l) => (
							<div
								key={l.id}
								className={`flex items-center justify-between rounded p-2 border ${selected === l.id ? "border-blue-600 bg-slate-800" : "border-slate-800"}`}
							>
								<button
									type="button"
									className="text-left flex-1"
									onClick={() => setSelected(l.id)}
								>
									<div className="text-slate-200 text-sm font-medium">
										{l.id}{" "}
										{l.readonly && (
											<span className="text-xs text-slate-500">(env)</span>
										)}
									</div>
									<div className="text-xs text-slate-500">
										{l.service}/{l.folder}{" "}
										{l.from_contains ? `· ${l.from_contains}` : ""}
									</div>
								</button>
								{!l.readonly && (
									<div className="flex gap-1">
										<Button
											variant="ghost"
											size="sm"
											onClick={() => {
												setForm({ ...l });
												setEditing(true);
											}}
										>
											Edit
										</Button>
										<Button
											variant="ghost"
											size="sm"
											onClick={() => void handleDelete(l.id)}
										>
											<Trash2 className="h-3 w-3" />
										</Button>
									</div>
								)}
							</div>
						))}
						<Button
							variant="outline"
							size="sm"
							className="w-full border-slate-700"
							onClick={() => void seedAlpha()}
						>
							<Plus className="h-3 w-3 mr-1" /> Seed AlphaSignal preset
						</Button>
					</CardContent>
				</Card>

				<Card className="bg-slate-900 border-slate-800">
					<CardHeader>
						<CardTitle className="text-white text-sm">
							{editing ? "Edit preset" : "New preset"}
						</CardTitle>
					</CardHeader>
					<CardContent className="space-y-2">
						<Input
							placeholder="id (alphasignal)"
							value={form.id}
							disabled={editing}
							onChange={(e) => setForm({ ...form, id: e.target.value })}
						/>
						<div className="grid grid-cols-2 gap-2">
							<Input
								placeholder="service"
								value={form.service}
								onChange={(e) => setForm({ ...form, service: e.target.value })}
							/>
							<Input
								placeholder="folder"
								value={form.folder}
								onChange={(e) => setForm({ ...form, folder: e.target.value })}
							/>
						</div>
						<Input
							placeholder="from_contains"
							value={form.from_contains || ""}
							onChange={(e) =>
								setForm({ ...form, from_contains: e.target.value })
							}
						/>
						<Input
							placeholder="subject_contains"
							value={form.subject_contains || ""}
							onChange={(e) =>
								setForm({ ...form, subject_contains: e.target.value })
							}
						/>
						<Input
							placeholder="description"
							value={form.description || ""}
							onChange={(e) =>
								setForm({ ...form, description: e.target.value })
							}
						/>
						<Button
							className="w-full"
							disabled={loading}
							onClick={() => void handleSave()}
						>
							{loading ? (
								<Loader2 className="h-4 w-4 animate-spin" />
							) : (
								"Save preset"
							)}
						</Button>
					</CardContent>
				</Card>

				<Card className="bg-slate-900 border-slate-800">
					<CardHeader>
						<CardTitle className="text-white text-sm">Crawl</CardTitle>
					</CardHeader>
					<CardContent className="space-y-2">
						<div className="flex items-center gap-2">
							<Input
								type="number"
								min={1}
								max={14}
								value={days}
								onChange={(e) => setDays(Number(e.target.value) || 3)}
								className="w-20"
							/>
							<span className="text-xs text-slate-500">days</span>
							<Button
								size="sm"
								disabled={!selected || loading}
								onClick={() => void handleCrawl()}
							>
								<RefreshCw className="h-3 w-3 mr-1" /> Crawl {selected || "…"}
							</Button>
						</div>
						<p className="text-xs text-slate-500">
							{crawl.length} issues in window. Checked ones go into the digest.
						</p>
						<div className="flex gap-2">
							<Button
								size="sm"
								variant="outline"
								className="border-slate-700"
								disabled={!checked.size || loading}
								onClick={() => void handleDistill(false)}
							>
								<Mail className="h-3 w-3 mr-1" /> Distill in-page
							</Button>
							<Button
								size="sm"
								disabled={!checked.size || loading}
								onClick={() => void handleDistill(true)}
							>
								<Send className="h-3 w-3 mr-1" /> Distill + push AIWatcher
							</Button>
						</div>
					</CardContent>
				</Card>
			</div>

			{crawl.length > 0 && (
				<Card className="bg-slate-900 border-slate-800">
					<CardHeader>
						<CardTitle className="text-white text-sm">
							Crawl results ({crawl.length})
						</CardTitle>
					</CardHeader>
					<CardContent className="space-y-1">
						{crawl.map((e) => (
							<label
								key={e.id}
								className="flex items-start gap-2 text-sm border-b border-slate-800 py-1"
							>
								<input
									type="checkbox"
									checked={checked.has(e.id)}
									onChange={() => {
										const next = new Set(checked);
										if (next.has(e.id)) next.delete(e.id);
										else next.add(e.id);
										setChecked(next);
									}}
								/>
								<span className="text-slate-200 flex-1">{e.subject}</span>
								<span className="text-xs text-slate-500">
									{e.date?.slice(0, 10)}
								</span>
							</label>
						))}
					</CardContent>
				</Card>
			)}

			{(distilled.length > 0 || report) && (
				<Card className="bg-slate-900 border-slate-800">
					<CardHeader>
						<CardTitle className="text-white text-sm">
							Distilled digest ({distilled.length})
						</CardTitle>
					</CardHeader>
					<CardContent className="space-y-3">
						{distilled.map((d) => (
							<div key={d.id} className="border-b border-slate-800 pb-2">
								<div className="text-slate-100 font-medium">{d.subject}</div>
								<div className="text-xs text-slate-500">
									{d.from} · {d.date?.slice(0, 10)}
								</div>
								<p className="text-sm text-slate-300 mt-1">
									{d.summary?.slice(0, 600)}
								</p>
								{d.links?.length > 0 && (
									<div className="text-xs text-blue-400 mt-1 space-y-0.5">
										{d.links.slice(0, 5).map((u) => (
											<div key={u} className="truncate">
												<a href={u} target="_blank" rel="noreferrer">
													{u}
												</a>
											</div>
										))}
									</div>
								)}
							</div>
						))}
						{report && (
							<pre className="text-xs text-slate-300 whitespace-pre-wrap bg-slate-950 rounded p-2 max-h-96 overflow-auto">
								{report.slice(0, 12000)}
							</pre>
						)}
					</CardContent>
				</Card>
			)}
		</div>
	);
}
