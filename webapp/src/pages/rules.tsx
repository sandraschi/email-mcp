import { Filter, GripVertical, Loader2, Plus, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useToast } from "@/components/toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { fetchWithAuth } from "@/lib/api";

type Rule = {
	id: string;
	name: string;
	match_field: string;
	match_pattern: string;
	filter_action: string;
	filter_target: string;
	enabled: boolean;
	service: string;
};

const ACTIONS = [
	{ value: "mark_read", label: "Mark as Read", color: "text-blue-400" },
	{ value: "star", label: "Star / Flag", color: "text-amber-400" },
	{ value: "move", label: "Move to Folder", color: "text-indigo-400" },
	{ value: "spam", label: "Flag as Spam", color: "text-red-400" },
	{ value: "delete", label: "Delete", color: "text-red-400" },
	{ value: "forward", label: "Forward to", color: "text-purple-400" },
	{ value: "notify", label: "Notify (log)", color: "text-emerald-400" },
];

export function Rules() {
	const { toast } = useToast();
	const [rules, setRules] = useState<Rule[]>([]);
	const [loading, setLoading] = useState(true);
	const [showAdd, setShowAdd] = useState(false);
	const [newRule, setNewRule] = useState({
		name: "",
		match_field: "subject",
		match_pattern: "",
		filter_action: "mark_read",
		filter_target: "",
		service: "default",
	});
	const [saving, setSaving] = useState(false);
	const [deleting, setDeleting] = useState<string | null>(null);

	const loadRules = useCallback(async () => {
		setLoading(true);
		try {
			const d = await fetchWithAuth("/api/auto-rules");
			setRules(d.rules || []);
		} catch {
			setRules([]);
		} finally {
			setLoading(false);
		}
	}, []);

	useEffect(() => {
		loadRules();
	}, [loadRules]);

	const handleAdd = async () => {
		if (!newRule.name.trim() || !newRule.match_pattern.trim()) {
			toast("error", "Name and pattern required");
			return;
		}
		setSaving(true);
		try {
			const data = await fetchWithAuth("/api/auto-rules", {
				method: "POST",
				body: JSON.stringify(newRule),
			});
			if (data.success) {
				toast("success", `Rule '${data.rule.name}' added`);
				setShowAdd(false);
				loadRules();
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
			await fetchWithAuth(`/api/auto-rules/${id}`, { method: "DELETE" });
			toast("success", "Rule deleted");
			loadRules();
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "Delete failed");
		} finally {
			setDeleting(null);
		}
	};

	const handleToggle = async (rule: Rule) => {
		try {
			await fetchWithAuth(`/api/auto-rules/${rule.id}`, {
				method: "PUT",
				body: JSON.stringify({ enabled: !rule.enabled }),
			});
			loadRules();
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "Toggle failed");
		}
	};

	return (
		<div className="space-y-6">
			<div className="flex items-center justify-between">
				<div>
					<h2 className="text-2xl font-bold tracking-tight text-white">
						Rules
					</h2>
					<p className="text-slate-400">
						Email processing rules — actions triggered on matching messages
					</p>
				</div>
				<Button
					size="sm"
					className="bg-blue-600 hover:bg-blue-700"
					onClick={() => setShowAdd(!showAdd)}
				>
					<Plus className="h-4 w-4 mr-1" /> {showAdd ? "Cancel" : "Add Rule"}
				</Button>
			</div>

			{showAdd && (
				<Card className="border-blue-800 bg-blue-950/20">
					<CardHeader>
						<CardTitle className="text-white text-sm">New Rule</CardTitle>
					</CardHeader>
					<CardContent className="space-y-3">
						<div className="grid gap-3 md:grid-cols-2">
							<div>
								<Label className="text-slate-300">Name</Label>
								<Input
									className="bg-slate-900 border-slate-700 text-white mt-1"
									placeholder="e.g. Auto-archive invoices"
									value={newRule.name}
									onChange={(e) =>
										setNewRule({ ...newRule, name: e.target.value })
									}
								/>
							</div>
							<div>
								<Label className="text-slate-300">Match Field</Label>
								<select
									className="bg-slate-900 border border-slate-700 text-white text-sm rounded px-3 py-2 w-full mt-1"
									value={newRule.match_field}
									onChange={(e) =>
										setNewRule({ ...newRule, match_field: e.target.value })
									}
								>
									<option value="subject">Subject</option>
									<option value="from">From (sender)</option>
									<option value="text_body">Body</option>
								</select>
							</div>
							<div>
								<Label className="text-slate-300">Match Pattern (regex)</Label>
								<Input
									className="bg-slate-900 border-slate-700 text-white mt-1"
									placeholder="invoice|receipt|order"
									value={newRule.match_pattern}
									onChange={(e) =>
										setNewRule({ ...newRule, match_pattern: e.target.value })
									}
								/>
							</div>
							<div>
								<Label className="text-slate-300">Action</Label>
								<select
									className="bg-slate-900 border border-slate-700 text-white text-sm rounded px-3 py-2 w-full mt-1"
									value={newRule.filter_action}
									onChange={(e) =>
										setNewRule({ ...newRule, filter_action: e.target.value })
									}
								>
									{ACTIONS.map((a) => (
										<option key={a.value} value={a.value}>
											{a.label}
										</option>
									))}
								</select>
							</div>
							{newRule.filter_action === "forward" && (
								<div className="md:col-span-2">
									<Label className="text-slate-300">Forward To</Label>
									<Input
										className="bg-slate-900 border-slate-700 text-white mt-1"
										placeholder="target@example.com"
										value={newRule.filter_target}
										onChange={(e) =>
											setNewRule({ ...newRule, filter_target: e.target.value })
										}
									/>
								</div>
							)}
							{newRule.filter_action === "move" && (
								<div className="md:col-span-2">
									<Label className="text-slate-300">Target Folder</Label>
									<Input
										className="bg-slate-900 border-slate-700 text-white mt-1"
										placeholder="Archive / Projects / Trash"
										value={newRule.filter_target}
										onChange={(e) =>
											setNewRule({ ...newRule, filter_target: e.target.value })
										}
									/>
								</div>
							)}
						</div>
						<div className="flex gap-2">
							<Button
								size="sm"
								className="bg-blue-600 hover:bg-blue-700"
								onClick={handleAdd}
								disabled={saving}
							>
								{saving ? (
									<Loader2 className="h-3 w-3 mr-1 animate-spin" />
								) : (
									<Plus className="h-3 w-3 mr-1" />
								)}{" "}
								Add Rule
							</Button>
						</div>
					</CardContent>
				</Card>
			)}

			{loading ? (
				<div className="flex justify-center py-12">
					<Loader2 className="h-8 w-8 animate-spin text-blue-500" />
				</div>
			) : rules.length === 0 ? (
				<div className="text-center py-12">
					<Filter className="h-12 w-12 text-slate-700 mx-auto mb-3" />
					<p className="text-slate-500 text-sm">
						No rules yet. Rules let you automatically process incoming emails.
					</p>
				</div>
			) : (
				<div className="space-y-1">
					{rules.map((rule, _i) => {
						const action = ACTIONS.find((a) => a.value === rule.filter_action);
						return (
							<div
								key={rule.id}
								className="flex items-center gap-3 py-2.5 px-3 rounded bg-slate-950/50 border border-slate-800 hover:border-slate-700 transition-colors"
							>
								<GripVertical className="h-4 w-4 text-slate-600 shrink-0 cursor-grab" />
								<div
									className={`h-2.5 w-2.5 rounded-full shrink-0 ${rule.enabled ? "bg-emerald-500" : "bg-slate-600"}`}
								/>
								<div className="flex-1 min-w-0">
									<div className="flex items-center gap-2">
										<p className="text-sm text-white font-medium">
											{rule.name}
										</p>
										{action && (
											<span className={`text-xs font-medium ${action.color}`}>
												{action.label}
											</span>
										)}
										{rule.filter_target && (
											<span className="text-xs text-slate-500">
												→ {rule.filter_target}
											</span>
										)}
									</div>
									<p className="text-xs text-slate-500 mt-0.5">
										<span className="font-mono text-blue-300">
											{rule.match_field}
										</span>
										<span className="text-slate-600"> ~/</span>
										<span className="text-emerald-300">
											{rule.match_pattern}
										</span>
										<span className="text-slate-600">/</span>
									</p>
								</div>
								<label className="relative inline-flex items-center cursor-pointer">
									<input
										type="checkbox"
										className="sr-only peer"
										checked={rule.enabled}
										onChange={() => handleToggle(rule)}
									/>
									<div className="w-8 h-4 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-emerald-600" />
								</label>
								<Button
									variant="ghost"
									size="icon"
									className="h-7 w-7 text-slate-500 hover:text-red-400"
									onClick={() => handleDelete(rule.id)}
									disabled={deleting === rule.id}
								>
									{deleting === rule.id ? (
										<Loader2 className="h-3.5 w-3.5 animate-spin" />
									) : (
										<Trash2 className="h-3.5 w-3.5" />
									)}
								</Button>
							</div>
						);
					})}
				</div>
			)}
		</div>
	);
}
