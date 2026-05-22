import { useState, useEffect, useCallback, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Play, Square, Loader2, Mail, Trash2, Forward, Sparkles, RefreshCw, Copy, CheckCircle2, AlertCircle, Server, Inbox, Send, Eye, EyeOff, Bell } from "lucide-react";
import { fetchWithAuth } from "@/lib/api";
import { useToast } from "@/components/toast";

type LabEmail = { id: string; from: string; to: string[]; subject: string; date: string; size: number };
type LabEmailDetail = LabEmail & { text_body: string; html_body?: string | null };

const SCENARIOS = [
    { value: "general", label: "General / Mixed" },
    { value: "newsletter", label: "Newsletters & Subscriptions" },
    { value: "invoice", label: "Invoices & Receipts" },
    { value: "support", label: "Support Tickets" },
    { value: "marketing", label: "Marketing & Promotions" },
    { value: "security", label: "Security Alerts" },
    { value: "social", label: "Social Notifications" },
    { value: "spam", label: "Spam / Phishing" },
    { value: "calendar", label: "Calendar & Meeting Invites" },
    { value: "shipping", label: "Shipping & Order Updates" },
];

export function Lab() {
    const { toast } = useToast();
    const [serverRunning, setServerRunning] = useState(false);
    const [serverPort, setServerPort] = useState(0);
    const [serverLoading, setServerLoading] = useState(false);
    const [emails, setEmails] = useState<LabEmail[]>([]);
    const [emailCount, setEmailCount] = useState(0);
    const [selectedEmail, setSelectedEmail] = useState<LabEmailDetail | null>(null);
    const [emailLoading, setEmailLoading] = useState(false);
    const [pollInterval, setPollInterval] = useState<ReturnType<typeof setInterval> | null>(null);

    // AI generator
    const [scenario, setScenario] = useState("general");
    const [genCount, setGenCount] = useState(5);
    const [generating, setGenerating] = useState(false);

    // Forward
    const [forwardTo, setForwardTo] = useState("");
    const [forwarding, setForwarding] = useState<string | null>(null);

    // Watcher
    const [watcherRunning, setWatcherRunning] = useState(false);
    const [watcherInterval, setWatcherInterval] = useState(60);
    const [webhookUrl, setWebhookUrl] = useState("");

    const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const fetchStatus = useCallback(async () => {
        try {
            const data = await fetchWithAuth("/api/lab/status");
            setServerRunning(data.running);
            setServerPort(data.port);
            setEmailCount(data.email_count);
        } catch { /* server may not support lab */ }
    }, []);

    const fetchEmails = useCallback(async () => {
        try {
            const data = await fetchWithAuth("/api/lab/emails");
            setEmails(data.emails || []);
            setEmailCount(data.count || 0);
        } catch { /* ignore */ }
    }, []);

    useEffect(() => {
        fetchStatus();
        fetchEmails();
        return () => { if (pollRef.current) clearInterval(pollRef.current); };
    }, [fetchStatus, fetchEmails]);

    useEffect(() => {
        if (serverRunning) {
            pollRef.current = setInterval(() => {
                fetchEmails();
            }, 3000);
        } else {
            if (pollRef.current) clearInterval(pollRef.current);
        }
        return () => { if (pollRef.current) clearInterval(pollRef.current); };
    }, [serverRunning, fetchEmails]);

    const handleStart = async () => {
        setServerLoading(true);
        try {
            const data = await fetchWithAuth("/api/lab/start", { method: "POST" });
            if (data.error) { toast("error", data.error); return; }
            setServerRunning(true);
            setServerPort(data.port);
            toast("success", `Lab server started on port ${data.port}`);
            fetchEmails();
        } catch (err: unknown) { toast("error", err instanceof Error ? err.message : "Start failed"); }
        finally { setServerLoading(false); }
    };

    const handleStop = async () => {
        setServerLoading(true);
        try {
            const data = await fetchWithAuth("/api/lab/stop", { method: "POST" });
            setServerRunning(false);
            toast("success", data.message || "Server stopped");
            fetchEmails();
        } catch (err: unknown) { toast("error", err instanceof Error ? err.message : "Stop failed"); }
        finally { setServerLoading(false); }
    };

    const handleClear = async () => {
        try {
            await fetchWithAuth("/api/lab/emails", { method: "DELETE" });
            setEmails([]);
            setEmailCount(0);
            setSelectedEmail(null);
            toast("success", "Emails cleared");
        } catch (err: unknown) { toast("error", err instanceof Error ? err.message : "Clear failed"); }
    };

    const handleGenerate = async () => {
        setGenerating(true);
        try {
            const data = await fetchWithAuth("/api/lab/generate", {
                method: "POST",
                body: JSON.stringify({ count: genCount, scenario }),
            });
            if (data.success) {
                toast("success", `${data.injected} emails generated`);
                fetchEmails();
            } else {
                toast("error", data.error || "Generation failed");
            }
        } catch (err: unknown) { toast("error", err instanceof Error ? err.message : "Generate failed"); }
        finally { setGenerating(false); }
    };

    // Watcher handlers
    const handleWatcherStart = async () => {
        try {
            const data = await fetchWithAuth("/api/watcher/start", { method: "POST", body: JSON.stringify({ interval: watcherInterval, webhook_url: webhookUrl.trim() }) });
            setWatcherRunning(data.running);
            if (data.running) toast("success", data.message);
            else toast("error", "Failed to start watcher");
        } catch (err: unknown) { toast("error", err instanceof Error ? err.message : "Start failed"); }
    };
    const handleWatcherStop = async () => {
        try {
            const data = await fetchWithAuth("/api/watcher/stop", { method: "POST" });
            setWatcherRunning(false);
            toast("success", data.message);
        } catch (err: unknown) { toast("error", err instanceof Error ? err.message : "Stop failed"); }
    };
    useEffect(() => {
        const poll = setInterval(async () => {
            try { const data = await fetchWithAuth("/api/watcher/status"); setWatcherRunning(data.running); }
            catch { /* ignore */ }
        }, 5000);
        return () => clearInterval(poll);
    }, []);

    const handleOpenEmail = async (emailId: string) => {
        setEmailLoading(true);
        try {
            const data = await fetchWithAuth(`/api/lab/emails/${emailId}`);
            setSelectedEmail(data);
        } catch { toast("error", "Failed to load email"); setSelectedEmail(null); }
        finally { setEmailLoading(false); }
    };

    const handleForward = async (emailId: string) => {
        if (!forwardTo.trim()) { toast("error", "Enter a forwarding address"); return; }
        setForwarding(emailId);
        try {
            const data = await fetchWithAuth(`/api/lab/forward/${emailId}`, {
                method: "POST",
                body: JSON.stringify({ to: forwardTo.trim() }),
            });
            if (data.success) { toast("success", `Forwarded to ${forwardTo}`); }
            else { toast("error", data.error || "Forward failed"); }
        } catch (err: unknown) { toast("error", err instanceof Error ? err.message : "Forward failed"); }
        finally { setForwarding(null); }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">Mail Lab</h2>
                    <p className="text-slate-400">Throwaway SMTP server for testing emails locally</p>
                </div>
            </div>

            {/* Server Control Panel */}
            <Card className={`border ${serverRunning ? "border-emerald-900/30 bg-emerald-950/10" : "border-slate-800 bg-slate-950/50"}`}>
                <CardHeader className="pb-2 flex flex-row items-center justify-between">
                    <CardTitle className="text-white text-sm flex items-center gap-2">
                        <Server className={`h-4 w-4 ${serverRunning ? "text-emerald-400" : "text-slate-500"}`} />
                        SMTP Server
                    </CardTitle>
                    <div className="flex gap-2">
                        {!serverRunning ? (
                            <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700 h-7 text-xs" onClick={handleStart} disabled={serverLoading}>
                                {serverLoading ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <Play className="h-3 w-3 mr-1" />}
                                Start
                            </Button>
                        ) : (
                            <Button size="sm" variant="outline" className="border-red-800 text-red-400 hover:bg-red-950/20 h-7 text-xs" onClick={handleStop} disabled={serverLoading}>
                                {serverLoading ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <Square className="h-3 w-3 mr-1" />}
                                Stop
                            </Button>
                        )}
                        <Button size="sm" variant="ghost" className="text-slate-500 hover:text-white h-7 text-xs" onClick={() => { fetchStatus(); fetchEmails(); }}>
                            <RefreshCw className="h-3 w-3" />
                        </Button>
                    </div>
                </CardHeader>
                <CardContent className="text-xs text-slate-400">
                    {serverRunning ? (
                        <span className="flex items-center gap-2">
                            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                            Running on <code className="text-emerald-300">127.0.0.1:{serverPort}</code>
                            &nbsp;·&nbsp; {emailCount} email{emailCount !== 1 ? "s" : ""} captured
                        </span>
                    ) : (
                        <span className="flex items-center gap-2">
                            <span className="h-2 w-2 rounded-full bg-slate-600" />
                            Stopped — click Start to launch a throwaway SMTP server
                        </span>
                    )}
                </CardContent>
            </Card>

            {/* AI Generator + Forward Controls */}
            <div className="grid gap-4 md:grid-cols-2">
                <Card className="border-purple-900/30 bg-purple-950/10">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-white text-sm flex items-center gap-2">
                            <Sparkles className="h-4 w-4 text-purple-400" />
                            AI Message Generator
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex gap-2 flex-wrap items-end">
                            <div className="flex-1 min-w-[140px]">
                                <Label className="text-slate-400 text-xs">Scenario</Label>
                                <select className="bg-slate-900 border border-slate-700 text-white text-xs rounded px-2 py-1.5 w-full mt-1" value={scenario} onChange={(e) => setScenario(e.target.value)}>
                                    {SCENARIOS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
                                </select>
                            </div>
                            <div className="w-20">
                                <Label className="text-slate-400 text-xs">Count</Label>
                                <select className="bg-slate-900 border border-slate-700 text-white text-xs rounded px-2 py-1.5 w-full mt-1" value={genCount} onChange={(e) => setGenCount(Number(e.target.value))}>
                                    {[3, 5, 10, 15, 25].map((n) => <option key={n}>{n}</option>)}
                                </select>
                            </div>
                            <Button size="sm" className="bg-purple-600 hover:bg-purple-700 h-7 text-xs" onClick={handleGenerate} disabled={generating || !serverRunning}>
                                {generating ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <Sparkles className="h-3 w-3 mr-1" />}
                                Generate
                            </Button>
                        </div>
                        {!serverRunning && <p className="text-xs text-amber-500 mt-2">Start the SMTP server first to generate emails</p>}
                    </CardContent>
                </Card>

                <Card className="border-blue-900/30 bg-blue-950/10">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-white text-sm flex items-center gap-2">
                            <Send className="h-4 w-4 text-blue-400" />
                            Forward to Real Email
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex gap-2 items-end">
                            <div className="flex-1">
                                <Label className="text-slate-400 text-xs">Destination address</Label>
                                <Input className="bg-slate-900 border-slate-700 text-white mt-1 text-xs" placeholder="your@email.com" value={forwardTo} onChange={(e) => setForwardTo(e.target.value)} />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Mail Watcher */}
            <Card className="border-cyan-900/30 bg-cyan-950/10">
                <CardHeader className="pb-2">
                    <CardTitle className="text-white text-sm flex items-center gap-2">
                        <Bell className="h-4 w-4 text-cyan-400" />
                        Mail Watcher
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex gap-2 items-center flex-wrap">
                        <span className="text-xs text-slate-400">
                            {watcherRunning ? (
                                <span className="flex items-center gap-1 text-emerald-400"><span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" /> Watching (every {watcherInterval}s)</span>
                            ) : (
                                "Monitor IMAP for new mail and POST to a webhook"
                            )}
                        </span>
                        <Input className="bg-slate-900 border-slate-700 text-white text-xs w-48 h-7" placeholder="Webhook URL (robofang/fleet-agent)" value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)} />
                        <Input className="bg-slate-900 border-slate-700 text-white text-xs w-16 h-7" placeholder="60s" value={watcherInterval} onChange={(e) => setWatcherInterval(Number(e.target.value) || 60)} />
                        {!watcherRunning ? (
                            <Button size="sm" className="bg-cyan-600 hover:bg-cyan-700 h-7 text-xs" onClick={handleWatcherStart} disabled={!webhookUrl.trim()}>
                                <Bell className="h-3 w-3 mr-1" /> Start Watch
                            </Button>
                        ) : (
                            <Button size="sm" variant="outline" className="border-red-800 text-red-400 hover:bg-red-950/20 h-7 text-xs" onClick={handleWatcherStop}>
                                <Square className="h-3 w-3 mr-1" /> Stop
                            </Button>
                        )}
                    </div>
                    {!webhookUrl.trim() && <p className="text-xs text-amber-500 mt-1">Enter a webhook URL to receive notifications (robofang, fleet-agent, etc.)</p>}
                </CardContent>
            </Card>

            {/* Captured Emails */}
            <Card className="border-slate-800 bg-slate-950/50">
                <CardHeader className="pb-2 flex flex-row items-center justify-between">
                    <CardTitle className="text-white text-sm flex items-center gap-2">
                        <Inbox className="h-4 w-4 text-emerald-400" />
                        Captured Emails ({emailCount})
                    </CardTitle>
                    <div className="flex gap-2">
                        <Button size="sm" variant="ghost" className="text-slate-500 hover:text-white h-7 text-xs" onClick={handleClear} disabled={emails.length === 0}>
                            <Trash2 className="h-3 w-3 mr-1" /> Clear
                        </Button>
                    </div>
                </CardHeader>
                <CardContent>
                    {emails.length === 0 ? (
                        <p className="text-slate-500 text-sm italic py-6 text-center">No emails captured yet. Start the server and send some test emails.</p>
                    ) : (
                        <div className="space-y-0">
                            {emails.map((email) => (
                                <div key={email.id}>
                                    <div
                                        className="flex items-start gap-3 py-2.5 px-2 rounded cursor-pointer hover:bg-slate-900/30 transition-colors border-b border-slate-800 last:border-0"
                                        onClick={() => handleOpenEmail(email.id)}
                                    >
                                        <div className="mt-0.5 p-1.5 bg-slate-900 rounded shrink-0">
                                            <Mail className="h-3 w-3 text-blue-400" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm truncate text-white font-medium">{email.subject}</p>
                                            <p className="text-xs text-slate-500 truncate">{email.from} &nbsp;·&nbsp; {email.date}</p>
                                        </div>
                                        <Button
                                            variant="ghost" size="icon" className="h-7 w-7 shrink-0 text-slate-500 hover:text-blue-400"
                                            onClick={(e) => { e.stopPropagation(); handleForward(email.id); }}
                                            disabled={forwarding === email.id || !forwardTo.trim()}
                                            title="Forward to real email"
                                        >
                                            {forwarding === email.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <Forward className="h-3 w-3" />}
                                        </Button>
                                    </div>

                                    {/* Expanded detail */}
                                    {selectedEmail?.id === email.id && (
                                        <div className="px-2 pb-3 pt-1 border-b border-slate-800">
                                            {emailLoading ? (
                                                <div className="flex items-center gap-2 text-slate-500 py-4"><Loader2 className="h-4 w-4 animate-spin" /> Loading...</div>
                                            ) : selectedEmail ? (
                                                <div className="bg-slate-900/50 rounded-md p-3 space-y-2">
                                                    <div className="text-xs text-slate-400"><span className="text-slate-500">From:</span> {selectedEmail.from}</div>
                                                    <div className="text-xs text-slate-400"><span className="text-slate-500">To:</span> {selectedEmail.to?.join(", ") || "—"}</div>
                                                    <div className="text-xs text-slate-400"><span className="text-slate-500">Date:</span> {selectedEmail.date}</div>
                                                    <div className="h-px bg-slate-800" />
                                                    <pre className="text-xs text-slate-300 whitespace-pre-wrap font-sans leading-relaxed">{selectedEmail.text_body || "(No body)"}</pre>
                                                    {selectedEmail.html_body && (
                                                        <div className="mt-2"><span className="text-xs text-amber-400">HTML version available</span></div>
                                                    )}
                                                    <div className="flex gap-2 pt-1">
                                                        <Button size="sm" className="bg-blue-600 hover:bg-blue-700 h-6 text-xs" onClick={() => handleForward(selectedEmail.id)} disabled={!forwardTo.trim()}>
                                                            <Forward className="h-3 w-3 mr-1" /> Forward to {forwardTo || "..."}
                                                        </Button>
                                                    </div>
                                                </div>
                                            ) : (
                                                <p className="text-xs text-red-400 py-2">Failed to load email</p>
                                            )}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
