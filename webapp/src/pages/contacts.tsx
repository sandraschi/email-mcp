import {
	BookOpen,
	Download,
	Loader2,
	Mail,
	Plus,
	Search,
	Trash2,
	Upload,
	User,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useToast } from "@/components/toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { fetchWithAuth } from "@/lib/api";

type Contact = {
	id: string;
	name: string;
	email: string;
	phone: string;
	notes: string;
	group: string;
};

export function Contacts() {
	const { toast } = useToast();
	const [contacts, setContacts] = useState<Contact[]>([]);
	const [loading, setLoading] = useState(true);
	const [search, setSearch] = useState("");
	const [showAdd, setShowAdd] = useState(false);
	const [showImport, setShowImport] = useState(false);
	const [newName, setNewName] = useState("");
	const [newEmail, setNewEmail] = useState("");
	const [newPhone, setNewPhone] = useState("");
	const [newNotes, setNewNotes] = useState("");
	const [newGroup, setNewGroup] = useState("");
	const [importText, setImportText] = useState("");
	const [importFormat, setImportFormat] = useState("csv");
	const [saving, setSaving] = useState(false);
	const [importing, setImporting] = useState(false);
	const [googleToken, setGoogleToken] = useState("");
	const [googleImporting, setGoogleImporting] = useState(false);
	const [msftToken, setMsftToken] = useState("");
	const [msftImporting, setMsftImporting] = useState(false);
	const [curatedLists, setCuratedLists] = useState<any[]>([]);
	const [importingCurated, setImportingCurated] = useState<string | null>(null);
	const [deleting, setDeleting] = useState<string | null>(null);

	const loadContacts = useCallback(async () => {
		setLoading(true);
		try {
			const params = search.trim() ? `?q=${encodeURIComponent(search)}` : "";
			const data = await fetchWithAuth(`/api/contacts${params}`);
			setContacts(data.contacts || []);
		} catch {
			/* ignore */
		} finally {
			setLoading(false);
		}
	}, [search]);

	useEffect(() => {
		loadContacts();
	}, [loadContacts]);

	useEffect(() => {
		fetchWithAuth("/api/curated-lists")
			.then((d) => setCuratedLists(d.lists || []))
			.catch(() => {});
	}, []);

	const handleImportCurated = async (listId: string) => {
		setImportingCurated(listId);
		try {
			const data = await fetchWithAuth(`/api/curated-lists/${listId}/import`, {
				method: "POST",
			});
			if (data.success) {
				toast(
					"success",
					`Imported ${data.imported} contact(s) from ${data.list_title}`,
				);
				loadContacts();
			} else {
				toast("error", data.error || "Import failed");
			}
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "Import failed");
		} finally {
			setImportingCurated(null);
		}
	};

	const handleAdd = async () => {
		if (!newEmail.trim()) {
			toast("error", "Email is required");
			return;
		}
		setSaving(true);
		try {
			const data = await fetchWithAuth("/api/contacts", {
				method: "POST",
				body: JSON.stringify({
					name: newName,
					email: newEmail,
					phone: newPhone,
					notes: newNotes,
					group: newGroup,
				}),
			});
			if (data.success) {
				toast("success", `Added ${data.contact.name || data.contact.email}`);
				setNewName("");
				setNewEmail("");
				setNewPhone("");
				setNewNotes("");
				setNewGroup("");
				setShowAdd(false);
				loadContacts();
			} else {
				toast("error", data.error || "Add failed");
			}
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "Add failed");
		} finally {
			setSaving(false);
		}
	};

	const handleDelete = async (id: string) => {
		setDeleting(id);
		try {
			await fetchWithAuth(`/api/contacts/${id}`, { method: "DELETE" });
			toast("success", "Contact deleted");
			loadContacts();
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "Delete failed");
		} finally {
			setDeleting(null);
		}
	};

	const handleImport = async () => {
		if (!importText.trim()) {
			toast("error", "Paste contacts data first");
			return;
		}
		setImporting(true);
		try {
			const data = await fetchWithAuth("/api/contacts/import", {
				method: "POST",
				body: JSON.stringify({ format: importFormat, text: importText }),
			});
			if (data.success) {
				toast("success", `Imported ${data.imported} contact(s)`);
				if (data.errors?.length)
					toast("error", `${data.errors.length} error(s): ${data.errors[0]}`);
				setShowImport(false);
				setImportText("");
				loadContacts();
			} else {
				toast("error", data.error || "Import failed");
			}
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "Import failed");
		} finally {
			setImporting(false);
		}
	};

	const handleImportGoogle = async () => {
		if (!googleToken.trim()) {
			toast("error", "Enter a Google OAuth token");
			return;
		}
		setGoogleImporting(true);
		try {
			const data = await fetchWithAuth("/api/contacts/import-google", {
				method: "POST",
				body: JSON.stringify({ token: googleToken.trim() }),
			});
			if (data.success) {
				toast("success", `Imported ${data.imported} contact(s) from Google`);
				if (data.errors?.length)
					toast("error", `${data.errors.length} error(s): ${data.errors[0]}`);
				loadContacts();
			} else {
				toast("error", data.errors?.[0] || "Import failed");
			}
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "Import failed");
		} finally {
			setGoogleImporting(false);
		}
	};

	const handleImportMicrosoft = async () => {
		if (!msftToken.trim()) {
			toast("error", "Enter a Microsoft Graph token");
			return;
		}
		setMsftImporting(true);
		try {
			const data = await fetchWithAuth("/api/contacts/import-microsoft", {
				method: "POST",
				body: JSON.stringify({ token: msftToken.trim() }),
			});
			if (data.success) {
				toast("success", `Imported ${data.imported} contact(s) from Microsoft`);
				if (data.errors?.length)
					toast("error", `${data.errors.length} error(s): ${data.errors[0]}`);
				loadContacts();
			} else {
				toast("error", data.errors?.[0] || "Import failed");
			}
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "Import failed");
		} finally {
			setMsftImporting(false);
		}
	};

	const groups = [...new Set(contacts.map((c) => c.group).filter(Boolean))];

	return (
		<div className="space-y-6">
			<div className="flex items-center justify-between">
				<div>
					<h2 className="text-2xl font-bold tracking-tight text-white">
						Contacts
					</h2>
					<p className="text-slate-400">
						{contacts.length} contact{contacts.length !== 1 ? "s" : ""}
					</p>
				</div>
				<div className="flex gap-2">
					<Button
						variant="outline"
						size="sm"
						className="border-slate-700 text-slate-300 hover:bg-slate-800"
						onClick={() => setShowImport(!showImport)}
					>
						<Upload className="h-4 w-4 mr-1" /> Import
					</Button>
					<Button
						size="sm"
						className="bg-blue-600 hover:bg-blue-700"
						onClick={() => setShowAdd(!showAdd)}
					>
						<Plus className="h-4 w-4 mr-1" /> Add
					</Button>
				</div>
			</div>

			{showAdd && (
				<Card className="border-blue-800 bg-blue-950/20">
					<CardHeader>
						<CardTitle className="text-white text-sm">Add Contact</CardTitle>
					</CardHeader>
					<CardContent className="space-y-3">
						<div className="grid gap-3 md:grid-cols-2">
							<div>
								<Label className="text-slate-300">Name</Label>
								<Input
									className="bg-slate-900 border-slate-700 text-white mt-1"
									value={newName}
									onChange={(e) => setNewName(e.target.value)}
								/>
							</div>
							<div>
								<Label className="text-slate-300">Email *</Label>
								<Input
									className="bg-slate-900 border-slate-700 text-white mt-1"
									value={newEmail}
									onChange={(e) => setNewEmail(e.target.value)}
								/>
							</div>
							<div>
								<Label className="text-slate-300">Phone</Label>
								<Input
									className="bg-slate-900 border-slate-700 text-white mt-1"
									value={newPhone}
									onChange={(e) => setNewPhone(e.target.value)}
								/>
							</div>
							<div>
								<Label className="text-slate-300">Group</Label>
								<Input
									className="bg-slate-900 border-slate-700 text-white mt-1"
									value={newGroup}
									onChange={(e) => setNewGroup(e.target.value)}
									placeholder="e.g. Friends, Work"
								/>
							</div>
						</div>
						<div>
							<Label className="text-slate-300">Notes</Label>
							<Input
								className="bg-slate-900 border-slate-700 text-white mt-1"
								value={newNotes}
								onChange={(e) => setNewNotes(e.target.value)}
							/>
						</div>
						<div className="flex gap-2">
							<Button
								size="sm"
								className="bg-blue-600 hover:bg-blue-700"
								onClick={handleAdd}
								disabled={saving || !newEmail.trim()}
							>
								{saving && <Loader2 className="h-3 w-3 mr-1 animate-spin" />}{" "}
								Add
							</Button>
							<Button
								size="sm"
								variant="outline"
								className="border-slate-700 text-slate-300"
								onClick={() => setShowAdd(false)}
							>
								Cancel
							</Button>
						</div>
					</CardContent>
				</Card>
			)}

			{showImport && (
				<Card className="border-purple-800 bg-purple-950/20">
					<CardHeader className="pb-2">
						<CardTitle className="text-white text-sm flex items-center gap-2">
							<Upload className="h-4 w-4 text-purple-400" /> Import Contacts
						</CardTitle>
					</CardHeader>
					<CardContent className="space-y-4">
						<div className="space-y-2">
							<div className="flex gap-2">
								<Button
									size="sm"
									variant={importFormat === "csv" ? "default" : "outline"}
									className={
										importFormat === "csv"
											? "bg-blue-600"
											: "border-slate-700 text-slate-300"
									}
									onClick={() => setImportFormat("csv")}
								>
									CSV
								</Button>
								<Button
									size="sm"
									variant={importFormat === "vcard" ? "default" : "outline"}
									className={
										importFormat === "vcard"
											? "bg-blue-600"
											: "border-slate-700 text-slate-300"
									}
									onClick={() => setImportFormat("vcard")}
								>
									vCard (.vcf)
								</Button>
							</div>
							<textarea
								className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-sm text-white resize-y min-h-[80px] font-mono"
								placeholder={
									importFormat === "csv"
										? "name,email,phone,notes,group\nJohn,john@test.com,555-0100,,Friends"
										: "BEGIN:VCARD\nFN:John\nEMAIL:john@test.com\nEND:VCARD"
								}
								value={importText}
								onChange={(e) => setImportText(e.target.value)}
							/>
							<Button
								size="sm"
								className="bg-purple-600 hover:bg-purple-700"
								onClick={handleImport}
								disabled={importing || !importText.trim()}
							>
								{importing ? (
									<Loader2 className="h-3 w-3 mr-1 animate-spin" />
								) : (
									<Upload className="h-3 w-3 mr-1" />
								)}{" "}
								Import
							</Button>
						</div>
						<div className="h-px bg-slate-800" />
						<div className="space-y-2">
							<p className="text-xs text-slate-400 flex items-center gap-1">
								<Mail className="h-3 w-3" /> Google Contacts
							</p>
							<Input
								className="bg-slate-900 border-slate-700 text-white text-sm font-mono"
								placeholder="Google OAuth token (needs contacts.readonly scope)"
								value={googleToken}
								onChange={(e) => setGoogleToken(e.target.value)}
							/>
							<div className="flex gap-2 items-center">
								<Button
									size="sm"
									className="bg-red-600 hover:bg-red-700 text-xs"
									onClick={handleImportGoogle}
									disabled={googleImporting || !googleToken.trim()}
								>
									{googleImporting ? (
										<Loader2 className="h-3 w-3 mr-1 animate-spin" />
									) : (
										<Download className="h-3 w-3 mr-1" />
									)}{" "}
									Fetch from Google
								</Button>
								<a
									className="text-xs text-blue-400 hover:underline"
									href="https://developers.google.com/oauthplayground"
									target="_blank"
									rel="noopener"
								>
									Get token →
								</a>
							</div>
						</div>
						<div className="h-px bg-slate-800" />
						<div className="space-y-2">
							<p className="text-xs text-slate-400 flex items-center gap-1">
								<Mail className="h-3 w-3" /> Office 365 / Outlook
							</p>
							<Input
								className="bg-slate-900 border-slate-700 text-white text-sm font-mono"
								placeholder="Microsoft Graph token (needs Contacts.Read scope)"
								value={msftToken}
								onChange={(e) => setMsftToken(e.target.value)}
							/>
							<div className="flex gap-2 items-center">
								<Button
									size="sm"
									className="bg-blue-600 hover:bg-blue-700 text-xs"
									onClick={handleImportMicrosoft}
									disabled={msftImporting || !msftToken.trim()}
								>
									{msftImporting ? (
										<Loader2 className="h-3 w-3 mr-1 animate-spin" />
									) : (
										<Download className="h-3 w-3 mr-1" />
									)}{" "}
									Fetch from Microsoft
								</Button>
								<a
									className="text-xs text-blue-400 hover:underline"
									href="https://developer.microsoft.com/en-us/graph/graph-explorer"
									target="_blank"
									rel="noopener"
								>
									Get token →
								</a>
							</div>
						</div>
					</CardContent>
				</Card>
			)}

			{/* Curated Public Lists */}
			<details className="group">
				<summary className="text-sm text-slate-400 cursor-pointer hover:text-slate-200 list-none flex items-center gap-1">
					<BookOpen className="h-4 w-4" /> Curated Public Lists{" "}
					<span className="text-xs text-slate-600 group-open:rotate-180 transition-transform">
						▼
					</span>
				</summary>
				<div className="mt-3 space-y-2">
					{curatedLists.length === 0 ? (
						<div className="flex justify-center py-4">
							<Loader2 className="h-5 w-5 animate-spin text-blue-500" />
						</div>
					) : (
						curatedLists.map((lst) => (
							<div
								key={lst.id}
								className="flex items-center gap-3 py-2 px-3 rounded bg-slate-950/50 border border-slate-800"
							>
								<BookOpen className="h-4 w-4 text-slate-500 shrink-0" />
								<div className="flex-1 min-w-0">
									<p className="text-sm text-white truncate">{lst.title}</p>
									<p className="text-xs text-slate-500 truncate">
										{lst.count} contacts — {lst.description}
									</p>
								</div>
								<Button
									size="sm"
									variant="outline"
									className="border-slate-700 text-slate-300 hover:bg-slate-800 h-7 text-xs"
									onClick={() => handleImportCurated(lst.id)}
									disabled={importingCurated === lst.id}
								>
									{importingCurated === lst.id ? (
										<Loader2 className="h-3 w-3 mr-1 animate-spin" />
									) : (
										<Download className="h-3 w-3 mr-1" />
									)}
									Import
								</Button>
							</div>
						))
					)}
					<p className="text-xs text-amber-500">
						These are publicly available addresses for civic engagement. Using
						them for spam is illegal and unethical.
					</p>
				</div>
			</details>

			{/* Search */}
			<div className="relative">
				<Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
				<input
					className="w-full bg-slate-900 border border-slate-700 rounded-md pl-9 pr-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
					placeholder="Search contacts..."
					value={search}
					onChange={(e) => setSearch(e.target.value)}
				/>
			</div>

			{/* Groups */}
			{groups.length > 0 && (
				<div className="flex gap-2 flex-wrap">
					<button
						className="text-xs px-2.5 py-1 rounded-md border border-slate-700 text-slate-300 hover:bg-slate-800"
						onClick={() => setSearch("")}
					>
						All
					</button>
					{groups.map((g) => (
						<button
							key={g}
							className="text-xs px-2.5 py-1 rounded-md border border-slate-700 text-slate-300 hover:bg-slate-800"
							onClick={() => setSearch(g)}
						>
							{g}
						</button>
					))}
				</div>
			)}

			{loading ? (
				<div className="flex justify-center py-12">
					<Loader2 className="h-8 w-8 animate-spin text-blue-500" />
				</div>
			) : contacts.length === 0 ? (
				<p className="text-slate-500 text-center py-12 text-sm italic">
					No contacts yet. Add one or import from CSV/vCard.
				</p>
			) : (
				<div className="space-y-2">
					{contacts.map((c) => (
						<div
							key={c.id}
							className="flex items-center gap-3 py-2.5 px-3 rounded bg-slate-950/50 border border-slate-800 hover:bg-slate-900/30 transition-colors"
						>
							<div className="p-2 bg-slate-900 rounded-full">
								<User className="h-4 w-4 text-blue-400" />
							</div>
							<div className="flex-1 min-w-0">
								<p className="text-sm text-white truncate">
									{c.name || "(no name)"}
								</p>
								<p className="text-xs text-slate-500 truncate">
									{c.email}
									{c.phone ? ` · ${c.phone}` : ""}
									{c.group ? ` · [${c.group}]` : ""}
								</p>
							</div>
							<Button
								variant="ghost"
								size="icon"
								className="h-7 w-7 text-slate-500 hover:text-red-400"
								onClick={() => handleDelete(c.id)}
								disabled={deleting === c.id}
							>
								<Trash2 className="h-3.5 w-3.5" />
							</Button>
						</div>
					))}
				</div>
			)}
		</div>
	);
}
