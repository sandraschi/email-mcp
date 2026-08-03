import {
	AlertCircle,
	Archive,
	ChevronDown,
	ChevronRight,
	Clock,
	FileText,
	Filter,
	Folder,
	FolderOpen,
	Inbox as InboxIcon,
	Loader2,
	Mail,
	Pencil,
	Plus,
	RefreshCw,
	Search,
	Send,
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

type FolderNode = {
	id?: string;
	name: string;
	unread?: number;
	total?: number;
	delimiter?: string;
	children?: FolderNode[];
};

const AUTO_REFRESH_MS = 30_000; // 30 seconds

function folderIcon(name: string, open: boolean) {
	const n = name.toLowerCase();
	if (/posteingang|inbox/i.test(n))
		return <InboxIcon className="h-4 w-4 text-emerald-400" />;
	if (/gesendete|sent/i.test(n))
		return <Send className="h-4 w-4 text-blue-400" />;
	if (/gel\u00f6schte|deleted|trash/i.test(n))
		return <Trash2 className="h-4 w-4 text-slate-400" />;
	if (/junk|spam/i.test(n))
		return <AlertCircle className="h-4 w-4 text-red-400" />;
	if (/entw\u00fcrfe|drafts/i.test(n))
		return <FileText className="h-4 w-4 text-amber-400" />;
	if (/archiv|archive/i.test(n))
		return <Archive className="h-4 w-4 text-slate-400" />;
	return open ? (
		<FolderOpen className="h-4 w-4 text-slate-400" />
	) : (
		<Folder className="h-4 w-4 text-slate-400" />
	);
}

/** Build a nested tree from either Graph nodes ({children}) or flat IMAP nodes ({name, delimiter}). */
function buildTree(nodes: FolderNode[]): FolderNode[] {
	if (nodes.some((n) => n.children)) {
		return nodes.map((n) => ({
			...n,
			children: n.children ? buildTree(n.children) : [],
		}));
	}
	const roots: FolderNode[] = [];
	const children = new Map<string, FolderNode[]>();
	for (const n of nodes) {
		const parts = (n.name || "").split("/");
		const node: FolderNode = { ...n, name: parts[parts.length - 1] };
		if (parts.length === 1) {
			roots.push(node);
		} else {
			const parent = parts.slice(0, -1).join("/");
			children.set(parent, [...(children.get(parent) || []), node]);
		}
	}
	const attach = (parentName: string): FolderNode[] =>
		(children.get(parentName) || []).map((c) => ({
			...c,
			children: attach(`${parentName}/${c.name}`),
		}));
	return [...roots.map((r) => ({ ...r, children: attach(r.name) }))].sort(
		(a, b) => a.name.toLowerCase().localeCompare(b.name.toLowerCase()),
	);
}

function FolderTree({
	nodes,
	depth,
	selected,
	expanded,
	onToggle,
	onSelect,
	onRename,
	onDelete,
}: {
	nodes: FolderNode[];
	depth: number;
	selected: string;
	expanded: Record<string, boolean>;
	onToggle: (name: string) => void;
	onSelect: (name: string) => void;
	onRename?: (name: string) => void;
	onDelete?: (name: string) => void;
}) {
	return (
		<>
			{nodes.map((n) => {
				const hasChildren = (n.children?.length ?? 0) > 0;
				const open = !!expanded[n.name];
				const isSelected = selected === n.name;
				return (
					<div key={n.id ?? n.name} data-testid="folder-node">
						{/* biome-ignore lint/a11y/useSemanticElements: row acts as selectable tree node with inner expand button - nesting buttons is invalid HTML */}
						<div
							role="button"
							tabIndex={0}
							aria-label={n.name}
							aria-expanded={hasChildren ? open : undefined}
							className={`flex items-center gap-1.5 w-full text-left rounded px-1.5 py-1 text-sm cursor-pointer select-none ${
								isSelected
									? "bg-blue-600/20 text-white"
									: "text-slate-300 hover:bg-slate-800/60"
							}`}
							style={{ paddingLeft: `${depth * 14 + 6}px` }}
							onClick={() => onSelect(n.name)}
							onKeyDown={(e) => {
								if (e.key === "Enter" || e.key === " ") {
									e.preventDefault();
									onSelect(n.name);
								}
							}}
						>
							{hasChildren ? (
								<button
									type="button"
									className="shrink-0 text-slate-500 hover:text-white p-0.5"
									title={open ? "Collapse" : "Expand"}
									onClick={(e) => {
										e.stopPropagation();
										onToggle(n.name);
									}}
								>
									{open ? (
										<ChevronDown className="h-3.5 w-3.5" />
									) : (
										<ChevronRight className="h-3.5 w-3.5" />
									)}
								</button>
							) : (
								<span className="w-[22px] shrink-0" />
							)}
							<span className="shrink-0">{folderIcon(n.name, open)}</span>
							<span className="flex-1 min-w-0 truncate">{n.name}</span>
							{(n.unread ?? 0) > 0 && (
								<span className="shrink-0 text-[10px] font-semibold text-amber-300 bg-amber-500/10 border border-amber-500/30 rounded-full px-1.5 py-0.5">
									{n.unread}
								</span>
							)}
							{isSelected && onRename && onDelete && (
								<span className="shrink-0 flex items-center gap-0.5 ml-1">
									<button
										type="button"
										title="Rename folder"
										data-testid="folder-rename"
										className="text-slate-500 hover:text-white p-0.5"
										onClick={(e) => {
											e.stopPropagation();
											onRename(n.name);
										}}
									>
										<Pencil className="h-3 w-3" />
									</button>
									<button
										type="button"
										title="Delete folder"
										data-testid="folder-delete"
										className="text-slate-500 hover:text-red-400 p-0.5"
										onClick={(e) => {
											e.stopPropagation();
											onDelete(n.name);
										}}
									>
										<Trash2 className="h-3 w-3" />
									</button>
								</span>
							)}
						</div>
						{hasChildren && open && (
							<FolderTree
								nodes={n.children ?? []}
								depth={depth + 1}
								selected={selected}
								expanded={expanded}
								onToggle={onToggle}
								onSelect={onSelect}
								onRename={onRename}
								onDelete={onDelete}
							/>
						)}
					</div>
				);
			})}
		</>
	);
}

export function Inbox() {
	const navigate = useNavigate();
	const { toast } = useToast();

	const [emails, setEmails] = useState<Email[]>([]);
	const [services, setServices] = useState<Service[]>([]);
	const [folderTree, setFolderTree] = useState<FolderNode[]>([]);
	const [expanded, setExpanded] = useState<Record<string, boolean>>({});
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
			const nodes: FolderNode[] = Array.isArray(data.folders)
				? data.folders
				: [];
			const tree = buildTree(nodes);
			setFolderTree(tree);
			// Auto-select the inbox node when the default "INBOX" isn't a real folder
			// (e.g. German mailbox: Posteingang) so counts/labels stay consistent.
			setFolder((current) => {
				if (current !== "INBOX") return current;
				const walk = (list: FolderNode[]): FolderNode | null => {
					for (const n of list) {
						if (/posteingang|inbox/i.test(n.name)) return n;
						const hit = n.children ? walk(n.children) : null;
						if (hit) return hit;
					}
					return null;
				};
				return walk(tree)?.name ?? current;
			});
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
			fetchFolders();
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

	const handleCreateFolder = async () => {
		const name = window.prompt("New folder name:");
		if (!name?.trim()) return;
		try {
			const res = await fetchWithAuth(
				`/api/services/${encodeURIComponent(selectedService)}/folders`,
				{ method: "POST", body: JSON.stringify({ folder: name.trim() }) },
			);
			if (res.success === false) {
				toast("error", res.error || "Create failed");
				return;
			}
			toast("success", `Folder "${name.trim()}" created`);
			fetchFolders();
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "Create failed");
		}
	};

	const handleRenameFolder = async (oldName: string) => {
		const newName = window.prompt(`Rename "${oldName}" to:`, oldName);
		if (!newName?.trim() || newName.trim() === oldName) return;
		try {
			const res = await fetchWithAuth(
				`/api/services/${encodeURIComponent(selectedService)}/folders/${encodeURIComponent(oldName)}`,
				{ method: "PUT", body: JSON.stringify({ new_name: newName.trim() }) },
			);
			if (res.success === false) {
				toast("error", res.error || "Rename failed");
				return;
			}
			toast("success", `Renamed to "${newName.trim()}"`);
			setFolder(newName.trim());
			fetchFolders();
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "Rename failed");
		}
	};

	const handleDeleteFolder = async (name: string) => {
		if (
			!window.confirm(
				`Delete folder "${name}"? Messages move to Deleted Items.`,
			)
		)
			return;
		try {
			const res = await fetchWithAuth(
				`/api/services/${encodeURIComponent(selectedService)}/folders/${encodeURIComponent(name)}`,
				{ method: "DELETE" },
			);
			if (res.success === false) {
				toast("error", res.error || "Delete failed");
				return;
			}
			toast("success", `Folder "${name}" deleted`);
			if (folder === name) setFolder("INBOX");
			fetchFolders();
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "Delete failed");
		}
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
						onClick={() => {
							fetchEmails();
							fetchFolders();
						}}
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

			<div className="grid gap-4 lg:grid-cols-[260px_1fr]">
				{/* Folder tree */}
				<Card
					className="border-slate-800 bg-slate-950/50 h-fit lg:sticky lg:top-4 max-h-[70vh] overflow-y-auto"
					data-testid="folder-tree"
				>
					<CardHeader className="pb-2 flex flex-row items-center justify-between">
						<CardTitle className="text-white text-sm flex items-center gap-2">
							<InboxIcon className="h-4 w-4 text-emerald-400" />
							Folders
						</CardTitle>
						<Button
							variant="ghost"
							size="icon"
							className="h-6 w-6 text-slate-400 hover:text-white"
							title="New folder"
							data-testid="folder-new"
							onClick={handleCreateFolder}
						>
							<Plus className="h-4 w-4" />
						</Button>
					</CardHeader>
					<CardContent className="pt-0 space-y-0.5">
						{folderTree.length === 0 ? (
							<p className="text-slate-500 text-xs italic px-2 py-3">
								No folders found.
							</p>
						) : (
							<FolderTree
								nodes={folderTree}
								depth={0}
								selected={folder}
								expanded={expanded}
								onToggle={(name) =>
									setExpanded((prev) => ({ ...prev, [name]: !prev[name] }))
								}
								onSelect={(name) => {
									setFolder(name);
									setExpanded((prev) => ({ ...prev, [name]: !prev[name] }));
								}}
								onRename={handleRenameFolder}
								onDelete={handleDeleteFolder}
							/>
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
		</div>
	);
}
