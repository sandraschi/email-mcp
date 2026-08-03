import {
	AlertCircle,
	ArrowLeft,
	Copy,
	FolderInput,
	Forward,
	Loader2,
	MailCheck,
	Reply,
	Send,
	Trash2,
	X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { SanitizedHtml } from "@/components/sanitized-html";
import { useToast } from "@/components/toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { fetchWithAuth } from "@/lib/api";

type EmailDetail = {
	id: string;
	subject: string;
	from: string;
	to: string;
	cc: string;
	date: string;
	text_body: string;
	html_body: string | null;
};

type FolderOption = { name: string; depth: number };

export function EmailDetail() {
	const [searchParams] = useSearchParams();
	const navigate = useNavigate();
	const { toast } = useToast();

	const emailId = searchParams.get("id") || "";
	const service = searchParams.get("service") || "default";
	const folder = searchParams.get("folder") || "INBOX";

	const [email, setEmail] = useState<EmailDetail | null>(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [deleting, setDeleting] = useState(false);
	const [folders, setFolders] = useState<FolderOption[]>([]);
	const [moveCopyMode, setMoveCopyMode] = useState<"move" | "copy" | null>(
		null,
	);
	const [targetFolder, setTargetFolder] = useState("");
	const [showForward, setShowForward] = useState(false);
	const [forwardTo, setForwardTo] = useState("");
	const [forwardComment, setForwardComment] = useState("");
	const [busy, setBusy] = useState(false);

	useEffect(() => {
		if (!emailId) {
			setError("No email ID provided");
			setLoading(false);
			return;
		}
		fetchWithAuth(
			`/api/inbox/${encodeURIComponent(emailId)}?service=${service}&folder=${folder}`,
		)
			.then((data) => {
				if (data.success) {
					setEmail(data);
				} else {
					setError(data.error || "Failed to load email");
				}
			})
			.catch((err) => setError(err.message))
			.finally(() => setLoading(false));
	}, [emailId, service, folder]);

	// Folder options for Move/Copy picker
	// biome-ignore lint/correctness/useExhaustiveDependencies: folder picker loads once per service
	useEffect(() => {
		fetchWithAuth(`/api/services/${encodeURIComponent(service)}/folders`)
			.then((data) => {
				const walk = (
					nodes: { name: string; children?: unknown[] }[],
					depth: number,
				): FolderOption[] =>
					(nodes || []).flatMap((n) => [
						{ name: n.name, depth },
						...(n.children ? walk(n.children as never, depth + 1) : []),
					]);
				const flat = walk((data.folders || []) as never, 0);
				if (flat.length > 0) {
					setFolders(flat);
					if (!targetFolder && folder !== "INBOX") setTargetFolder(folder);
				}
			})
			.catch(() => {});
	}, [service]);

	const handleDelete = async () => {
		if (!emailId || !window.confirm("Delete this email?")) return;
		setDeleting(true);
		try {
			await fetchWithAuth(
				`/api/inbox/${encodeURIComponent(emailId)}?service=${service}&folder=${folder}`,
				{ method: "DELETE" },
			);
			toast("success", "Email deleted");
			navigate(-1);
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "Delete failed");
		} finally {
			setDeleting(false);
		}
	};

	const handleMarkRead = async () => {
		if (!emailId) return;
		try {
			await fetchWithAuth(
				`/api/inbox/${encodeURIComponent(emailId)}/mark-read`,
				{
					method: "POST",
					body: JSON.stringify({ service, folder }),
				},
			);
			toast("success", "Marked as read");
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "Failed");
		}
	};

	const handleMoveCopy = async () => {
		if (!emailId || !moveCopyMode || !targetFolder) return;
		setBusy(true);
		try {
			await fetchWithAuth(
				`/api/inbox/${encodeURIComponent(emailId)}/${moveCopyMode}`,
				{
					method: "POST",
					body: JSON.stringify({ service, folder, to_folder: targetFolder }),
				},
			);
			toast(
				"success",
				moveCopyMode === "move" ? "Email moved" : "Email copied",
			);
			if (moveCopyMode === "move") navigate(-1);
			else setMoveCopyMode(null);
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "Operation failed");
		} finally {
			setBusy(false);
		}
	};

	const handleForward = async () => {
		if (!emailId || !forwardTo.trim()) {
			toast("error", "Recipient is required");
			return;
		}
		setBusy(true);
		try {
			await fetchWithAuth(`/api/inbox/${encodeURIComponent(emailId)}/forward`, {
				method: "POST",
				body: JSON.stringify({
					service,
					folder,
					to: forwardTo.trim(),
					comment: forwardComment.trim(),
				}),
			});
			toast("success", "Email forwarded");
			setShowForward(false);
			setForwardTo("");
			setForwardComment("");
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "Forward failed");
		} finally {
			setBusy(false);
		}
	};

	const handleReply = () => {
		if (!email) return;
		const to = email.from.replace(/.*<(.+)>.*/, "$1") || email.from;
		const re = `Re: ${email.subject}`;
		navigate(
			`/compose?to=${encodeURIComponent(to)}&subject=${encodeURIComponent(re)}`,
		);
	};

	if (loading) {
		return (
			<div className="flex items-center justify-center h-64">
				<Loader2 className="h-8 w-8 animate-spin text-blue-500" />
			</div>
		);
	}

	if (error || !email) {
		return (
			<div className="flex items-center gap-2 text-red-400 p-4">
				<AlertCircle className="h-5 w-5" />
				<span>{error || "Email not found"}</span>
				<Button
					variant="outline"
					size="sm"
					className="ml-4 border-slate-700"
					onClick={() => navigate(-1)}
				>
					<ArrowLeft className="h-4 w-4 mr-1" /> Back
				</Button>
			</div>
		);
	}

	const _displayBody = email.html_body || email.text_body || "";

	return (
		<div className="space-y-4" data-testid="email-detail-page">
			<div className="flex items-center justify-between">
				<Button
					variant="outline"
					size="sm"
					data-testid="email-detail-back"
					className="border-slate-700 text-slate-300 hover:bg-slate-800"
					onClick={() => navigate(-1)}
				>
					<ArrowLeft className="h-4 w-4 mr-1" /> Back to Inbox
				</Button>
				<div className="flex gap-2 flex-wrap">
					<Button
						variant="outline"
						size="sm"
						className="border-slate-700 text-slate-300 hover:bg-slate-800"
						onClick={handleMarkRead}
					>
						<MailCheck className="h-4 w-4 mr-1" /> Mark Read
					</Button>
					<Button
						variant="outline"
						size="sm"
						data-testid="email-detail-reply"
						className="border-slate-700 text-slate-300 hover:bg-slate-800"
						onClick={handleReply}
					>
						<Reply className="h-4 w-4 mr-1" /> Reply
					</Button>
					<Button
						variant="outline"
						size="sm"
						data-testid="email-detail-forward"
						className="border-slate-700 text-slate-300 hover:bg-slate-800"
						onClick={() => setShowForward((s) => !s)}
					>
						<Forward className="h-4 w-4 mr-1" /> Forward
					</Button>
					<Button
						variant="outline"
						size="sm"
						data-testid="email-detail-move"
						className="border-slate-700 text-slate-300 hover:bg-slate-800"
						onClick={() =>
							setMoveCopyMode((m) => (m === "move" ? null : "move"))
						}
					>
						<FolderInput className="h-4 w-4 mr-1" /> Move
					</Button>
					<Button
						variant="outline"
						size="sm"
						data-testid="email-detail-copy"
						className="border-slate-700 text-slate-300 hover:bg-slate-800"
						onClick={() =>
							setMoveCopyMode((m) => (m === "copy" ? null : "copy"))
						}
					>
						<Copy className="h-4 w-4 mr-1" /> Copy
					</Button>
					<Button
						variant="outline"
						size="sm"
						className="border-red-800 text-red-400 hover:bg-red-950/30"
						onClick={handleDelete}
						disabled={deleting}
					>
						<Trash2 className="h-4 w-4 mr-1" /> Delete
					</Button>
				</div>
			</div>

			{moveCopyMode && (
				<Card className="border-slate-700 bg-slate-900/60">
					<CardContent className="pt-4 pb-3 flex flex-wrap items-center gap-3">
						<span className="text-sm text-slate-300 capitalize">
							{moveCopyMode} to:
						</span>
						<select
							data-testid="movecopy-folder"
							className="bg-slate-800 border border-slate-600 text-white text-sm rounded px-2 py-1.5 min-w-52"
							value={targetFolder}
							onChange={(e) => setTargetFolder(e.target.value)}
						>
							<option value="">Select folder...</option>
							{folders.map((f) => (
								<option key={f.name} value={f.name}>
									{"\u00A0".repeat(f.depth * 3)}
									{f.name}
								</option>
							))}
						</select>
						<Button
							size="sm"
							data-testid="movecopy-apply"
							className="bg-blue-600 hover:bg-blue-700"
							disabled={busy || !targetFolder}
							onClick={handleMoveCopy}
						>
							{moveCopyMode === "move" ? "Move" : "Copy"}
						</Button>
						<Button
							variant="ghost"
							size="sm"
							className="text-slate-400"
							onClick={() => setMoveCopyMode(null)}
						>
							<X className="h-4 w-4" />
						</Button>
					</CardContent>
				</Card>
			)}

			{showForward && (
				<Card
					className="border-slate-700 bg-slate-900/60"
					data-testid="forward-dialog"
				>
					<CardContent className="pt-4 pb-3 space-y-3">
						<div className="flex items-center gap-2">
							<Input
								data-testid="forward-to"
								placeholder="To (comma-separated)"
								className="bg-slate-800 border-slate-600 text-white"
								value={forwardTo}
								onChange={(e) => setForwardTo(e.target.value)}
							/>
							<Button
								variant="ghost"
								size="icon"
								className="text-slate-400 shrink-0"
								onClick={() => setShowForward(false)}
							>
								<X className="h-4 w-4" />
							</Button>
						</div>
						<textarea
							data-testid="forward-comment"
							placeholder="Add a comment (optional)"
							rows={3}
							className="w-full bg-slate-800 border border-slate-600 text-white text-sm rounded px-3 py-2 resize-none"
							value={forwardComment}
							onChange={(e) => setForwardComment(e.target.value)}
						/>
						<div className="flex justify-end">
							<Button
								size="sm"
								data-testid="forward-send"
								className="bg-blue-600 hover:bg-blue-700"
								disabled={busy || !forwardTo.trim()}
								onClick={handleForward}
							>
								<Send className="h-4 w-4 mr-1" />
								{busy ? "Sending..." : "Forward"}
							</Button>
						</div>
					</CardContent>
				</Card>
			)}

			<Card className="border-slate-800 bg-slate-950/50">
				<CardHeader className="pb-3">
					<CardTitle className="text-white text-lg">
						{email.subject || "(No Subject)"}
					</CardTitle>
					<div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-slate-400 mt-2">
						<div>
							<span className="text-slate-500">From:</span>{" "}
							<span className="text-slate-200">{email.from || "Unknown"}</span>
						</div>
						<div>
							<span className="text-slate-500">To:</span>{" "}
							<span className="text-slate-200">{email.to || "—"}</span>
						</div>
						{email.cc && (
							<div>
								<span className="text-slate-500">CC:</span>{" "}
								<span className="text-slate-200">{email.cc}</span>
							</div>
						)}
						<div>
							<span className="text-slate-500">Date:</span>{" "}
							<span className="text-slate-200">{email.date || "Unknown"}</span>
						</div>
					</div>
				</CardHeader>
				<CardContent>
					{email.html_body ? (
						<SanitizedHtml
							html={email.html_body}
							className="prose prose-invert prose-slate max-w-none text-sm text-slate-300 [&_a]:text-blue-400 [&_img]:max-w-full"
						/>
					) : (
						<pre className="text-sm text-slate-300 whitespace-pre-wrap font-sans">
							{email.text_body || "(No body)"}
						</pre>
					)}
				</CardContent>
			</Card>
		</div>
	);
}
