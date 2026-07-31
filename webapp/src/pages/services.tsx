// @ts-nocheck

import {
	Eye,
	EyeOff,
	Key,
	Loader2,
	Mail,
	Play,
	Plus,
	Sparkles,
	Trash2,
} from "lucide-react";
import { useEffect, useState } from "react";
import { cn } from "@/common/utils";
import { useToast } from "@/components/toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { fetchWithAuth } from "@/lib/api";

type ServiceMap = Record<
	string,
	{
		type: string;
		enabled: boolean;
		configured: boolean;
		description: string;
		connected?: boolean;
	}
>;
type FieldDef = {
	key: string;
	label: string;
	placeholder: string;
	secret: boolean;
	required?: boolean;
};

const FIELD_DEFS: Record<string, FieldDef[]> = {
	smtp: [
		{
			key: "smtp_server",
			label: "SMTP Server",
			placeholder: "smtp.gmail.com",
			secret: false,
			required: true,
		},
		{ key: "smtp_port", label: "SMTP Port", placeholder: "587", secret: false },
		{
			key: "smtp_user",
			label: "SMTP Username",
			placeholder: "your.email@gmail.com",
			secret: false,
			required: true,
		},
		{
			key: "smtp_password",
			label: "SMTP Password",
			placeholder: "App password or regular password",
			secret: true,
			required: true,
		},
		{
			key: "smtp_from",
			label: "From Address",
			placeholder: "Same as username if blank",
			secret: false,
		},
		{
			key: "imap_server",
			label: "IMAP Server (optional)",
			placeholder: "imap.gmail.com",
			secret: false,
		},
		{ key: "imap_port", label: "IMAP Port", placeholder: "993", secret: false },
		{
			key: "imap_user",
			label: "IMAP User (optional)",
			placeholder: "Same as SMTP user if blank",
			secret: false,
		},
		{
			key: "imap_password",
			label: "IMAP Password (optional)",
			placeholder: "Same as SMTP password if blank",
			secret: true,
		},
	],
	api: [
		{
			key: "api_key",
			label: "API Key",
			placeholder: "sk-... or similar",
			secret: true,
			required: true,
		},
		{
			key: "api_url",
			label: "API URL",
			placeholder: "https://api.sendgrid.com/v3/mail/send",
			secret: false,
			required: true,
		},
		{
			key: "from_email",
			label: "From Email",
			placeholder: "noreply@yourdomain.com",
			secret: false,
			required: true,
		},
		{
			key: "service_type",
			label: "Service Type",
			placeholder: "sendgrid / mailgun / resend / ses",
			secret: false,
		},
	],
	local: [
		{
			key: "smtp_server",
			label: "SMTP Server",
			placeholder: "localhost",
			secret: false,
			required: true,
		},
		{
			key: "smtp_port",
			label: "SMTP Port",
			placeholder: "1025",
			secret: false,
		},
		{
			key: "http_url",
			label: "Web UI URL (optional)",
			placeholder: "http://localhost:8025",
			secret: false,
		},
		{
			key: "service_type",
			label: "Service Type",
			placeholder: "mailhog / mailpit / mailcatcher / inbucket",
			secret: false,
		},
	],
	webhook: [
		{
			key: "webhook_url",
			label: "Webhook URL",
			placeholder: "https://hooks.slack.com/services/...",
			secret: true,
			required: true,
		},
		{
			key: "service_type",
			label: "Service Type",
			placeholder: "slack / discord / telegram",
			secret: false,
		},
	],
};

const SERVICE_TYPE_LABELS: Record<string, string> = {
	smtp: "SMTP / IMAP",
	api: "Transactional API",
	local: "Local Testing",
	webhook: "Webhook",
};

const PRESETS = [
	{
		label: "Gmail",
		type: "smtp",
		prompt:
			"Gmail SMTP/IMAP with App Password. SMTP: smtp.gmail.com:587, IMAP: imap.gmail.com:993. User needs 2FA enabled and an App Password.",
	},
	{
		label: "Outlook",
		type: "smtp",
		prompt:
			"Outlook/Hotmail SMTP/IMAP. SMTP: smtp-mail.outlook.com:587, IMAP: outlook.office365.com:993. Use the full email address as username.",
	},
	{
		label: "Yahoo",
		type: "smtp",
		prompt:
			"Yahoo Mail SMTP/IMAP. SMTP: smtp.mail.yahoo.com:587, IMAP: imap.mail.yahoo.com:993. Use App Password if 2FA enabled.",
	},
	{
		label: "ProtonMail",
		type: "smtp",
		prompt:
			"ProtonMail via local Bridge. SMTP: 127.0.0.1:1025, IMAP: 127.0.0.1:1143. Requires ProtonMail Bridge app running locally.",
	},
	{
		label: "MailHog",
		type: "local",
		prompt:
			"Local MailHog for dev testing. SMTP: localhost:1025, HTTP UI at http://localhost:8025. Docker: docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog",
	},
	{
		label: "SendGrid",
		type: "api",
		prompt:
			"SendGrid transactional email API. API: https://api.sendgrid.com/v3/mail/send. Needs an API Key with Mail Send permission.",
	},
	{
		label: "Mailgun",
		type: "api",
		prompt:
			"Mailgun transactional email API. API: https://api.mailgun.net/v3/YOUR_DOMAIN/messages. Needs API key and verified domain.",
	},
	{
		label: "Slack",
		type: "webhook",
		prompt:
			"Slack incoming webhook. Posts email content as Slack message to a channel. Needs a Slack webhook URL from api.slack.com/apps.",
	},
	{
		label: "Discord",
		type: "webhook",
		prompt:
			"Discord webhook. Sends email as Discord embed. Needs a webhook URL from Server Settings → Integrations.",
	},
];

export function Services() {
	const { toast } = useToast();
	const [services, setServices] = useState<ServiceMap>({});
	const [loading, setLoading] = useState(true);
	const [showAdd, setShowAdd] = useState(false);
	const [newName, setNewName] = useState("");
	const [newType, setNewType] = useState("smtp");
	const [configValues, setConfigValues] = useState<Record<string, string>>({});
	const [adding, setAdding] = useState(false);
	const [testingAdd, setTestingAdd] = useState(false);
	const [fieldErrors, setFieldErrors] = useState<Set<string>>(new Set());
	const [quickProvider, setQuickProvider] = useState<
		"gmail" | "outlook" | null
	>(null);
	const [quickEmail, setQuickEmail] = useState("");
	const [quickPassword, setQuickPassword] = useState("");
	const [quickSettingUp, setQuickSettingUp] = useState(false);
	const [bridgeStatus, setBridgeStatus] = useState<{
		checking: boolean;
		status?: string;
		message?: string;
		bridge_running?: boolean;
		ports_open?: number[];
	}>({ checking: false });

	// Check ProtonMail Bridge status when selected
	useEffect(() => {
		if (quickProvider === "protonmail") {
			setBridgeStatus({ checking: true });
			fetchWithAuth("/api/services/check-bridge")
				.then((d) => setBridgeStatus({ checking: false, ...d }))
				.catch(() =>
					setBridgeStatus({
						checking: false,
						status: "error",
						message: "Could not check Bridge status",
					}),
				);
		} else {
			setBridgeStatus({ checking: false });
		}
	}, [quickProvider]);
	const [deleting, setDeleting] = useState<string | null>(null);
	const [assisting, setAssisting] = useState(false);
	const [aiPrompt, setAiPrompt] = useState("");
	const [showSecrets, setShowSecrets] = useState<Set<string>>(new Set());

	const loadServices = async () => {
		setLoading(true);
		try {
			const data = await fetchWithAuth("/api/services");
			setServices(data.services || {});
		} catch (err: unknown) {
			toast(
				"error",
				err instanceof Error ? err.message : "Failed to load services",
			);
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		loadServices();
		// biome-ignore lint/correctness/useExhaustiveDependencies: loadServices is a stable useCallback; internal fetch deps live in its own deps array
	}, [loadServices]);

	const resetForm = () => {
		setNewName("");
		setNewType("smtp");
		setConfigValues({});
		setFieldErrors(new Set());
		setTestingAdd(false);
		setAiPrompt("");
	};

	const handleTypeChange = (type: string) => {
		setNewType(type);
		setConfigValues({});
		setFieldErrors(new Set());
	};

	const handleAdd = async () => {
		if (!newName.trim()) {
			toast("error", "Service name is required");
			return;
		}
		// Validate required fields
		const requiredFields = fields.filter((f) => f.required);
		const missing: string[] = [];
		const errs = new Set<string>();
		for (const f of requiredFields) {
			if (!configValues[f.key]?.trim()) {
				missing.push(f.label);
				errs.add(f.key);
			}
		}
		if (missing.length > 0) {
			setFieldErrors(errs);
			toast("error", `Fill required field(s): ${missing.join(", ")}`);
			return;
		}
		setFieldErrors(new Set());
		setAdding(true);
		const cfg = getConfigPayload();
		try {
			const data = await fetchWithAuth("/api/services", {
				method: "POST",
				body: JSON.stringify({
					name: newName.trim(),
					type: newType,
					config: cfg,
				}),
			});
			if (data.success) {
				toast("success", `Service ${newName} added`);
				setShowAdd(false);
				resetForm();
				loadServices();
			} else {
				toast("error", data.message || data.error || "Add failed");
			}
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "Add failed");
		} finally {
			setAdding(false);
		}
	};

	const handleTestAdd = async () => {
		if (!newName.trim()) {
			toast("error", "Service name is required");
			return;
		}
		const requiredFields = fields.filter((f) => f.required);
		const missing: string[] = [];
		const errs = new Set<string>();
		for (const f of requiredFields) {
			if (!configValues[f.key]?.trim()) {
				missing.push(f.label);
				errs.add(f.key);
			}
		}
		if (missing.length > 0) {
			setFieldErrors(errs);
			toast("error", `Fill required field(s): ${missing.join(", ")}`);
			return;
		}
		setFieldErrors(new Set());
		setTestingAdd(true);
		const cfg = getConfigPayload();
		try {
			const data = await fetchWithAuth("/api/services", {
				method: "POST",
				body: JSON.stringify({
					name: newName.trim(),
					type: newType,
					config: cfg,
				}),
			});
			if (!data.success) {
				toast("error", data.message || data.error || "Add failed");
				setTestingAdd(false);
				return;
			}
			// Test the new service directly (lightweight, single-service check)
			await new Promise((r) => setTimeout(r, 1000));
			const test = await fetchWithAuth(
				`/api/services/${encodeURIComponent(newName.trim())}/test`,
				{ method: "POST" },
			);
			const svcInfo = test.services?.[newName.trim()];
			if (svcInfo?.connected) {
				toast("success", `${newName} — connected!`);
				setShowAdd(false);
				resetForm();
			} else {
				toast(
					"error",
					`${newName} added but not connected: ${svcInfo?.error || "Check credentials"}`,
				);
			}
			loadServices(); // refresh list in background
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "Test failed");
		} finally {
			setTestingAdd(false);
		}
	};

	const handleAiAssist = async () => {
		if (!aiPrompt.trim()) {
			toast("error", "Describe the service");
			return;
		}
		setAssisting(true);
		try {
			const data = await fetchWithAuth("/api/parse-config", {
				method: "POST",
				body: JSON.stringify({
					description: aiPrompt,
					service_type: newType,
					fields: FIELD_DEFS[newType].map((f) => f.key),
				}),
			});
			const resp = (data.response || "")
				.trim()
				.replace(/^```json\s*|```\s*$/g, "")
				.replace(/^```\s*|```\s*$/g, "");
			try {
				const parsed = JSON.parse(resp);
				if (typeof parsed === "object" && !Array.isArray(parsed)) {
					const filled: Record<string, string> = {};
					for (const field of FIELD_DEFS[newType]) {
						const val = parsed[field.key];
						if (val !== undefined && val !== null) {
							filled[field.key] = String(val);
						}
					}
					if (Object.keys(filled).length > 0) {
						setConfigValues((prev) => ({ ...prev, ...filled }));
						// Auto-fill name if empty
						if (!newName.trim() && parsed.name) {
							setNewName(String(parsed.name));
						}
						toast("success", `Filled ${Object.keys(filled).length} field(s)`);
					} else {
						toast("error", "AI didn't return usable config fields");
					}
				} else {
					toast("error", "AI returned non-object JSON");
				}
			} catch {
				toast("error", "AI didn't return valid JSON. Try being more specific.");
			}
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "AI assist failed");
		} finally {
			setAssisting(false);
		}
	};

	const handleDelete = async (name: string) => {
		if (!window.confirm(`Remove service "${name}"?`)) return;
		setDeleting(name);
		try {
			await fetchWithAuth(`/api/services/${encodeURIComponent(name)}`, {
				method: "DELETE",
			});
			toast("success", `Service ${name} removed`);
			loadServices();
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "Delete failed");
		} finally {
			setDeleting(null);
		}
	};

	const handleTest = async (name: string) => {
		try {
			const data = await fetchWithAuth(`/api/services`);
			const svc = data.services?.[name];
			if (svc?.connected) {
				toast("success", `${name} is connected`);
			} else {
				toast("error", `${name}: ${svc?.error || "Not connected"}`);
			}
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "Test failed");
		}
	};

	const handleQuickSetup = async (
		provider:
			| "gmail"
			| "outlook"
			| "protonmail"
			| "yahoo"
			| "icloud"
			| "zoho"
			| "gmx"
			| "fastmail",
	) => {
		if (!quickEmail.trim() || !quickPassword.trim()) {
			toast("error", "Enter email and password first");
			return;
		}
		setQuickProvider(provider);
		setQuickSettingUp(true);

		// ProtonMail: Bridge or direct SMTP/IMAP requires a paid subscription
		if (provider === "protonmail" && !bridgeStatus.bridge_running) {
			toast(
				"error",
				"ProtonMail SMTP/IMAP requires a paid subscription (Mail Plus €3.99/mo). Free accounts cannot connect via third-party apps.",
			);
			setQuickSettingUp(false);
			return;
		}

		// ProtonMail with Bridge running: use localhost
		if (provider === "protonmail" && bridgeStatus.bridge_running) {
			try {
				const data = await fetchWithAuth("/api/services", {
					method: "POST",
					body: JSON.stringify({
						name: "protonmail",
						type: "smtp",
						config: {
							smtp_server: "127.0.0.1",
							smtp_port: 1025,
							smtp_user: quickEmail.trim(),
							smtp_password: quickPassword,
							smtp_from: quickEmail.trim(),
							imap_server: "127.0.0.1",
							imap_port: 1143,
							imap_user: quickEmail.trim(),
							imap_password: quickPassword,
						},
					}),
				});
				if (data.success) {
					toast("success", "ProtonMail (via Bridge) configured!");
					setQuickEmail("");
					setQuickPassword("");
					setQuickProvider(null);
					loadServices();
				} else {
					toast("error", data.message || data.error || "Setup failed");
				}
			} catch (err: unknown) {
				toast("error", err instanceof Error ? err.message : "Setup failed");
			} finally {
				setQuickSettingUp(false);
			}
			return;
		}

		try {
			const data = await fetchWithAuth("/api/services/quick", {
				method: "POST",
				body: JSON.stringify({
					provider,
					email: quickEmail.trim(),
					password: quickPassword,
				}),
			});
			if (data.success) {
				toast(
					"success",
					`${provider === "gmail" ? "Gmail" : "Outlook"} configured!`,
				);
				setQuickEmail("");
				setQuickPassword("");
				setQuickProvider(null);
				loadServices();
			} else {
				toast("error", data.message || data.error || "Setup failed");
			}
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "Setup failed");
		} finally {
			setQuickSettingUp(false);
		}
	};

	const toggleSecret = (key: string) => {
		setShowSecrets((prev) => {
			const next = new Set(prev);
			if (next.has(key)) next.delete(key);
			else next.add(key);
			return next;
		});
	};

	const fields = FIELD_DEFS[newType] || [];

	return (
		<div className="space-y-6" data-testid="services-page">
			<div className="flex items-center justify-between">
				<div>
					<h2 className="text-2xl font-bold tracking-tight text-white">
						Email Services
					</h2>
					<p className="text-slate-400">Configure and manage email providers</p>
				</div>
				<Button
					className="bg-blue-600 hover:bg-blue-700"
					data-testid="services-add"
					onClick={() => setShowAdd(!showAdd)}
				>
					<Plus className="h-4 w-4 mr-1" /> {showAdd ? "Cancel" : "Add Service"}
				</Button>
			</div>

			{/* Quick Setup */}
			<Card className="border-slate-800 bg-slate-950/50">
				<CardHeader className="pb-2">
					<CardTitle className="text-white text-sm">Quick Setup</CardTitle>
				</CardHeader>
				<CardContent className="space-y-3">
					<p className="text-xs text-slate-500">
						Select a provider, enter your email and password. Server details are
						auto-configured.
					</p>
					<div className="flex gap-2 flex-wrap">
						{[
							{
								id: "gmail",
								label: "Gmail",
								color:
									"border-emerald-700 hover:border-emerald-500 text-emerald-300",
							},
							{
								id: "outlook",
								label: "Outlook",
								color: "border-blue-700 hover:border-blue-500 text-blue-300",
							},
							{
								id: "yahoo",
								label: "Yahoo",
								color:
									"border-purple-700 hover:border-purple-500 text-purple-300",
							},
							{
								id: "icloud",
								label: "iCloud",
								color: "border-slate-600 hover:border-slate-400 text-slate-300",
							},
							{
								id: "protonmail",
								label: "ProtonMail",
								color:
									"border-indigo-700 hover:border-indigo-500 text-indigo-300",
							},
							{
								id: "zoho",
								label: "Zoho",
								color: "border-amber-700 hover:border-amber-500 text-amber-300",
							},
							{
								id: "gmx",
								label: "GMX",
								color: "border-cyan-700 hover:border-cyan-500 text-cyan-300",
							},
							{
								id: "fastmail",
								label: "Fastmail",
								color: "border-rose-700 hover:border-rose-500 text-rose-300",
							},
						].map((p) => (
							<button
								type="button"
								key={p.id}
								className={`text-xs px-3 py-1.5 rounded-md border transition-colors ${quickProvider === p.id ? `${p.color} bg-slate-800/50` : "border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-500"}`}
								onClick={() => setQuickProvider(p.id)}
							>
								{p.label}
							</button>
						))}
					</div>
					{quickProvider === "protonmail" && (
						<div
							className={`text-xs px-3 py-2 rounded border ${bridgeStatus.status === "ready" ? "text-emerald-400 border-emerald-900/30 bg-emerald-950/20" : bridgeStatus.status === "not_installed" ? "text-amber-400 border-amber-900/30 bg-amber-950/20" : bridgeStatus.checking ? "text-slate-400 border-slate-700/30 bg-slate-900/20" : "text-red-400 border-red-900/30 bg-red-950/20"}`}
						>
							{bridgeStatus.checking ? (
								<>
									<Loader2 className="h-3 w-3 mr-1 inline animate-spin" />{" "}
									Checking ProtonMail Bridge...
								</>
							) : bridgeStatus.status === "ready" ? (
								<>
									Bridge running on {bridgeStatus.ports_open?.join(", ")} —
									configure below
								</>
							) : bridgeStatus.status === "not_installed" ? (
								<>
									ProtonMail Bridge not found. Free ProtonMail accounts require
									the{" "}
									<a
										className="text-blue-400 hover:underline"
										href="https://proton.me/mail/bridge"
										target="_blank"
										rel="noopener"
									>
										Bridge app
									</a>{" "}
									for SMTP/IMAP access. Install it, log in, then come back.
								</>
							) : (
								bridgeStatus.message || "Bridge status unknown"
							)}
						</div>
					)}
					{quickProvider && (
						<div className="flex gap-2 items-end flex-wrap">
							<div className="min-w-[220px] flex-1">
								<Label className="text-slate-400 text-xs">
									{quickProvider === "gmail"
										? "Email (requires App Password)"
										: "Email"}
								</Label>
								<Input
									className="bg-slate-900 border-slate-700 text-white mt-1 text-sm"
									placeholder="your@email.com"
									value={quickEmail}
									onChange={(e) => setQuickEmail(e.target.value)}
								/>
							</div>
							<div className="min-w-[180px] flex-1">
								<Label className="text-slate-400 text-xs">
									{quickProvider === "gmail" ? "App Password" : "Password"}
								</Label>
								<div className="relative mt-1">
									<Input
										type="password"
										className="bg-slate-900 border-slate-700 text-white text-sm pr-8"
										placeholder="..."
										value={quickPassword}
										onChange={(e) => setQuickPassword(e.target.value)}
										onKeyDown={(e) =>
											e.key === "Enter" && handleQuickSetup(quickProvider)
										}
									/>
								</div>
							</div>
							<Button
								size="sm"
								className="bg-blue-600 hover:bg-blue-700 h-8 text-xs"
								onClick={() => handleQuickSetup(quickProvider)}
								disabled={
									quickSettingUp || !quickEmail.trim() || !quickPassword.trim()
								}
							>
								{quickSettingUp ? (
									<Loader2 className="h-3 w-3 mr-1 animate-spin" />
								) : (
									<Mail className="h-3 w-3 mr-1" />
								)}
								Set up{" "}
								{quickProvider === "outlook"
									? "Outlook"
									: quickProvider.charAt(0).toUpperCase() +
										quickProvider.slice(1)}
							</Button>
						</div>
					)}
					{quickProvider === "gmail" && (
						<p className="text-xs text-slate-500">
							Gmail requires an{" "}
							<a
								className="text-blue-400 hover:underline"
								href="https://myaccount.google.com/apppasswords"
								target="_blank"
								rel="noopener"
							>
								App Password
							</a>
							. Generate one at myaccount.google.com/apppasswords.
						</p>
					)}
				</CardContent>
			</Card>

			{showAdd && (
				<Card className="border-blue-800 bg-blue-950/20">
					<CardHeader>
						<CardTitle className="text-white text-base">
							Add New Service
						</CardTitle>
					</CardHeader>
					<CardContent className="space-y-4">
						<div className="flex gap-3 flex-wrap">
							<div className="flex-1 min-w-[180px]">
								<Label className="text-slate-300">Service Name</Label>
								<Input
									className="bg-slate-900 border-slate-700 text-white"
									placeholder="e.g. my-gmail"
									value={newName}
									onChange={(e) => setNewName(e.target.value)}
								/>
							</div>
							<div className="min-w-[160px]">
								<Label className="text-slate-300">Type</Label>
								<select
									className="bg-slate-900 border border-slate-700 text-white text-sm rounded px-3 py-2 w-full mt-1"
									value={newType}
									onChange={(e) => handleTypeChange(e.target.value)}
								>
									{Object.entries(SERVICE_TYPE_LABELS).map(([v, l]) => (
										<option key={v} value={v}>
											{l}
										</option>
									))}
								</select>
							</div>
						</div>

						{/* AI Assist */}
						<div className="space-y-2">
							<Label className="text-slate-300 text-xs">Quick presets</Label>
							<div className="flex gap-2 flex-wrap">
								{PRESETS.map((p) => (
									<button
										type="button"
										key={p.label}
										className="text-xs px-2.5 py-1 rounded-md border border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
										onClick={() => {
											handleTypeChange(p.type);
											setAiPrompt(p.prompt);
											setNewName(p.label.toLowerCase().replace(/\s+/g, "-"));
										}}
									>
										{p.label}
									</button>
								))}
							</div>
						</div>
						<div className="flex gap-2 items-end">
							<div className="flex-1">
								<Label className="text-slate-300 text-xs">
									or describe in plain language
								</Label>
								<Input
									className="bg-slate-900 border-slate-700 text-white mt-1"
									placeholder='e.g. "Gmail with app password for sandra.schipral@gmail.com"'
									value={aiPrompt}
									onChange={(e) => setAiPrompt(e.target.value)}
									onKeyDown={(e) => e.key === "Enter" && handleAiAssist()}
								/>
							</div>
							<Button
								variant="outline"
								size="sm"
								className="border-purple-700 text-purple-300 hover:bg-purple-950/30 shrink-0"
								onClick={handleAiAssist}
								disabled={assisting || !aiPrompt.trim()}
							>
								{assisting ? (
									<Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" />
								) : (
									<Sparkles className="h-3.5 w-3.5 mr-1" />
								)}
								AI Auto-fill
							</Button>
						</div>

						{/* Dynamic fields */}
						<div className="grid gap-3 md:grid-cols-2">
							{fields.map((field) => {
								const isSecret = field.secret;
								const show = showSecrets.has(field.key);
								return (
									<div key={field.key}>
										<Label className="text-slate-300 text-xs flex items-center gap-1">
											{isSecret && <Key className="h-3 w-3 text-amber-400" />}
											{field.label}
											{field.required && (
												<span className="text-red-400">*</span>
											)}
										</Label>
										<div className="relative mt-1">
											<Input
												type={isSecret && !show ? "password" : "text"}
												className={cn(
													"pr-8",
													fieldErrors.has(field.key)
														? "border-red-500 bg-red-950/20"
														: "bg-slate-900 border-slate-700 text-white",
												)}
												placeholder={field.placeholder}
												value={configValues[field.key] || ""}
												onChange={(e) => {
													setConfigValues((prev) => ({
														...prev,
														[field.key]: e.target.value,
													}));
													if (fieldErrors.has(field.key)) {
														setFieldErrors((prev) => {
															const n = new Set(prev);
															n.delete(field.key);
															return n;
														});
													}
												}}
											/>
											{isSecret && (
												<button
													type="button"
													className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
													onClick={() => toggleSecret(field.key)}
												>
													{show ? (
														<EyeOff className="h-3.5 w-3.5" />
													) : (
														<Eye className="h-3.5 w-3.5" />
													)}
												</button>
											)}
										</div>
									</div>
								);
							})}
						</div>

						<div className="flex gap-2 pt-1">
							<Button
								className="bg-blue-600 hover:bg-blue-700"
								onClick={handleAdd}
								disabled={adding || testingAdd || !newName.trim()}
							>
								{adding && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
								<Plus className="h-4 w-4 mr-1" /> Add Service
							</Button>
							<Button
								className="bg-emerald-600 hover:bg-emerald-700"
								onClick={handleTestAdd}
								disabled={adding || testingAdd || !newName.trim()}
							>
								{testingAdd ? (
									<Loader2 className="h-4 w-4 mr-2 animate-spin" />
								) : (
									<Play className="h-4 w-4 mr-1" />
								)}
								Test & Save
							</Button>
							<Button
								variant="outline"
								className="border-slate-700 text-slate-300"
								onClick={() => {
									setShowAdd(false);
									resetForm();
								}}
							>
								Cancel
							</Button>
						</div>
					</CardContent>
				</Card>
			)}

			{loading ? (
				<div className="flex items-center justify-center py-12">
					<Loader2 className="h-8 w-8 animate-spin text-blue-500" />
				</div>
			) : Object.keys(services).length === 0 ? (
				<p className="text-slate-500 text-center py-12">
					No services configured.
				</p>
			) : (
				<div className="grid gap-4">
					{Object.entries(services).map(([name, info]) => (
						<Card
							key={name}
							className="border-slate-800 bg-slate-950/50 hover:bg-slate-900/30 transition-colors"
						>
							<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
								<div className="flex items-center gap-3">
									<span
										className={`h-2.5 w-2.5 rounded-full ${typeof info.connected === "boolean" ? (info.connected ? "bg-emerald-500" : "bg-red-500") : "bg-slate-600"}`}
									/>
									<div>
										<CardTitle className="text-white text-sm">{name}</CardTitle>
										<p className="text-xs text-slate-500">
											{info.description || info.type}
										</p>
									</div>
								</div>
								<div className="flex gap-2">
									<Button
										size="sm"
										variant="outline"
										className="border-slate-700 text-slate-300 hover:bg-slate-800 text-xs h-7"
										onClick={() => handleTest(name)}
									>
										<Play className="h-3 w-3 mr-1" /> Test
									</Button>
									{name !== "default" && (
										<Button
											size="sm"
											variant="outline"
											className="border-red-800 text-red-400 hover:bg-red-950/20 text-xs h-7"
											onClick={() => handleDelete(name)}
											disabled={deleting === name}
										>
											{deleting === name ? (
												<Loader2 className="h-3 w-3 animate-spin" />
											) : (
												<Trash2 className="h-3 w-3" />
											)}
										</Button>
									)}
								</div>
							</CardHeader>
						</Card>
					))}
				</div>
			)}
		</div>
	);
}
