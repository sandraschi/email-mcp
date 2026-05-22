import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus, Trash2, Send, Loader2, CheckCircle2, AlertCircle, Bot, Sparkles, RefreshCw, X } from "lucide-react";
import { fetchWithAuth } from "@/lib/api";
import { useToast } from "@/components/toast";

type Rule = { id: string; name: string; match_field: string; match_pattern: string; reply_body: string; reply_subject: string; use_ai: boolean; auto_send: boolean; ai_prompt?: string; enabled: boolean; service: string };
type Pending = { id: string; email_subject: string; email_from: string; email_body: string; reply_body: string; reply_subject: string; status: string; service: string };

export function AutoRespond() {
    const { toast } = useToast();
    const [rules, setRules] = useState<Rule[]>([]);
    const [pending, setPending] = useState<Pending[]>([]);
    const [loading, setLoading] = useState(true);
    const [tab, setTab] = useState<"rules" | "pending">("rules");
    const [showAdd, setShowAdd] = useState(false);
    const [saving, setSaving] = useState(false);
    const [newRule, setNewRule] = useState({ name: "", match_field: "subject", match_pattern: "", reply_body: "", reply_subject: "", use_ai: false, auto_send: false, ai_prompt: "", service: "default" });

    const loadData = useCallback(async () => {
        setLoading(true);
        try {
            const [rData, pData] = await Promise.all([
                fetchWithAuth("/api/auto-rules"),
                fetchWithAuth("/api/auto-pending"),
            ]);
            setRules(rData.rules || []);
            setPending(pData.pending || []);
        } catch { /* ignore */ }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { loadData(); }, [loadData]);

    const handleAdd = async () => {
        if (!newRule.name.trim() || !newRule.match_pattern.trim()) { toast("error", "Name and pattern required"); return; }
        setSaving(true);
        try {
            const data = await fetchWithAuth("/api/auto-rules", { method: "POST", body: JSON.stringify(newRule) });
            if (data.success) {
                toast("success", `Rule '${data.rule.name}' added`);
                setShowAdd(false);
                setNewRule({ name: "", match_field: "subject", match_pattern: "", reply_body: "", reply_subject: "", use_ai: false, auto_send: false, ai_prompt: "", service: "default" });
                loadData();
            } else { toast("error", data.error || "Add failed"); }
        } catch (err: unknown) { toast("error", err instanceof Error ? err.message : "Add failed"); }
        finally { setSaving(false); }
    };

    const handleDelete = async (id: string) => {
        try {
            await fetchWithAuth(`/api/auto-rules/${id}`, { method: "DELETE" });
            toast("success", "Rule deleted");
            loadData();
        } catch (err: unknown) { toast("error", err instanceof Error ? err.message : "Delete failed"); }
    };

    const handleApprove = async (id: string) => {
        try {
            const data = await fetchWithAuth(`/api/auto-pending/${id}/approve`, { method: "POST" });
            if (data.success) {
                toast("success", data.send_message || "Approved and sent");
            } else {
                toast("error", data.error || "Approval failed");
            }
            loadData();
        } catch (err: unknown) { toast("error", err instanceof Error ? err.message : "Approve failed"); }
    };

    const handleReject = async (id: string) => {
        try {
            await fetchWithAuth(`/api/auto-pending/${id}/reject`, { method: "POST" });
            toast("success", "Rejected");
            loadData();
        } catch (err: unknown) { toast("error", err instanceof Error ? err.message : "Reject failed"); }
    };

    const pendingCount = pending.filter(p => p.status === "pending").length;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">Auto-Respond</h2>
                    <p className="text-slate-400">Rule-based and AI-powered email auto-reply</p>
                </div>
                <div className="flex items-center gap-2">
                    <Button size="sm" variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800" onClick={loadData}><RefreshCw className="h-4 w-4 mr-1" /> Refresh</Button>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 border-b border-slate-800 pb-2">
                <button className={`text-sm px-3 py-1.5 rounded-t ${tab === "rules" ? "text-white border-b-2 border-blue-500" : "text-slate-500 hover:text-slate-300"}`} onClick={() => setTab("rules")}>
                    Rules {rules.length > 0 && <span className="text-xs text-slate-500">({rules.length})</span>}
                </button>
                <button className={`text-sm px-3 py-1.5 rounded-t ${tab === "pending" ? "text-white border-b-2 border-amber-500" : "text-slate-500 hover:text-slate-300"}`} onClick={() => setTab("pending")}>
                    Pending {pendingCount > 0 && <span className="ml-1 px-1.5 py-0.5 text-xs bg-amber-600 rounded-full text-white">{pendingCount}</span>}
                </button>
            </div>

            {loading ? (
                <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-blue-500" /></div>
            ) : tab === "rules" ? (
                <>
                    <Button size="sm" className="bg-blue-600 hover:bg-blue-700" onClick={() => setShowAdd(!showAdd)}>
                        <Plus className="h-4 w-4 mr-1" /> {showAdd ? "Cancel" : "Add Rule"}
                    </Button>

                    {showAdd && (
                        <Card className="border-blue-800 bg-blue-950/20">
                            <CardHeader><CardTitle className="text-white text-sm">New Auto-Respond Rule</CardTitle></CardHeader>
                            <CardContent className="space-y-3">
                                <div className="grid gap-3 md:grid-cols-2">
                                    <div><Label className="text-slate-300">Rule Name</Label><Input className="bg-slate-900 border-slate-700 text-white mt-1" placeholder="e.g. Invoice reply" value={newRule.name} onChange={(e) => setNewRule({ ...newRule, name: e.target.value })} /></div>
                                    <div>
                                        <Label className="text-slate-300">Match Field</Label>
                                        <select className="bg-slate-900 border border-slate-700 text-white text-sm rounded px-3 py-2 w-full mt-1" value={newRule.match_field} onChange={(e) => setNewRule({ ...newRule, match_field: e.target.value })}>
                                            <option value="subject">Subject</option>
                                            <option value="from">From (sender)</option>
                                            <option value="text_body">Body</option>
                                        </select>
                                    </div>
                                    <div><Label className="text-slate-300">Match Pattern (regex)</Label><Input className="bg-slate-900 border-slate-700 text-white mt-1" placeholder="invoice|receipt|order" value={newRule.match_pattern} onChange={(e) => setNewRule({ ...newRule, match_pattern: e.target.value })} /></div>
                                    <div className="flex gap-4 items-end pb-2">
                                        <label className="flex items-center gap-1 text-xs text-slate-300 cursor-pointer"><input type="checkbox" checked={newRule.use_ai} onChange={(e) => setNewRule({ ...newRule, use_ai: e.target.checked, auto_send: e.target.checked ? newRule.auto_send : false })} className="accent-blue-500" /> Use AI to draft reply</label>
                                        <label className="flex items-center gap-1 text-xs text-slate-300 cursor-pointer"><input type="checkbox" checked={newRule.auto_send} onChange={(e) => setNewRule({ ...newRule, auto_send: e.target.checked })} className="accent-emerald-500" disabled={!newRule.use_ai} /> Auto-send (no approval)</label>
                                    </div>
                                </div>
                                {newRule.use_ai ? (
                                    <div><Label className="text-slate-300">AI Prompt (optional — leave blank for default)</Label>
                                        <textarea className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-sm text-white resize-y min-h-[60px] mt-1" placeholder="Reply politely saying I'm out of office until Monday" value={newRule.ai_prompt} onChange={(e) => setNewRule({ ...newRule, ai_prompt: e.target.value })} /></div>
                                ) : (
                                    <>
                                        <div><Label className="text-slate-300">Reply Subject (leave blank to use Re: original)</Label><Input className="bg-slate-900 border-slate-700 text-white mt-1" value={newRule.reply_subject} onChange={(e) => setNewRule({ ...newRule, reply_subject: e.target.value })} /></div>
                                        <div><Label className="text-slate-300">Reply Body</Label><textarea className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-sm text-white resize-y min-h-[80px] mt-1" value={newRule.reply_body} onChange={(e) => setNewRule({ ...newRule, reply_body: e.target.value })} /></div>
                                    </>
                                )}
                                <Button size="sm" className="bg-blue-600 hover:bg-blue-700" onClick={handleAdd} disabled={saving}>{saving ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <Plus className="h-3 w-3 mr-1" />} Add Rule</Button>
                            </CardContent>
                        </Card>
                    )}

                    {rules.length === 0 ? (
                        <p className="text-slate-500 text-sm italic py-6 text-center">No rules yet. Add one to start auto-responding.</p>
                    ) : (
                        <div className="space-y-2">
                            {rules.map(r => (
                                <div key={r.id} className="flex items-center gap-3 py-3 px-3 rounded bg-slate-950/50 border border-slate-800 hover:bg-slate-900/30">
                                    <div className={`h-2 w-2 rounded-full ${r.enabled ? "bg-emerald-500" : "bg-slate-600"}`} />
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm text-white truncate">{r.name}</p>
                                        <p className="text-xs text-slate-500 truncate">
                                            {r.match_field} ~/{r.match_pattern}/ &nbsp;→&nbsp; {r.use_ai ? <><Bot className="h-3 w-3 inline" /> AI reply</> : `"${(r.reply_body || "").slice(0, 40)}..."`}
                                            {r.auto_send ? <span className="text-emerald-400 ml-1">· auto-send</span> : <span className="text-amber-400 ml-1">· pending</span>}
                                        </p>
                                    </div>
                                    <Button variant="ghost" size="icon" className="h-7 w-7 text-slate-500 hover:text-red-400" onClick={() => handleDelete(r.id)}><Trash2 className="h-3.5 w-3.5" /></Button>
                                </div>
                            ))}
                        </div>
                    )}
                </>
            ) : (
                /* Pending tab */
                <>
                    {pending.length === 0 ? (
                        <p className="text-slate-500 text-sm italic py-6 text-center">No pending replies.</p>
                    ) : (
                        <div className="space-y-3">
                            {pending.filter(p => p.status === "pending").map(p => (
                                <Card key={p.id} className="border-amber-900/30 bg-amber-950/10">
                                    <CardHeader className="pb-2">
                                        <div className="flex items-center justify-between">
                                            <CardTitle className="text-white text-sm truncate">{p.email_subject}</CardTitle>
                                            <span className="text-xs text-amber-400 ml-2">pending</span>
                                        </div>
                                        <p className="text-xs text-slate-500">From: {p.email_from}</p>
                                    </CardHeader>
                                    <CardContent className="space-y-2">
                                        <div className="text-xs text-slate-400 bg-slate-900/50 rounded p-2 max-h-[80px] overflow-y-auto">{p.email_body?.slice(0, 300)}</div>
                                        <div className="h-px bg-slate-800" />
                                        <div>
                                            <p className="text-xs text-emerald-400 font-medium">Reply: {p.reply_subject}</p>
                                            <p className="text-xs text-slate-300 bg-slate-900/50 rounded p-2 mt-1">{p.reply_body?.slice(0, 500)}</p>
                                        </div>
                                        <div className="flex gap-2 pt-1">
                                            <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700 h-7 text-xs" onClick={() => handleApprove(p.id)}><CheckCircle2 className="h-3 w-3 mr-1" /> Approve & Send</Button>
                                            <Button size="sm" variant="outline" className="border-red-800 text-red-400 hover:bg-red-950/20 h-7 text-xs" onClick={() => handleReject(p.id)}><X className="h-3 w-3 mr-1" /> Reject</Button>
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
