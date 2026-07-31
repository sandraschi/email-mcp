import {
	AlertCircle,
	Clock,
	Filter,
	Inbox as InboxIcon,
	Loader2,
	Mail,
	RefreshCw,
	Search,
	Trash2,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useToast } from "@/components/toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { fetchWithAuth } from "@/lib/api";

type Email = {
	id: string;
	subject: string;
	from: string;
	date: string;
	read: boolean;
	_service?: string;
};

type Service = { name: string; type: string };

const AUTO_REFRESH_MS = 30_000; // 30 seconds

export function Inbox() {
	const navigate = useNavigate();
	const { toast } = useToast();

	const [emails, setEmails] = useState<Email[]>([]);
	const [services, setServices] = useState<Service[]>([]);
	const [folders, setFolders] = useState<string[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [selectedService, setSelectedService] = useState("default");
	const [folder, setFolder] = useState("INBOX");
	const [limit, setLimit] = useState(20);
	const [unreadOnly, setUnreadOnly] = useState(false);
	const [fromFilter, setFromFilter] = useState("");
	const [subjectFilter, setSubjectFilter] = useState("");
	const [showFilters, setShowFilters] = useState(false);
	const [autoRefresh, setAutoRefresh] = useState(true);
	const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set());
	const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

	const fetchEmails = useCallback(async () => {
		setLoading(true);
		setError(null);
		try {
			const params = new URLSearchParams({
				service: selectedService,
				folder,
				limit: String(limit),
				unread_only: String(unreadOnly),
				...(fromFilter ? { from_contains: fromFilter } : {}),
				...(subjectFilter ? { subject_contains: subjectFilter } : {}),
			});
			const data = await fetchWithAuth(`/api/inbox?${params}`);
			if (data.success === false) {
				setError(data.error || "Failed to fetch inbox");
				setEmails([]);
			} else {
				setEmails(data.emails || []);
			}
		} catch (err: unknown) {
			setError(err instanceof Error ? err.message : String(err));
		} finally {
			setLoading(false);
		}
	}, [selectedService, folder, limit, unreadOnly, fromFilter, subjectFilter]);

	useEffect(() => {
		fetchWithAuth("/api/services")
			.then((data) => {
				const svcMap = data.services || {};
				const list: Service[] = Object.entries(svcMap).map(([name, info]) => ({
					name,
					type: (info as { type?: string } | undefined)?.type ?? "",
				}));
				setServices(list);
			})
			.catch(() => {});
	}, []);

	// Load folders when service changes
	const fetchFolders = useCallback(async () => {
		try {
			const data = await fetchWithAuth(
				`/api/services/${encodeURIComponent(selectedService)}/folders`,
			);
			const folderNames = (data.folders || []).map(
				(f: { name: string }) => f.name,
			);
			if (folderNames.length > 0) {
				setFolders(folderNames);
			}
		} catch {
			/* ignore */
		}
	}, [selectedService]);

	useEffect(() => {
		fetchFolders();
	}, [fetchFolders]);

	useEffect(() => {
		fetchEmails();
	}, [fetchEmails]);

	useEffect(() => {
		if (autoRefresh) {
			intervalRef.current = setInterval(fetchEmails, AUTO_REFRESH_MS);
		}
		return () => {
			if (intervalRef.current) clearInterval(intervalRef.current);
		};
	}, [autoRefresh, fetchEmails]);

	const handleDelete = async (e: React.MouseEvent, emailId: string) => {
		e.stopPropagation();
		if (deletingIds.has(emailId)) return;
		setDeletingIds((prev) => new Set(prev).add(emailId));
		try {
			await fetchWithAuth(
				`/api/inbox/${encodeURIComponent(emailId)}?service=${selectedService}&folder=${folder}`,
				{ method: "DELETE" },
			);
			setEmails((prev) => prev.filter((em) => em.id !== emailId));
			toast("success", "Email deleted");
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "Delete failed");
		} finally {
			setDeletingIds((prev) => {
				const next = new Set(prev);
				next.delete(emailId);
				return next;
			});
		}
	};

	const handleOpenEmail = (email: Email) => {
		navigate(
			`/email?id=${encodeURIComponent(email.id)}&service=${selectedService}&folder=${folder}`,
		);
	};

	return (
		<div className="space-y-4" data-testid="inbox-page">
			<div className="flex items-center justify-between">
				<div>
					<h2 className="text-2xl font-bold tracking-tight text-white">
						Inbox
					</h2>
					<p className="text-slate-400">
						{emails.length} message{emails.length !== 1 ? "s" : ""} in {folder}{" "}
						via <span className="text-blue-400">{selectedService}</span>
					</p>
				</div>
				<div className="flex gap-2 items-center">
					<Button
						variant="ghost"
						size="sm"
						className={`text-xs ${autoRefresh ? "text-emerald-400" : "text-slate-500"} hover:text-emerald-300`}
						onClick={() => setAutoRefresh((r) => !r)}
						title="Toggle auto-refresh (30s)"
					>
						<Clock
							className={`h-3.5 w-3.5 mr-1 ${autoRefresh ? "text-emerald-400" : "text-slate-600"}`}
						/>
						{autoRefresh ? "Auto" : "Manual"}
					</Button>
					<Button
						variant="outline"
						size="sm"
						className="border-slate-700 text-slate-300 hover:bg-slate-800"
						onClick={() => setShowFilters((f) => !f)}
					>
						<Filter className="h-4 w-4 mr-1" />
						Filter
					</Button>
					<Button
						size="sm"
						className="bg-blue-600 hover:bg-blue-700"
						onClick={fetchEmails}
						disabled={loading}
					>
						<RefreshCw
							className={`h-4 w-4 mr-1 ${loading ? "animate-spin" : ""}`}
						/>
						Refresh
					</Button>
				</div>
			</div>

			{/* Controls */}
			<Card className="border-slate-800 bg-slate-950/50">
				<CardContent className="pt-4 pb-3">
					<div className="flex flex-wrap gap-3 items-center">
						<div className="flex items-center gap-2">
							<label htmlFor="inbox-service" className="text-xs text-slate-400">
								Service
							</label>
							<select
								id="inbox-service"
								className="bg-slate-900 border border-slate-700 text-white text-sm rounded px-2 py-1"
								value={selectedService}
								onChange={(e) => setSelectedService(e.target.value)}
							>
								<option value="default">default</option>
								{services.map((s) => (
									<option key={s.name} value={s.name}>
										{s.name} ({s.type})
									</option>
								))}
							</select>
						</div>
						<div className="flex items-center gap-2">
							<label htmlFor="inbox-folder" className="text-xs text-slate-400">
								Folder
							</label>
							<select
								id="inbox-folder"
								className="bg-slate-900 border border-slate-700 text-white text-sm rounded px-2 py-1"
								value={folder}
								onChange={(e) => setFolder(e.target.value)}
							>
								{folders.length > 0
									? folders.map((f) => <option key={f}>{f}</option>)
									: ["INBOX", "Sent", "Drafts", "Trash", "Spam"].map((f) => (
											<option key={f}>{f}</option>
										))}
							</select>
						</div>
						<div className="flex items-center gap-2">
							<label htmlFor="inbox-limit" className="text-xs text-slate-400">
								Limit
							</label>
							<select
								id="inbox-limit"
								className="bg-slate-900 border border-slate-700 text-white text-sm rounded px-2 py-1"
								value={limit}
								onChange={(e) => setLimit(Number(e.target.value))}
							>
								{[10, 20, 50, 100].map((n) => (
									<option key={n}>{n}</option>
								))}
							</select>
						</div>
						<label className="flex items-center gap-1 text-xs text-slate-400 cursor-pointer">
							<input
								type="checkbox"
								checked={unreadOnly}
								onChange={(e) => setUnreadOnly(e.target.checked)}
								className="accent-blue-500"
							/>
							Unread only
						</label>
					</div>

					{showFilters && (
						<div className="flex flex-wrap gap-3 mt-3 pt-3 border-t border-slate-800">
							<Input
								className="bg-slate-900 border-slate-700 text-white text-sm w-52"
								data-testid="filter-sender"
								placeholder="Filter by sender..."
								value={fromFilter}
								onChange={(e) => setFromFilter(e.target.value)}
								onKeyDown={(e) => e.key === "Enter" && fetchEmails()}
							/>
							<Input
								className="bg-slate-900 border-slate-700 text-white text-sm w-52"
								data-testid="filter-subject"
								placeholder="Filter by subject..."
								value={subjectFilter}
								onChange={(e) => setSubjectFilter(e.target.value)}
								onKeyDown={(e) => e.key === "Enter" && fetchEmails()}
							/>
							<Button
								size="sm"
								className="bg-blue-600 hover:bg-blue-700"
								data-testid="apply-filters"
								onClick={fetchEmails}
							>
								Apply
							</Button>
						</div>
					)}
				</CardContent>
			</Card>

			{/* Email list */}
			<Card className="border-slate-800 bg-slate-950/50">
				<CardHeader className="pb-2 flex flex-row items-center justify-between">
					<CardTitle className="text-white text-base">
						<InboxIcon className="inline h-4 w-4 mr-2 text-emerald-400" />
						{folder}
					</CardTitle>
					<Button
						variant="ghost"
						size="sm"
						className="text-slate-400 hover:text-white text-xs"
						onClick={() =>
							navigate(`/search?service=${selectedService}&folder=${folder}`)
						}
					>
						<Search className="h-3.5 w-3.5 mr-1" />
						Search
					</Button>
				</CardHeader>
				<CardContent>
					{loading && emails.length === 0 && (
						<div className="flex items-center gap-2 text-slate-500 py-8 justify-center">
							<Loader2 className="h-5 w-5 animate-spin" />
							<span>Fetching mail...</span>
						</div>
					)}
					{error && (
						<div className="flex items-center gap-2 text-red-400 py-4">
							<AlertCircle className="h-4 w-4" />
							<span className="text-sm">{error}</span>
						</div>
					)}
					{!loading && !error && emails.length === 0 && (
						<p className="text-slate-500 text-sm italic py-8 text-center">
							No messages found.
						</p>
					)}
					{emails.map((email, i) => (
						// biome-ignore lint/a11y/noStaticElementInteractions: list row with inner delete button - nesting buttons is invalid HTML
						// biome-ignore lint/a11y/useKeyWithClickEvents: row opens email via onClick; inner button handles its own key
						<div
							key={email.id || i}
							className="group flex items-start gap-3 py-3 border-b border-slate-800 last:border-0 hover:bg-slate-900/30 px-2 rounded transition-colors cursor-pointer"
							onClick={() => handleOpenEmail(email)}
						>
							<div className="mt-0.5 p-1.5 bg-slate-900 rounded shrink-0">
								<Mail
									className={`h-3.5 w-3.5 ${email.read ? "text-slate-500" : "text-blue-400"}`}
								/>
							</div>
							<div className="flex-1 min-w-0">
								<p
									className={`text-sm truncate ${email.read ? "text-slate-300" : "text-white font-medium"}`}
								>
									{email.subject || "(No Subject)"}
								</p>
								<p className="text-xs text-slate-500 truncate">
									{email.from} &nbsp;·&nbsp; {email.date}
								</p>
							</div>
							<Button
								variant="ghost"
								size="icon"
								className="h-7 w-7 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity text-slate-500 hover:text-red-400 hover:bg-red-950/20"
								onClick={(e) => handleDelete(e, email.id)}
								disabled={deletingIds.has(email.id)}
								title="Delete"
							>
								<Trash2 className="h-3.5 w-3.5" />
							</Button>
						</div>
					))}
				</CardContent>
			</Card>
		</div>
	);
}
