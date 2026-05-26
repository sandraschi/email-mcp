import { useState, useEffect, useCallback, useRef } from "react";
import { fetchWithAuth } from "@/lib/api";
import { useToast } from "@/components/toast";
import { Loader2, RefreshCw, Search, Trash2, Star, Paperclip, Download, ChevronLeft, ChevronRight, Bell, BellOff, Clock } from "lucide-react";

type Email = { id: string; subject: string; from: string; date: string; read: boolean; _service?: string };
type Attachment = { filename: string; content_type: string; size: number; content_id: string; part_index: number };
type EmailDetail = { id: string; subject: string; from: string; to: string; cc: string; date: string; text_body: string; html_body: string | null; attachments?: Attachment[] };

function Avatar({ name, email }: { name: string; email: string }) {
    const initial = (name || email || "?").charAt(0).toUpperCase();
    const colors = ["bg-blue-600", "bg-emerald-600", "bg-purple-600", "bg-amber-600", "bg-rose-600", "bg-cyan-600"];
    const color = colors[Math.abs((email || name).split("").reduce((a, c) => a + c.charCodeAt(0), 0)) % colors.length];
    return <div className={`h-9 w-9 rounded-full ${color} flex items-center justify-center text-white text-sm font-medium shrink-0`}>{initial}</div>;
}

function timeAgo(dateStr: string): string {
    try {
        const d = new Date(dateStr); const now = Date.now(); const diff = now - d.getTime(); const mins = Math.floor(diff / 60000);
        if (mins < 1) return "now"; if (mins < 60) return `${mins}m`; const hours = Math.floor(mins / 60);
        if (hours < 24) return `${hours}h`; const days = Math.floor(hours / 24);
        if (days < 7) return `${days}d`; return d.toLocaleDateString([], { month: "short", day: "numeric" });
    } catch { return dateStr; }
}

function formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes}B`; if (bytes < 1048576) return `${(bytes / 1024).toFixed(0)}KB`;
    return `${(bytes / 1048576).toFixed(1)}MB`;
}

export function MailReader() {
    const { toast } = useToast();
    const [emails, setEmails] = useState<Email[]>([]);
    const [selectedEmail, setSelectedEmail] = useState<EmailDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [detailLoading, setDetailLoading] = useState(false);
    const [services, setServices] = useState<string[]>([]);
    const [folders, setFolders] = useState<string[]>([]);
    const [selectedService, setSelectedService] = useState("unified");
    const [folder, setFolder] = useState("INBOX");
    const [searchQuery, setSearchQuery] = useState("");
    const [unreadOnly, setUnreadOnly] = useState(false);
    const [showMobileList, setShowMobileList] = useState(true);
    const resizeRef = useRef<HTMLDivElement>(null);
    const dragging = useRef(false);
    const [listWidth, setListWidth] = useState(380);
    const [notifyEnabled, setNotifyEnabled] = useState(false);
    const [snoozedIds, setSnoozedIds] = useState<Set<string>>(new Set());
    const prevEmailIds = useRef<Set<string>>(new Set());

    // Request notification permission
    useEffect(() => {
        if ("Notification" in window && Notification.permission === "default") {
            Notification.requestPermission();
        }
    }, []);

    // Check for new emails and notify
    useEffect(() => {
        if (!notifyEnabled || emails.length === 0) return;
        const currentIds = new Set(emails.map(e => e.id));
        const newIds = [...currentIds].filter(id => !prevEmailIds.current.has(id));
        if (newIds.length > 0 && "Notification" in window && Notification.permission === "granted") {
            const newEmails = emails.filter(e => newIds.includes(e.id));
            newEmails.slice(0, 3).forEach(e => {
                new Notification(`📬 ${e.from}`, { body: e.subject || "(No Subject)", icon: "/favicon.ico" });
            });
        }
        prevEmailIds.current = currentIds;
    }, [emails, notifyEnabled]);

    const handleSnooze = (emailId: string) => {
        setSnoozedIds(prev => new Set(prev).add(emailId));
        setTimeout(() => setSnoozedIds(prev => { const n = new Set(prev); n.delete(emailId); return n; }), 30 * 60 * 1000); // 30 min
        toast("info", "Snoozed for 30 minutes");
    };

    const filteredEmails = emails.filter(e => !snoozedIds.has(e.id));

    const fetchEmails = useCallback(async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams({ limit: "50", unread_only: String(unreadOnly) });
            let url: string;
            if (selectedService === "unified") {
                url = `/api/inbox/unified?${params}`;
            } else {
                params.set("service", selectedService); params.set("folder", folder);
                url = searchQuery.trim() ? `/api/search?q=${encodeURIComponent(searchQuery)}&${params}` : `/api/inbox?${params}`;
            }
            const data = await fetchWithAuth(url);
            setEmails(data.emails || []);
        } catch { setEmails([]); }
        finally { setLoading(false); }
    }, [selectedService, folder, unreadOnly, searchQuery]);

    useEffect(() => {
        fetchWithAuth("/api/services").then(d => {
            const names = Object.keys(d.services || {});
            setServices(names);
        }).catch(() => {});
    }, []);

    useEffect(() => {
        if (selectedService !== "unified") {
            fetchWithAuth(`/api/services/${encodeURIComponent(selectedService)}/folders`).then(d => {
                const names = (d.folders || []).map((f: any) => f.name);
                if (names.length) setFolders(names);
            }).catch(() => {});
        }
    }, [selectedService]);

    useEffect(() => { fetchEmails(); }, [fetchEmails]);

    const handleSelect = async (email: Email) => {
        setShowMobileList(false); setDetailLoading(true);
        const svc = email._service || selectedService;
        try {
            const data = await fetchWithAuth(`/api/inbox/${encodeURIComponent(email.id)}?service=${encodeURIComponent(svc)}&folder=${folder}`);
            setSelectedEmail(data);
            fetchWithAuth(`/api/inbox/${encodeURIComponent(email.id)}/mark-read`, { method: "POST", body: JSON.stringify({ service: svc, folder }) }).catch(() => {});
        } catch { setSelectedEmail(null); }
        finally { setDetailLoading(false); }
    };

    const handleDelete = async (e: React.MouseEvent, emailId: string) => {
        e.stopPropagation();
        const svc = selectedEmail?._service || selectedService;
        try {
            await fetchWithAuth(`/api/inbox/${encodeURIComponent(emailId)}?service=${encodeURIComponent(svc)}&folder=${folder}`, { method: "DELETE" });
            setEmails(prev => prev.filter(e => e.id !== emailId));
            if (selectedEmail?.id === emailId) setSelectedEmail(null);
            toast("success", "Deleted");
        } catch { toast("error", "Delete failed"); }
    };

    const handleDownload = (emailId: string, att: Attachment) => {
        const svc = selectedEmail?._service || selectedService;
        window.open(`/api/inbox/${encodeURIComponent(emailId)}/attachment/${att.part_index}?service=${encodeURIComponent(svc)}&folder=${folder}`, "_blank");
    };

    // Resize handle
    useEffect(() => {
        const el = resizeRef.current; if (!el) return;
        const onMouseDown = () => { dragging.current = true; document.body.style.cursor = "col-resize"; };
        const onMouseUp = () => { dragging.current = false; document.body.style.cursor = ""; };
        const onMouseMove = (e: MouseEvent) => { if (dragging.current) setListWidth(Math.max(280, Math.min(600, e.clientX))); };
        el.addEventListener("mousedown", onMouseDown); document.addEventListener("mouseup", onMouseUp); document.addEventListener("mousemove", onMouseMove);
        return () => { el.removeEventListener("mousedown", onMouseDown); document.removeEventListener("mouseup", onMouseUp); document.removeEventListener("mousemove", onMouseMove); };
    }, []);

    return (
        <div className="flex flex-col h-[calc(100vh-8rem)]">
            {/* Top bar */}
            <div className="flex items-center gap-2 pb-2 flex-wrap">
                <select className="bg-slate-900 border border-slate-700 text-white text-xs rounded px-2 py-1" value={selectedService} onChange={(e) => setSelectedService(e.target.value)}>
                    <option value="unified">📬 Unified Inbox</option>
                    {services.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
                {selectedService !== "unified" && (
                    <select className="bg-slate-900 border border-slate-700 text-white text-xs rounded px-2 py-1" value={folder} onChange={(e) => setFolder(e.target.value)}>
                        {(folders.length ? folders : ["INBOX", "Sent", "Drafts", "Trash", "Spam"]).map(f => <option key={f}>{f}</option>)}
                    </select>
                )}
                <div className="relative flex-1 max-w-xs">
                    <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-500" />
                    <input className="w-full bg-slate-900 border border-slate-700 rounded-md pl-7 pr-2 py-1.5 text-xs text-white focus:outline-none focus:ring-1 focus:ring-blue-500" placeholder={selectedService === "unified" ? "Search (uses first service)" : "Search..."} value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
                </div>
                <label className="flex items-center gap-1 text-xs text-slate-400 cursor-pointer"><input type="checkbox" checked={unreadOnly} onChange={(e) => setUnreadOnly(e.target.checked)} className="accent-blue-500" /> Unread</label>
                <button className={`p-1.5 rounded text-xs ${notifyEnabled ? "text-blue-400" : "text-slate-500 hover:text-white"}`} onClick={() => setNotifyEnabled(!notifyEnabled)} title={notifyEnabled ? "Notifications on" : "Notifications off"}>
                    {notifyEnabled ? <Bell className="h-4 w-4" /> : <BellOff className="h-4 w-4" />}
                </button>
                <button className="p-1.5 text-slate-500 hover:text-white rounded" onClick={fetchEmails}><RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /></button>
            </div>

            <div className="flex flex-1 overflow-hidden border border-slate-800 rounded-lg bg-slate-950/30">
                {/* Email list */}
                <div className={`${showMobileList ? "flex" : "hidden"} md:flex flex-col border-r border-slate-800 overflow-hidden`} style={{ width: listWidth, minWidth: 280 }}>
                    <div className="flex-1 overflow-y-auto">
                        {loading && emails.length === 0 ? <div className="flex items-center justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-blue-500" /></div>
                        : emails.length === 0 ? <div className="text-slate-500 text-sm text-center py-12 italic">No messages</div>
                        : filteredEmails.map(email => (
                            <div key={`${email._service}-${email.id}`}
                                className={`group flex items-start gap-2.5 px-3 py-2.5 cursor-pointer border-b border-slate-800/50 transition-colors ${selectedEmail?.id === email.id ? "bg-blue-950/20" : "hover:bg-slate-900/30"} ${!email.read ? "bg-slate-900/20" : ""}`}
                                onClick={() => handleSelect(email)}>
                                <Avatar name={email.from} email={email.from} />
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center justify-between gap-2">
                                        <p className={`text-sm truncate ${email.read ? "text-slate-300" : "text-white font-medium"}`}>{email.from}</p>
                                        <span className="text-xs text-slate-500 shrink-0">{timeAgo(email.date)}</span>
                                    </div>
                                    <p className={`text-xs truncate mt-0.5 ${email.read ? "text-slate-500" : "text-slate-300"}`}>{email.subject || "(No Subject)"}</p>
                                    {email._service && <p className="text-[10px] text-blue-400 mt-0.5">{email._service}</p>}
                                </div>
                                <button onClick={(e) => { e.stopPropagation(); handleSnooze(email.id); }} className="p-1 text-slate-600 hover:text-amber-400 opacity-0 group-hover:opacity-100 shrink-0" title="Snooze 30min"><Clock className="h-3 w-3" /></button>
                                <button onClick={(e) => handleDelete(e, email.id)} className="p-1 text-slate-600 hover:text-red-400 opacity-0 group-hover:opacity-100 shrink-0"><Trash2 className="h-3 w-3" /></button>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Resize handle */}
                <div ref={resizeRef} className="w-1 hover:w-1.5 bg-slate-800 hover:bg-blue-500 cursor-col-resize transition-colors hidden md:block shrink-0" />

                {/* Email detail */}
                <div className={`${!showMobileList ? "flex" : "hidden"} md:flex flex-1 flex-col overflow-hidden`}>
                    {detailLoading ? (
                        <div className="flex items-center justify-center flex-1"><Loader2 className="h-8 w-8 animate-spin text-blue-500" /></div>
                    ) : selectedEmail ? (
                        <div className="flex-1 overflow-y-auto p-4 space-y-3">
                            <h2 className="text-lg font-semibold text-white">{selectedEmail.subject || "(No Subject)"}</h2>
                            <div className="flex items-center gap-3">
                                <Avatar name={selectedEmail.from} email={selectedEmail.from} />
                                <div>
                                    <p className="text-sm text-white font-medium">{selectedEmail.from}</p>
                                    <p className="text-xs text-slate-500">to {selectedEmail.to || "—"}{selectedEmail.cc ? `, cc ${selectedEmail.cc}` : ""}</p>
                                    <p className="text-xs text-slate-500">{selectedEmail.date}</p>
                                </div>
                            </div>
                            {/* Attachments */}
                            {selectedEmail.attachments && selectedEmail.attachments.length > 0 && (
                                <div className="flex gap-2 flex-wrap">
                                    {selectedEmail.attachments.map(att => (
                                        <div key={att.part_index} className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border border-slate-700 bg-slate-900/50 text-xs cursor-pointer hover:bg-slate-800 transition-colors" onClick={() => handleDownload(selectedEmail.id, att)} title="Download">
                                            <Paperclip className="h-3 w-3 text-blue-400" />
                                            <span className="text-slate-300 truncate max-w-[150px]">{att.filename}</span>
                                            <span className="text-slate-500 shrink-0">({formatSize(att.size)})</span>
                                            <Download className="h-3 w-3 text-slate-500 ml-1" />
                                        </div>
                                    ))}
                                </div>
                            )}
                            <div className="h-px bg-slate-800" />
                            {selectedEmail.html_body ? (
                                <div className="prose prose-invert prose-slate max-w-none text-sm [&_a]:text-blue-400 [&_img]:max-w-full" dangerouslySetInnerHTML={{ __html: selectedEmail.html_body }} />
                            ) : (
                                <pre className="text-sm text-slate-300 whitespace-pre-wrap font-sans leading-relaxed">{selectedEmail.text_body || "(No body)"}</pre>
                            )}
                        </div>
                    ) : (
                        <div className="flex-1 flex items-center justify-center text-slate-500 text-sm italic">Select an email to read</div>
                    )}
                </div>
            </div>
        </div>
    );
}
