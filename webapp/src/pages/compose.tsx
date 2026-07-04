import {
  AlertCircle,
  BookTemplate,
  CheckCircle2,
  Clock,
  FileText,
  Loader2,
  RefreshCw,
  Save,
  Send,
  Sparkles,
  Trash2,
  User,
  Wand2,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useToast } from "@/components/toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { fetchWithAuth } from "@/lib/api";

type Service = { name: string; type: string };
type Draft = {
  id: string;
  to: string;
  cc: string;
  subject: string;
  body: string;
  html?: string;
  service: string;
  updated_at: number;
};
type Provider = {
  id: string;
  name: string;
  available: boolean | null;
  models: string[];
};
type ImproveParams = { style: string; length: string; mood: string };

const STYLES = [
  { value: "professional", label: "Professional" },
  { value: "formal", label: "Formal" },
  { value: "casual", label: "Casual" },
  { value: "friendly", label: "Friendly" },
  { value: "persuasive", label: "Persuasive" },
  { value: "direct", label: "Direct" },
];

const LENGTHS = [
  { value: "same", label: "Same length" },
  { value: "shorter", label: "Shorter" },
  { value: "longer", label: "Longer" },
  { value: "concise", label: "Concise" },
  { value: "detailed", label: "Detailed" },
];

const MOODS = [
  { value: "neutral", label: "Neutral" },
  { value: "enthusiastic", label: "Enthusiastic" },
  { value: "urgent", label: "Urgent" },
  { value: "empathetic", label: "Empathetic" },
  { value: "confident", label: "Confident" },
  { value: "humble", label: "Humble" },
];

export function Compose() {
  const [searchParams] = useSearchParams();
  const { toast } = useToast();

  const [to, setTo] = useState(searchParams.get("to") || "");
  const [cc, setCc] = useState("");
  const [bcc, setBcc] = useState("");
  const [subject, setSubject] = useState(searchParams.get("subject") || "");
  const [body, setBody] = useState("");
  const [htmlBody, setHtmlBody] = useState("");
  const [useHtml, setUseHtml] = useState(false);
  const [service, setService] = useState("default");
  const [services, setServices] = useState<Service[]>([]);
  const [sending, setSending] = useState(false);
  const [suggesting, setSuggesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [showDrafts, setShowDrafts] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; msg: string } | null>(
    null,
  );
  const [draftId, setDraftId] = useState<string | null>(null);

  // ── Improve state ──
  const [_providers, setProviders] = useState<Provider[]>([]);
  const [loadingProviders, setLoadingProviders] = useState(false);
  const [improveStyle, setImproveStyle] = useState("professional");
  const [improveLength, setImproveLength] = useState("same");
  const [improveMood, setImproveMood] = useState("neutral");
  const [improving, setImproving] = useState(false);

  // ── Expander state ──
  const [expandNote, setExpandNote] = useState("");
  const [expandStyle, setExpandStyle] = useState("humorous");
  const [expandLength, setExpandLength] = useState("long");
  const [expandContext, setExpandContext] = useState("none");
  const [expanding, setExpanding] = useState(false);

  // ── Bulk send state ──
  const [bulkRecipients, setBulkRecipients] = useState("");
  const [bulkConfirmed, setBulkConfirmed] = useState(false);
  const [bulkSending, setBulkSending] = useState(false);
  const [bulkResult, setBulkResult] = useState<{
    ok: boolean;
    msg: string;
    results?: any[];
  } | null>(null);
  const [showBulk, setShowBulk] = useState(false);

  // ── Templates state ──
  const [templates, setTemplates] = useState<any[]>([]);
  const [showTemplates, setShowTemplates] = useState(false);
  const [signature, setSignature] = useState("");
  const [scheduleAt, setScheduleAt] = useState("");
  const [showSchedule, setShowSchedule] = useState(false);
  const [contactSuggestions, setContactSuggestions] = useState<any[]>([]);
  const [showContactSuggestions, setShowContactSuggestions] = useState(false);
  const toRef = useRef<HTMLInputElement>(null);

  // Load templates
  useEffect(() => {
    fetchWithAuth("/api/templates")
      .then((d) => setTemplates(d.templates || []))
      .catch(() => {});
  }, []);

  // Load signature when service changes
  useEffect(() => {
    fetchWithAuth(`/api/signatures?service=${encodeURIComponent(service)}`)
      .then((d) => setSignature(d.signature || ""))
      .catch(() => {});
  }, [service]);

  // Contact autocomplete
  useEffect(() => {
    const val = to.split(/[,;]/).pop()?.trim() || "";
    if (val.length >= 2) {
      fetchWithAuth(`/api/contacts?q=${encodeURIComponent(val)}`)
        .then((d) => {
          setContactSuggestions(d.contacts || []);
          setShowContactSuggestions(d.contacts?.length > 0);
        })
        .catch(() => {});
    } else {
      setShowContactSuggestions(false);
    }
  }, [to]);

  useEffect(() => {
    fetchWithAuth("/api/services")
      .then((data) => {
        const svcMap = data.services || {};
        const list = Object.entries(svcMap).map(
          ([name, info]: [string, any]) => ({ name, type: info.type }),
        );
        setServices(list);
      })
      .catch(() => {});
    loadDrafts();
    loadProviders();
  }, [loadProviders, loadDrafts]);

  const loadProviders = async () => {
    setLoadingProviders(true);
    try {
      const data = await fetchWithAuth("/api/llm/models");
      setProviders(data.providers || []);
    } catch {
      /* ignore */
    } finally {
      setLoadingProviders(false);
    }
  };

  const loadDrafts = async () => {
    try {
      const data = await fetchWithAuth("/api/drafts");
      setDrafts(data.drafts || []);
    } catch {
      /* ignore */
    }
  };

  const loadDraft = (draft: Draft) => {
    setTo(draft.to || "");
    setCc(draft.cc || "");
    setSubject(draft.subject || "");
    setBody(draft.body || "");
    setHtmlBody(draft.html || "");
    setService(draft.service || "default");
    setDraftId(draft.id);
    setShowDrafts(false);
    toast("info", `Loaded draft: ${draft.subject || "(no subject)"}`);
  };

  const handleSaveDraft = async () => {
    if (!subject.trim() && !body.trim()) {
      toast("error", "Nothing to save");
      return;
    }
    setSaving(true);
    try {
      const payload: Record<string, unknown> = {
        to,
        cc,
        subject,
        body,
        service,
        ...(draftId ? { id: draftId } : {}),
        ...(htmlBody && useHtml ? { html: htmlBody } : {}),
      };
      const data = await fetchWithAuth(
        draftId ? `/api/drafts/${draftId}` : "/api/drafts",
        { method: draftId ? "PUT" : "POST", body: JSON.stringify(payload) },
      );
      setDraftId(data.draft?.id || data.draft_id);
      toast("success", "Draft saved");
      loadDrafts();
    } catch (err: unknown) {
      toast("error", err instanceof Error ? err.message : "Save draft failed");
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteDraft = async (id: string) => {
    try {
      await fetchWithAuth(`/api/drafts/${id}`, { method: "DELETE" });
      if (draftId === id) setDraftId(null);
      loadDrafts();
      toast("success", "Draft deleted");
    } catch (err: unknown) {
      toast(
        "error",
        err instanceof Error ? err.message : "Delete draft failed",
      );
    }
  };

  const handleSend = async () => {
    if (!to.trim() || !subject.trim() || !body.trim()) {
      setResult({ ok: false, msg: "To, Subject, and Body are required." });
      return;
    }
    setSending(true);
    setResult(null);
    try {
      let finalBody = body.trim();
      if (signature && !finalBody.includes(signature.trim().slice(0, 20))) {
        finalBody += `\n\n${signature}`;
      }
      const payload: Record<string, unknown> = {
        to: to.trim(),
        subject: subject.trim(),
        body: finalBody,
        service,
        ...(cc.trim()
          ? {
              cc: cc
                .split(",")
                .map((s) => s.trim())
                .filter(Boolean),
            }
          : {}),
        ...(bcc.trim()
          ? {
              bcc: bcc
                .split(",")
                .map((s) => s.trim())
                .filter(Boolean),
            }
          : {}),
        ...(htmlBody && useHtml ? { html: htmlBody } : {}),
      };
      const data = await fetchWithAuth("/api/send", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      if (data.success) {
        setResult({ ok: true, msg: `Sent via ${data.service || service}.` });
        toast("success", `Email sent via ${data.service || service}`);
        setTo("");
        setCc("");
        setBcc("");
        setSubject("");
        setBody("");
        setHtmlBody("");
        setDraftId(null);
        if (draftId) {
          try {
            await fetchWithAuth(`/api/drafts/${draftId}`, { method: "DELETE" });
          } catch {
            /* ignore */
          }
        }
      } else {
        setResult({ ok: false, msg: data.error || "Send failed." });
        toast("error", data.error || "Send failed");
      }
    } catch (err: unknown) {
      setResult({
        ok: false,
        msg: err instanceof Error ? err.message : String(err),
      });
      toast("error", err instanceof Error ? err.message : "Send failed");
    } finally {
      setSending(false);
    }
  };

  const suggestSubject = async () => {
    if (!body.trim()) return;
    setSuggesting(true);
    try {
      const data = await fetchWithAuth("/api/chat", {
        method: "POST",
        body: JSON.stringify({
          query: `Suggest 3 short email subject lines for this body:\n\n${body.slice(0, 500)}`,
        }),
      });
      const text = (data.response || "").trim();
      if (text) setSubject(text.split("\n")[0].replace(/^[-\d.*]+\s*/, ""));
    } catch {
      /* silent */
    } finally {
      setSuggesting(false);
    }
  };

  const handleImprove = async () => {
    if (!body.trim()) {
      toast("error", "Write a body first");
      return;
    }
    setImproving(true);
    try {
      const data = await fetchWithAuth("/api/improve", {
        method: "POST",
        body: JSON.stringify({
          text: body,
          style: improveStyle,
          length: improveLength,
          mood: improveMood,
        }),
      });
      if (data.success && data.response) {
        setBody(data.response);
        toast(
          "success",
          `Improved: ${improveStyle}, ${improveMood}, ${improveLength}`,
        );
      } else {
        toast("error", data.response || "Improve failed");
      }
    } catch (err: unknown) {
      toast("error", err instanceof Error ? err.message : "Improve failed");
    } finally {
      setImproving(false);
    }
  };

  const handleExpand = async () => {
    if (!expandNote.trim()) {
      toast("error", "Write a short note first");
      return;
    }
    setExpanding(true);
    try {
      const data = await fetchWithAuth("/api/expand", {
        method: "POST",
        body: JSON.stringify({
          text: expandNote,
          style: expandStyle,
          length: expandLength,
          context: expandContext,
        }),
      });
      if (data.success && data.response) {
        setBody(data.response);
        setExpandNote("");
        toast(
          "success",
          `Expanded: ${expandStyle}, ${expandLength}, ${expandContext}`,
        );
      } else {
        toast("error", data.response || "Expand failed");
      }
    } catch (err: unknown) {
      toast("error", err instanceof Error ? err.message : "Expand failed");
    } finally {
      setExpanding(false);
    }
  };

  const handleBulkSend = async () => {
    const parsed = bulkRecipients
      .split(/[\n,]+/)
      .map((s) => s.trim())
      .filter(Boolean);
    if (parsed.length === 0) {
      toast("error", "Paste at least one email address");
      return;
    }
    if (parsed.length > 50) {
      toast("error", "Max 50 recipients per batch");
      return;
    }
    setBulkSending(true);
    setBulkResult(null);
    try {
      const data = await fetchWithAuth("/api/send-bulk", {
        method: "POST",
        body: JSON.stringify({
          to: parsed,
          subject,
          body,
          service,
          confirmed: bulkConfirmed,
        }),
      });
      if (data.success === false && data.needs_confirmation) {
        setBulkResult({
          ok: false,
          msg: data.warning || "Large batch needs confirmation",
        });
        setBulkSending(false);
        return;
      }
      if (data.success) {
        setBulkResult({
          ok: true,
          msg: `Sent to ${data.sent}/${data.total} recipients (${data.failed} failed)`,
          results: data.results,
        });
        if (data.sent > 0)
          toast("success", `Sent to ${data.sent} recipient(s)`);
        if (data.failed > 0) toast("error", `${data.failed} failed`);
      } else {
        setBulkResult({ ok: false, msg: data.error || "Bulk send failed" });
      }
    } catch (err: unknown) {
      toast("error", err instanceof Error ? err.message : "Bulk send failed");
    } finally {
      setBulkSending(false);
    }
  };

  const parseCount = bulkRecipients
    .split(/[\n,]+/)
    .map((s) => s.trim())
    .filter(Boolean).length;

  const handleTemplateSelect = (tmpl: any) => {
    setSubject(tmpl.subject || subject);
    setBody(tmpl.body || body);
    if (tmpl.html) {
      setHtmlBody(tmpl.html);
      setUseHtml(true);
    }
    setShowTemplates(false);
    toast("info", `Loaded template: ${tmpl.name}`);
  };

  const handleScheduleSend = async () => {
    const ts = new Date(scheduleAt).getTime() / 1000;
    if (!ts || ts <= Date.now() / 1000) {
      toast("error", "Pick a future time");
      return;
    }
    try {
      const data = await fetchWithAuth("/api/schedule", {
        method: "POST",
        body: JSON.stringify({
          to: to.trim(),
          subject: subject.trim(),
          body: body.trim(),
          send_at: ts,
          service,
        }),
      });
      if (data.success) {
        toast(
          "success",
          `Scheduled for ${new Date(scheduleAt).toLocaleString()}`,
        );
        setScheduleAt("");
        setShowSchedule(false);
      } else {
        toast("error", data.error || "Schedule failed");
      }
    } catch (err: unknown) {
      toast("error", err instanceof Error ? err.message : "Schedule failed");
    }
  };

  const handleSelectContact = (contact: any) => {
    const parts = to.split(/[,;]/);
    parts[parts.length - 1] = contact.email;
    setTo(parts.join(", "));
    setShowContactSuggestions(false);
  };

  const defaultServices =
    services.length > 0 ? services.find((s) => s.name === "default") : null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Compose Email
          </h2>
          <p className="text-slate-400">Send via any configured provider</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="border-slate-700 text-slate-300 hover:bg-slate-800"
            onClick={() => setShowDrafts((d) => !d)}
          >
            <FileText className="h-4 w-4 mr-1" /> Drafts ({drafts.length})
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="border-slate-700 text-slate-300 hover:bg-slate-800"
            onClick={() => setShowTemplates((t) => !t)}
          >
            <BookTemplate className="h-4 w-4 mr-1" /> Templates (
            {templates.length})
          </Button>
        </div>
      </div>

      {/* Drafts panel */}
      {showDrafts && (
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-white text-sm">Saved Drafts</CardTitle>
          </CardHeader>
          <CardContent>
            {drafts.length === 0 ? (
              <p className="text-slate-500 text-sm italic">No drafts</p>
            ) : (
              <div className="space-y-1">
                {drafts.map((d) => (
                  <div
                    key={d.id}
                    className="flex items-center justify-between py-2 px-3 rounded hover:bg-slate-900/50 transition-colors"
                  >
                    <button
                      className="flex-1 text-left text-sm text-slate-300 hover:text-white truncate"
                      onClick={() => loadDraft(d)}
                    >
                      <span className="font-medium">
                        {d.subject || "(no subject)"}
                      </span>
                      <span className="text-slate-500 ml-2 text-xs">
                        → {d.to || "no recipient"}
                      </span>
                    </button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 text-slate-600 hover:text-red-400"
                      onClick={() => handleDeleteDraft(d.id)}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Templates panel */}
      {showTemplates && (
        <Card className="border-indigo-800 bg-indigo-950/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-white text-sm">
              Email Templates
            </CardTitle>
          </CardHeader>
          <CardContent>
            {templates.length === 0 ? (
              <div className="text-sm text-slate-500">
                No templates yet. Save a template from Settings.
              </div>
            ) : (
              <div className="space-y-1">
                {templates.map((t) => (
                  <div
                    key={t.id}
                    className="flex items-center justify-between py-2 px-3 rounded hover:bg-slate-900/50 transition-colors cursor-pointer"
                    onClick={() => handleTemplateSelect(t)}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-300 truncate">
                        {t.name}
                      </p>
                      <p className="text-xs text-slate-500 truncate">
                        {t.subject || "(no subject)"}{" "}
                        {t.category ? `· [${t.category}]` : ""}
                      </p>
                    </div>
                    <BookTemplate className="h-4 w-4 text-indigo-400 shrink-0 ml-2" />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-white text-base">New Message</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-3">
            <Label className="text-slate-300 w-16 shrink-0">From</Label>
            <select
              className="bg-slate-900 border border-slate-700 text-white text-sm rounded px-3 py-1.5 w-64"
              value={service}
              onChange={(e) => setService(e.target.value)}
            >
              <option value="default">
                {defaultServices
                  ? `default (${defaultServices.type})`
                  : "default"}
              </option>
              {services
                .filter((s) => s.name !== "default")
                .map((s) => (
                  <option key={s.name} value={s.name}>
                    {s.name} ({s.type})
                  </option>
                ))}
            </select>
          </div>
          <div className="flex items-center gap-3 relative">
            <Label className="text-slate-300 w-16 shrink-0">To</Label>
            <Input
              className="bg-slate-900 border-slate-700 text-white flex-1"
              placeholder="recipient@example.com"
              value={to}
              onChange={(e) => setTo(e.target.value)}
              ref={toRef}
              onFocus={() => {
                if (contactSuggestions.length) setShowContactSuggestions(true);
              }}
              onBlur={() =>
                setTimeout(() => setShowContactSuggestions(false), 200)
              }
            />
            {showContactSuggestions && (
              <div className="absolute left-16 top-full mt-1 w-64 bg-slate-900 border border-slate-700 rounded-md shadow-xl z-50 max-h-[200px] overflow-y-auto">
                {contactSuggestions.map((c: any) => (
                  <div
                    key={c.id}
                    className="flex items-center gap-2 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800 cursor-pointer"
                    onClick={() => handleSelectContact(c)}
                    onMouseDown={(e) => e.preventDefault()}
                  >
                    <User className="h-3 w-3 text-blue-400 shrink-0" />
                    <span className="truncate">{c.name || c.email}</span>
                    <span className="text-xs text-slate-500 ml-auto">
                      {c.email}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="flex items-center gap-3">
            <Label className="text-slate-300 w-16 shrink-0">CC</Label>
            <Input
              className="bg-slate-900 border-slate-700 text-white flex-1"
              placeholder="optional, comma-separated"
              value={cc}
              onChange={(e) => setCc(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-3">
            <Label className="text-slate-300 w-16 shrink-0">BCC</Label>
            <Input
              className="bg-slate-900 border-slate-700 text-white flex-1"
              placeholder="optional, comma-separated"
              value={bcc}
              onChange={(e) => setBcc(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-3">
            <Label className="text-slate-300 w-16 shrink-0">Subject</Label>
            <div className="flex flex-1 gap-2">
              <Input
                className="bg-slate-900 border-slate-700 text-white flex-1"
                placeholder="Subject line"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
              />
              <Button
                variant="outline"
                size="sm"
                className="border-slate-700 text-slate-300 hover:bg-slate-800 shrink-0"
                onClick={suggestSubject}
                disabled={!body.trim() || suggesting}
                title="AI subject suggestion"
              >
                {suggesting ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Wand2 className="h-3.5 w-3.5" />
                )}
              </Button>
            </div>
          </div>

          <div className="flex gap-3">
            <Label className="text-slate-300 w-16 shrink-0 pt-2">Body</Label>
            <div className="flex-1 space-y-2">
              <div className="flex gap-2 items-center">
                <label className="flex items-center gap-1 text-xs text-slate-400 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={useHtml}
                    onChange={(e) => setUseHtml(e.target.checked)}
                    className="accent-blue-500"
                  />
                  HTML
                </label>
              </div>
              {useHtml ? (
                <textarea
                  className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-sm text-white resize-y min-h-[200px] focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
                  placeholder="<h1>Title</h1>&#10;<p>Your HTML content...</p>"
                  value={htmlBody}
                  onChange={(e) => setHtmlBody(e.target.value)}
                />
              ) : (
                <textarea
                  className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-sm text-white resize-y min-h-[200px] focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="Write your email..."
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                />
              )}
            </div>
          </div>

          {/* AI Improve Panel */}
          {!useHtml && body.trim() && (
            <Card className="border-purple-900/30 bg-purple-950/10">
              <CardHeader className="pb-2 pt-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-purple-400" />
                  <CardTitle className="text-white text-sm">
                    AI Improve
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <Label className="text-slate-400 text-xs">Style</Label>
                    <select
                      className="bg-slate-900 border border-slate-700 text-white text-xs rounded px-2 py-1.5 w-full mt-1"
                      value={improveStyle}
                      onChange={(e) => setImproveStyle(e.target.value)}
                    >
                      {STYLES.map((s) => (
                        <option key={s.value} value={s.value}>
                          {s.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <Label className="text-slate-400 text-xs">Length</Label>
                    <select
                      className="bg-slate-900 border border-slate-700 text-white text-xs rounded px-2 py-1.5 w-full mt-1"
                      value={improveLength}
                      onChange={(e) => setImproveLength(e.target.value)}
                    >
                      {LENGTHS.map((s) => (
                        <option key={s.value} value={s.value}>
                          {s.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <Label className="text-slate-400 text-xs">Mood</Label>
                    <select
                      className="bg-slate-900 border border-slate-700 text-white text-xs rounded px-2 py-1.5 w-full mt-1"
                      value={improveMood}
                      onChange={(e) => setImproveMood(e.target.value)}
                    >
                      {MOODS.map((s) => (
                        <option key={s.value} value={s.value}>
                          {s.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500">Model:</span>
                    <select
                      className="bg-slate-900 border border-slate-700 text-white text-xs rounded px-2 py-1"
                      disabled
                    >
                      <option>From Settings</option>
                    </select>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 text-slate-500 hover:text-white"
                      onClick={loadProviders}
                      disabled={loadingProviders}
                      title="Refresh providers"
                    >
                      <RefreshCw
                        className={`h-3 w-3 ${loadingProviders ? "animate-spin" : ""}`}
                      />
                    </Button>
                  </div>
                  <Button
                    size="sm"
                    className="bg-purple-600 hover:bg-purple-700 text-xs h-7"
                    onClick={handleImprove}
                    disabled={improving || !body.trim()}
                  >
                    {improving ? (
                      <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                    ) : (
                      <Sparkles className="h-3 w-3 mr-1" />
                    )}
                    Improve
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Expander Panel — short note to full email */}
          {!useHtml && (
            <Card className="border-amber-900/30 bg-amber-950/10">
              <CardHeader className="pb-2 pt-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-amber-400" />
                  <CardTitle className="text-white text-sm">
                    Expander — short note to full email
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <textarea
                  className="w-full bg-slate-900 border border-amber-800/50 rounded-md px-3 py-2 text-sm text-white resize-y min-h-[60px] focus:outline-none focus:ring-1 focus:ring-amber-500"
                  placeholder='e.g. "In Venice for the Biennale. Weather nice, prices high."'
                  value={expandNote}
                  onChange={(e) => setExpandNote(e.target.value)}
                />
                <div className="grid grid-cols-4 gap-3">
                  <div>
                    <Label className="text-slate-400 text-xs">Style</Label>
                    <select
                      className="bg-slate-900 border border-slate-700 text-white text-xs rounded px-2 py-1.5 w-full mt-1"
                      value={expandStyle}
                      onChange={(e) => setExpandStyle(e.target.value)}
                    >
                      {[
                        "humorous",
                        "dramatic",
                        "absurd",
                        "poetic",
                        "dry",
                        "enthusiastic",
                      ].map((s) => (
                        <option key={s}>{s}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <Label className="text-slate-400 text-xs">Length</Label>
                    <select
                      className="bg-slate-900 border border-slate-700 text-white text-xs rounded px-2 py-1.5 w-full mt-1"
                      value={expandLength}
                      onChange={(e) => setExpandLength(e.target.value)}
                    >
                      {["short", "medium", "long", "epic"].map((s) => (
                        <option key={s}>{s}</option>
                      ))}
                    </select>
                  </div>
                  <div className="col-span-2">
                    <Label className="text-slate-400 text-xs">
                      Context (adds fictional details)
                    </Label>
                    <select
                      className="bg-slate-900 border border-slate-700 text-white text-xs rounded px-2 py-1.5 w-full mt-1"
                      value={expandContext}
                      onChange={(e) => setExpandContext(e.target.value)}
                    >
                      <option value="none">None — just expand</option>
                      <option value="venice">Venice Biennale</option>
                      <option value="mars">Elon's Mars Colony</option>
                      <option value="castle">Medieval Castle</option>
                      <option value="underwater">Underwater Base</option>
                      <option value="space">Space Station</option>
                      <option value="wildwest">Wild West Frontier</option>
                    </select>
                  </div>
                </div>
                <div className="flex justify-end">
                  <Button
                    size="sm"
                    className="bg-amber-600 hover:bg-amber-700 text-xs h-7"
                    onClick={handleExpand}
                    disabled={expanding || !expandNote.trim()}
                  >
                    {expanding ? (
                      <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                    ) : (
                      <Sparkles className="h-3 w-3 mr-1" />
                    )}
                    Expand
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Bulk Send Toggle */}
          <div className="flex justify-end">
            <button
              className={`text-xs px-2.5 py-1 rounded border transition-colors ${showBulk ? "border-red-800 text-red-300 bg-red-950/20" : "border-slate-700 text-slate-400 hover:text-slate-200"}`}
              onClick={() => setShowBulk(!showBulk)}
            >
              {showBulk ? "Hide Bulk Send" : "Bulk Send"}
            </button>
          </div>

          {showBulk && (
            <Card className="border-red-900/30 bg-red-950/10">
              <CardHeader className="pb-2 pt-3">
                <div className="flex items-center gap-2">
                  <Send className="h-4 w-4 text-red-400" />
                  <CardTitle className="text-white text-sm">
                    Bulk Send
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <Label className="text-slate-400 text-xs">
                    Recipients — one per line or comma-separated
                  </Label>
                  <textarea
                    className="w-full bg-slate-900 border border-red-800/30 rounded-md px-3 py-2 text-sm text-white resize-y min-h-[80px] mt-1"
                    placeholder="alice@example.com&#10;bob@example.com&#10;carol@example.com"
                    value={bulkRecipients}
                    onChange={(e) => setBulkRecipients(e.target.value)}
                  />
                  {parseCount > 0 && (
                    <p className="text-xs text-slate-500 mt-1">
                      {parseCount} recipient{parseCount !== 1 ? "s" : ""}{" "}
                      parsed.{" "}
                      {parseCount > 25 ? (
                        <span className="text-amber-400">
                          Large batch — review carefully.
                        </span>
                      ) : (
                        ""
                      )}
                    </p>
                  )}
                </div>
                {parseCount > 10 && (
                  <div className="p-2 bg-red-950/30 rounded border border-red-800/30">
                    <p className="text-xs text-red-300">
                      ⚠ Sending unsolicited bulk email (spam) is illegal under
                      CAN-SPAM Act, GDPR, UK PECR, and many other laws. Only
                      proceed if you have <strong>explicit consent</strong> from
                      every recipient. You are responsible for compliance.
                    </p>
                    <label className="flex items-center gap-1 text-xs text-slate-300 cursor-pointer mt-1">
                      <input
                        type="checkbox"
                        checked={bulkConfirmed}
                        onChange={(e) => setBulkConfirmed(e.target.checked)}
                        className="accent-red-500"
                      />
                      I confirm I have consent to email these recipients
                    </label>
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500">
                    Uses current subject, body, and service
                  </span>
                  <Button
                    size="sm"
                    className="bg-red-600 hover:bg-red-700 text-xs h-7"
                    onClick={handleBulkSend}
                    disabled={
                      bulkSending ||
                      parseCount === 0 ||
                      (parseCount > 10 && !bulkConfirmed)
                    }
                  >
                    {bulkSending ? (
                      <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                    ) : (
                      <Send className="h-3 w-3 mr-1" />
                    )}
                    Send to {parseCount} recipient{parseCount !== 1 ? "s" : ""}
                  </Button>
                </div>
                {bulkResult && (
                  <div
                    className={`text-xs px-2 py-1.5 rounded ${bulkResult.ok ? "text-emerald-400 bg-emerald-950/30 border border-emerald-900/30" : "text-red-400 bg-red-950/30 border border-red-900/30"}`}
                  >
                    {bulkResult.msg}
                    {bulkResult.results &&
                      bulkResult.results.filter((r) => !r.success).length >
                        0 && (
                        <div className="mt-1 max-h-[100px] overflow-y-auto">
                          {bulkResult.results
                            .filter((r) => !r.success)
                            .map((r) => (
                              <div key={r.to} className="text-xs text-red-400">
                                {r.to}: {r.error || "failed"}
                              </div>
                            ))}
                        </div>
                      )}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {result && (
            <div
              className={`flex items-center gap-2 text-sm px-3 py-2 rounded border ${result.ok ? "text-emerald-400 border-emerald-900 bg-emerald-950/30" : "text-red-400 border-red-900 bg-red-950/30"}`}
            >
              {result.ok ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : (
                <AlertCircle className="h-4 w-4" />
              )}
              {result.msg}
            </div>
          )}

          {showSchedule && (
            <div className="flex gap-2 items-center pt-1">
              <Label className="text-slate-400 text-xs">Send at</Label>
              <input
                type="datetime-local"
                className="bg-slate-900 border border-slate-700 text-white text-xs rounded px-2 py-1.5"
                value={scheduleAt}
                onChange={(e) => setScheduleAt(e.target.value)}
              />
              <Button
                size="sm"
                className="bg-amber-600 hover:bg-amber-700 text-xs h-7"
                onClick={handleScheduleSend}
                disabled={!scheduleAt}
              >
                <Clock className="h-3 w-3 mr-1" /> Schedule
              </Button>
            </div>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="ghost"
              size="sm"
              className="text-slate-500 hover:text-white text-xs h-7"
              onClick={() => setShowSchedule(!showSchedule)}
            >
              <Clock className="h-3 w-3 mr-1" />{" "}
              {showSchedule ? "Hide Schedule" : "Schedule"}
            </Button>
            <Button
              variant="outline"
              className="border-slate-700 text-slate-300 hover:bg-slate-800"
              onClick={() => {
                setTo("");
                setCc("");
                setBcc("");
                setSubject("");
                setBody("");
                setHtmlBody("");
                setResult(null);
                setDraftId(null);
              }}
            >
              Clear
            </Button>
            <Button
              variant="outline"
              className="border-slate-700 text-slate-300 hover:bg-slate-800"
              onClick={handleSaveDraft}
              disabled={saving}
            >
              {saving ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Save className="h-4 w-4 mr-2" />
              )}
              Save Draft
            </Button>
            <Button
              className="bg-blue-600 hover:bg-blue-700"
              onClick={handleSend}
              disabled={
                sending || !to.trim() || !subject.trim() || !body.trim()
              }
            >
              {sending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Send className="h-4 w-4 mr-2" />
              )}
              Send
            </Button>
          </div>
          {signature && (
            <p className="text-xs text-slate-500 border-t border-slate-800 pt-2 mt-2">
              Signature: {signature.slice(0, 80)}...
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
