import {
	AlertCircle,
	CheckCircle2,
	Cpu,
	Globe,
	Key,
	Loader2,
	Radio,
	Server,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useToast } from "@/components/toast";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { fetchWithAuth } from "@/lib/api";

type Provider = {
	id: string;
	name: string;
	endpoint: string | null;
	available: boolean | null;
	models: string[];
};

type GpuInfo = {
	detected: boolean;
	name?: string;
	vram?: string;
	driver?: string;
};

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

export function Settings() {
	const { toast } = useToast();

	// ── AI Provider state ──
	const [providers, setProviders] = useState<Provider[]>([]);
	const [gpu, setGpu] = useState<GpuInfo>({ detected: false });
	const [loadingProviders, setLoadingProviders] = useState(true);
	const [selectedProvider, setSelectedProvider] = useState("");
	const [selectedModel, setSelectedModel] = useState("");
	const [customEndpoint, setCustomEndpoint] = useState("");
	const [apiKey, setApiKey] = useState("");
	const [saving, setSaving] = useState(false);
	const [saveResult, setSaveResult] = useState<{
		ok: boolean;
		msg: string;
	} | null>(null);
	const [testResult, setTestResult] = useState<{
		ok: boolean;
		msg: string;
	} | null>(null);
	const [testing, setTesting] = useState(false);

	// ── Email Service state ──
	const [emailServices, setEmailServices] = useState<ServiceMap>({});
	const [smtpServer, setSmtpServer] = useState("");
	const [smtpPort, setSmtpPort] = useState("587");
	const [smtpUser, setSmtpUser] = useState("");
	const [smtpPassword, setSmtpPassword] = useState("");
	const [imapServer, setImapServer] = useState("");
	const [imapPort, setImapPort] = useState("993");
	const [savingEmail, setSavingEmail] = useState(false);
	const [serviceName, setServiceName] = useState("default");
	const [serviceType, setServiceType] = useState("smtp");
	const [_showEmailForm, _setShowEmailForm] = useState(true);
	const [oauthConfigured, setOauthConfigured] = useState(false);
	const [oauthAuthorized, setOauthAuthorized] = useState(false);
	const [oauthAccount, setOauthAccount] = useState("");
	const [oauthScope, setOauthScope] = useState<"exchange" | "graph">(
		"exchange",
	);
	const [oauthFamilies, setOauthFamilies] = useState<
		Record<string, { authorized: boolean }>
	>({});
	const [flow, setFlow] = useState<{
		device_code: string;
		user_code: string;
		verification_uri: string;
		interval: number;
	} | null>(null);
	const oauthTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

	// ── Load AI providers ──
	useEffect(() => {
		fetchWithAuth("/api/llm/models")
			.then((data) => {
				const list: Provider[] = data.providers || [];
				const gpuInfo: GpuInfo = data.gpu || { detected: false };
				setProviders(list);
				setGpu(gpuInfo);
				const local = list.find((p) => p.available === true);
				const first = local || list[0];
				if (first) {
					setSelectedProvider(first.id);
					setSelectedModel(first.models[0] || "");
					setCustomEndpoint(first.endpoint || "");
				}
			})
			.catch(() => {})
			.finally(() => setLoadingProviders(false));
	}, []);

	// ── Load email services ──
	useEffect(() => {
		fetchWithAuth("/api/services")
			.then((data) => setEmailServices(data.services || {}))
			.catch(() => {});
	}, []);

	const currentProvider = providers.find((p) => p.id === selectedProvider);

	// Filter out non-chat models (embeddings, re-rank, etc.)
	const chatModels = (currentProvider?.models || []).filter(
		(m) =>
			!m.toLowerCase().includes("embedding") &&
			!m.toLowerCase().includes("rerank"),
	);

	const handleProviderChange = (id: string) => {
		setSelectedProvider(id);
		const p = providers.find((pr) => pr.id === id);
		if (p) {
			const filtered = p.models.filter(
				(m: string) =>
					!m.toLowerCase().includes("embedding") &&
					!m.toLowerCase().includes("rerank"),
			);
			setSelectedModel(filtered[0] || p.models[0] || "");
			setCustomEndpoint(p.endpoint || "");
		}
		setSaveResult(null);
	};

	const handleSave = async () => {
		setSaving(true);
		setSaveResult(null);
		try {
			const data = await fetchWithAuth("/api/llm/configure", {
				method: "POST",
				body: JSON.stringify({
					provider: selectedProvider,
					model: selectedModel,
					endpoint: customEndpoint || undefined,
					api_key: apiKey || undefined,
				}),
			});
			if (data.success) {
				setSaveResult({
					ok: true,
					msg: `Saved: ${selectedProvider} / ${selectedModel}`,
				});
				toast("success", `AI provider set to ${selectedProvider}`);
			} else {
				setSaveResult({ ok: false, msg: data.error || "Save failed." });
			}
		} catch (err: unknown) {
			setSaveResult({
				ok: false,
				msg: err instanceof Error ? err.message : String(err),
			});
		} finally {
			setSaving(false);
		}
	};

	const handleTest = async () => {
		setTesting(true);
		setTestResult(null);
		try {
			// Save the provider first so the backend uses the right config
			await fetchWithAuth("/api/llm/configure", {
				method: "POST",
				body: JSON.stringify({
					provider: selectedProvider,
					model: selectedModel,
					endpoint: customEndpoint || undefined,
					api_key: apiKey || undefined,
				}),
			});
			// Now test via chat
			const data = await fetchWithAuth("/api/chat", {
				method: "POST",
				body: JSON.stringify({ query: "Respond with exactly: OK" }),
			});
			const resp = (data.response || "").trim();
			const ok = resp.length > 0 && !resp.toLowerCase().startsWith("error");
			setTestResult({
				ok,
				msg: ok
					? `Response: "${resp.slice(0, 80)}"`
					: `Error: ${resp.slice(0, 120)}`,
			});
		} catch (err: unknown) {
			setTestResult({
				ok: false,
				msg: err instanceof Error ? err.message : String(err),
			});
		} finally {
			setTesting(false);
		}
	};

	// ── Email service handlers ──
	const handleSaveEmailService = async () => {
		if (!smtpServer || !smtpUser || !smtpPassword) {
			toast("error", "SMTP Server, User, and Password are required");
			return;
		}
		setSavingEmail(true);
		try {
			const config: Record<string, unknown> = {
				smtp_server: smtpServer,
				smtp_port: parseInt(smtpPort, 10) || 587,
				smtp_user: smtpUser,
				smtp_password: smtpPassword,
				smtp_from: smtpUser,
			};
			if (imapServer) {
				config.imap_server = imapServer;
				config.imap_port = parseInt(imapPort, 10) || 993;
				config.imap_user = smtpUser;
				config.imap_password = smtpPassword;
			}
			const data = await fetchWithAuth("/api/services", {
				method: "POST",
				body: JSON.stringify({ name: serviceName, type: serviceType, config }),
			});
			if (data.success) {
				toast("success", `Email service "${serviceName}" saved`);
				// Refresh service list
				const svcs = await fetchWithAuth("/api/services");
				setEmailServices(svcs.services || {});
			} else {
				toast("error", data.message || data.error || "Save failed");
			}
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "Save failed");
		} finally {
			setSavingEmail(false);
		}
	};

	const stopOAuthPolling = () => {
		if (oauthTimerRef.current) {
			clearInterval(oauthTimerRef.current);
			oauthTimerRef.current = null;
		}
	};

	const cancelOAuthFlow = () => {
		stopOAuthPolling();
		setFlow(null);
	};

	const loadOAuthStatus = useCallback(async () => {
		try {
			const data = await fetchWithAuth("/api/oauth/status");
			setOauthConfigured(data.configured === true);
			setOauthAuthorized(data.authorized === true);
			setOauthAccount(data.account || "");
			setOauthFamilies(data.families || {});
		} catch {
			/* ignore */
		}
	}, []);

	useEffect(() => {
		loadOAuthStatus();
	}, [loadOAuthStatus]);

	const startOAuthFlow = async () => {
		try {
			const data = await fetchWithAuth("/api/oauth/device", {
				method: "POST",
				body: JSON.stringify({ scope: oauthScope }),
			});
			if (!data.success) {
				toast("error", data.error || "OAuth start failed");
				return;
			}
			setFlow(data);
			const intervalMs = Math.max(Number(data.interval || 5) * 1000, 3000);
			oauthTimerRef.current = setInterval(async () => {
				try {
					const poll = await fetchWithAuth("/api/oauth/poll", {
						method: "POST",
						body: JSON.stringify({
							device_code: data.device_code,
							scope: oauthScope,
						}),
					});
					if (poll.status === "authorized") {
						stopOAuthPolling();
						setFlow(null);
						setOauthAuthorized(true);
						setOauthAccount(poll.account || "");
						toast("success", `Outlook authorized as ${poll.account}`);
						loadOAuthStatus();
					} else if (
						poll.status === "declined" ||
						poll.status === "expired" ||
						poll.status === "error"
					) {
						stopOAuthPolling();
						setFlow(null);
						toast("error", poll.error || "OAuth flow failed");
					}
				} catch {
					/* keep polling */
				}
			}, intervalMs);
		} catch {
			toast("error", "OAuth start failed");
		}
	};

	const handleTestEmailService = async () => {
		try {
			const data = await fetchWithAuth("/api/services");
			const svcs = (data.services || {}) as Record<
				string,
				{ connected?: boolean }
			>;
			const connected = Object.values(svcs).some((s) => s.connected === true);
			if (connected) {
				toast("success", "At least one service is connected");
			} else {
				toast("error", "No services connected — check credentials");
			}
		} catch (err: unknown) {
			toast("error", err instanceof Error ? err.message : "Test failed");
		}
	};

	const currentService = emailServices[serviceName];

	return (
		<div className="space-y-6" data-testid="settings-page">
			<div>
				<h2 className="text-2xl font-bold tracking-tight text-white">
					Settings
				</h2>
				<p className="text-slate-400">
					Configure AI provider and email service credentials
				</p>
			</div>

			{/* ── Email Service Credentials ── */}
			<Card className="border-slate-800 bg-slate-950/50">
				<CardHeader>
					<CardTitle className="text-white flex items-center gap-2">
						<Server className="h-4 w-4 text-emerald-400" />
						Email Service Credentials
					</CardTitle>
					<CardDescription className="text-slate-400">
						Enter your SMTP/IMAP user and password to add an email service.
					</CardDescription>
				</CardHeader>
				<CardContent className="space-y-4">
					<div className="flex gap-3 flex-wrap">
						<div className="min-w-[150px] flex-1">
							<Label className="text-slate-300">Service Name</Label>
							<Input
								className="bg-slate-900 border-slate-700 text-white"
								placeholder="e.g. gmail, outlook, default"
								value={serviceName}
								onChange={(e) => setServiceName(e.target.value)}
							/>
						</div>
						<div className="min-w-[120px]">
							<Label className="text-slate-300">Type</Label>
							<select
								className="bg-slate-900 border border-slate-700 text-white text-sm rounded px-3 py-2 w-full"
								value={serviceType}
								onChange={(e) => setServiceType(e.target.value)}
							>
								<option value="smtp">SMTP/IMAP</option>
								<option value="api">API</option>
								<option value="local">Local</option>
								<option value="webhook">Webhook</option>
							</select>
						</div>
					</div>

					{serviceType === "smtp" && (
						<>
							<div className="grid gap-4 md:grid-cols-2">
								<div className="space-y-2">
									<Label className="text-slate-300 flex items-center gap-1">
										<Globe className="h-3 w-3" /> SMTP Server
									</Label>
									<Input
										className="bg-slate-900 border-slate-700 text-white"
										placeholder="smtp.gmail.com"
										value={smtpServer}
										onChange={(e) => setSmtpServer(e.target.value)}
									/>
								</div>
								<div className="space-y-2">
									<Label className="text-slate-300">SMTP Port</Label>
									<Input
										className="bg-slate-900 border-slate-700 text-white"
										placeholder="587"
										value={smtpPort}
										onChange={(e) => setSmtpPort(e.target.value)}
									/>
								</div>
							</div>
							<div className="grid gap-4 md:grid-cols-2">
								<div className="space-y-2">
									<Label className="text-slate-300 flex items-center gap-1">
										<Key className="h-3 w-3" /> SMTP Username
									</Label>
									<Input
										className="bg-slate-900 border-slate-700 text-white"
										placeholder="your.email@gmail.com"
										value={smtpUser}
										onChange={(e) => setSmtpUser(e.target.value)}
									/>
								</div>
								<div className="space-y-2">
									<Label className="text-slate-300">SMTP Password</Label>
									<Input
										type="password"
										className="bg-slate-900 border-slate-700 text-white"
										placeholder="app password"
										value={smtpPassword}
										onChange={(e) => setSmtpPassword(e.target.value)}
									/>
								</div>
							</div>
							<div className="grid gap-4 md:grid-cols-2">
								<div className="space-y-2">
									<Label className="text-slate-300">
										IMAP Server{" "}
										<span className="text-slate-500 text-xs">(optional)</span>
									</Label>
									<Input
										className="bg-slate-900 border-slate-700 text-white"
										placeholder="imap.gmail.com"
										value={imapServer}
										onChange={(e) => setImapServer(e.target.value)}
									/>
								</div>
								<div className="space-y-2">
									<Label className="text-slate-300">IMAP Port</Label>
									<Input
										className="bg-slate-900 border-slate-700 text-white"
										placeholder="993"
										value={imapPort}
										onChange={(e) => setImapPort(e.target.value)}
									/>
								</div>
							</div>
						</>
					)}

					{serviceType === "api" && (
						<p className="text-sm text-slate-500">
							For API services, use the{" "}
							<a href="/services" className="text-blue-400 hover:underline">
								Services page
							</a>{" "}
							to add with full JSON config.
						</p>
					)}
					{serviceType === "webhook" && (
						<p className="text-sm text-slate-500">
							For webhook services, use the{" "}
							<a href="/services" className="text-blue-400 hover:underline">
								Services page
							</a>{" "}
							with a webhook URL.
						</p>
					)}
					{serviceType === "local" && (
						<p className="text-sm text-slate-500">
							For local test services, use the{" "}
							<a href="/services" className="text-blue-400 hover:underline">
								Services page
							</a>{" "}
							to configure MailHog, Mailpit, etc.
						</p>
					)}

					{currentService && (
						<div
							className={`text-xs px-3 py-2 rounded border ${currentService.connected ? "text-emerald-400 border-emerald-900 bg-emerald-950/20" : "text-amber-400 border-amber-900 bg-amber-950/20"}`}
						>
							{currentService.connected ? "Connected" : "Not connected"} —{" "}
							{currentService.type} — {currentService.description}
						</div>
					)}

					<div className="flex gap-2">
						<Button
							className="bg-emerald-600 hover:bg-emerald-700"
							onClick={handleSaveEmailService}
							disabled={savingEmail}
						>
							{savingEmail && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
							<Key className="h-4 w-4 mr-1" /> Save Credentials
						</Button>
						<Button
							variant="outline"
							className="border-slate-700 text-slate-300 hover:bg-slate-800"
							onClick={handleTestEmailService}
						>
							<Radio className="h-4 w-4 mr-1" /> Test Connection
						</Button>
					</div>

					<p className="text-xs text-slate-500">
						Credentials are sent to the backend and configured at runtime. For
						persistent config, set environment variables (see
						docs/configuration.md).
					</p>
				</CardContent>
			</Card>

			{/* ── AI Provider ── */}
			<Card className="border-slate-800 bg-slate-950/50">
				<CardHeader>
					<CardTitle className="text-white flex items-center gap-2">
						<Cpu className="h-4 w-4 text-blue-400" />
						AI Provider
					</CardTitle>
					<CardDescription className="text-slate-400">
						Local LLMs are auto-discovered. Cloud providers need an API key.
					</CardDescription>
				</CardHeader>
				<CardContent className="space-y-5">
					{loadingProviders ? (
						<div className="flex items-center gap-2 text-slate-500">
							<Loader2 className="h-4 w-4 animate-spin" />
							Probing Ollama and LM Studio...
						</div>
					) : (
						<>
							<div
								className="grid grid-cols-2 md:grid-cols-3 gap-3"
								data-testid="llm-provider-select"
							>
								{providers.map((p) => {
									const isSelected = selectedProvider === p.id;
									const statusDot =
										p.available === true
											? "bg-emerald-500"
											: p.available === false
												? "bg-red-500"
												: "bg-slate-600";
									return (
										<button
											type="button"
											key={p.id}
											onClick={() => handleProviderChange(p.id)}
											className={`text-left p-3 rounded-lg border transition-colors ${
												isSelected
													? "border-blue-600 bg-blue-950/30"
													: "border-slate-800 bg-slate-900/50 hover:border-slate-700"
											}`}
										>
											<div className="flex items-center gap-2 mb-1">
												<span className={`h-2 w-2 rounded-full ${statusDot}`} />
												<span className="text-sm font-medium text-white">
													{p.name}
												</span>
											</div>
											<p className="text-xs text-slate-500">
												{p.available === true
													? (() => {
															const chatCount = p.models.filter(
																(m: string) =>
																	!m.toLowerCase().includes("embedding") &&
																	!m.toLowerCase().includes("rerank"),
															).length;
															return `${chatCount} chat model${chatCount !== 1 ? "s" : ""} available`;
														})()
													: p.available === false
														? "Not running"
														: "Cloud — needs API key"}
											</p>
										</button>
									);
								})}
							</div>

							{/* GPU opportunity prompt */}
							{gpu.detected && providers.every((p) => p.available !== true) && (
								<div className="rounded-lg border border-amber-800/50 bg-amber-950/20 p-3">
									<p className="text-sm text-amber-300 font-medium">
										GPU Detected: {gpu.name} ({gpu.vram})
									</p>
									<p className="text-xs text-amber-400/70 mt-1">
										No local LLM running. Install <strong>Ollama</strong> or{" "}
										<strong>LM Studio</strong> to run AI features locally for
										free.
									</p>
								</div>
							)}

							{currentProvider && (
								<div className="space-y-3 pt-1">
									<div className="grid gap-2">
										<Label className="text-slate-300">Model</Label>
										{chatModels.length > 0 ? (
											<select
												data-testid="llm-model-select"
												className="bg-slate-900 border border-slate-700 text-white text-sm rounded px-3 py-1.5"
												value={selectedModel}
												onChange={(e) => setSelectedModel(e.target.value)}
											>
												{chatModels.map((m) => (
													<option key={m}>{m}</option>
												))}
											</select>
										) : currentProvider.models.length > 0 ? (
											<select
												data-testid="llm-model-select"
												className="bg-slate-900 border border-slate-700 text-white text-sm rounded px-3 py-1.5"
												value={selectedModel}
												onChange={(e) => setSelectedModel(e.target.value)}
											>
												{currentProvider.models.map((m) => (
													<option key={m}>{m}</option>
												))}
											</select>
										) : (
											<Input
												className="bg-slate-900 border-slate-700 text-white"
												placeholder="e.g. llama3.1:8b or gpt-4o-mini"
												value={selectedModel}
												onChange={(e) => setSelectedModel(e.target.value)}
											/>
										)}
									</div>

									<div className="grid gap-2">
										<Label className="text-slate-300">
											Endpoint{" "}
											<span className="text-slate-500 text-xs">
												(optional override)
											</span>
										</Label>
										<Input
											className="bg-slate-900 border-slate-700 text-white"
											placeholder={
												currentProvider.endpoint ||
												"http://localhost:11434/api/generate"
											}
											value={customEndpoint}
											onChange={(e) => setCustomEndpoint(e.target.value)}
										/>
									</div>

									{currentProvider.available === null && (
										<div className="grid gap-2">
											<Label className="text-slate-300">API Key</Label>
											<Input
												type="password"
												className="bg-slate-900 border-slate-700 text-white"
												placeholder="sk-... or similar"
												value={apiKey}
												onChange={(e) => setApiKey(e.target.value)}
											/>
											<p className="text-xs text-slate-500">
												Stored in process memory only — not persisted to disk.
											</p>
										</div>
									)}
								</div>
							)}

							{saveResult && (
								<div
									className={`flex items-center gap-2 text-sm px-3 py-2 rounded border ${saveResult.ok ? "text-emerald-400 border-emerald-900 bg-emerald-950/30" : "text-red-400 border-red-900 bg-red-950/30"}`}
								>
									{saveResult.ok ? (
										<CheckCircle2 className="h-4 w-4" />
									) : (
										<AlertCircle className="h-4 w-4" />
									)}
									{saveResult.msg}
								</div>
							)}

							{testResult && (
								<div
									className={`flex items-center gap-2 text-sm px-3 py-2 rounded border ${testResult.ok ? "text-emerald-400 border-emerald-900 bg-emerald-950/30" : "text-red-400 border-red-900 bg-red-950/30"}`}
								>
									{testResult.ok ? (
										<CheckCircle2 className="h-4 w-4" />
									) : (
										<AlertCircle className="h-4 w-4" />
									)}
									{testResult.msg}
								</div>
							)}

							<div className="flex gap-2 pt-1">
								<Button
									className="bg-blue-600 hover:bg-blue-700"
									onClick={handleSave}
									disabled={saving || !selectedModel}
								>
									{saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}{" "}
									Save Provider
								</Button>
								<Button
									variant="outline"
									className="border-slate-700 text-slate-300 hover:bg-slate-800"
									onClick={handleTest}
									disabled={testing}
								>
									{testing ? (
										<Loader2 className="h-4 w-4 mr-2 animate-spin" />
									) : (
										<Radio className="h-4 w-4 mr-2" />
									)}{" "}
									Test Connection
								</Button>
							</div>
						</>
					)}
				</CardContent>
			</Card>
			{/* Outlook OAuth */}
			<Card
				className="border-slate-800 bg-slate-950/50"
				data-testid="oauth-card"
			>
				<CardHeader className="pb-2">
					<CardTitle className="text-white text-sm flex items-center gap-2">
						<Key className="h-4 w-4 text-amber-400" /> Outlook OAuth (XOAUTH2)
					</CardTitle>
					<CardDescription className="text-slate-400">
						Personal Outlook/Hotmail accounts require OAuth2 — Microsoft
						disabled basic auth (app passwords). Device-code flow; tokens stored
						locally.
					</CardDescription>
				</CardHeader>
				<CardContent className="space-y-3">
					{!oauthConfigured && (
						<p className="text-sm text-amber-400">
							Set{" "}
							<code className="text-slate-300">EMAIL_MCP_OAUTH_CLIENT_ID</code>{" "}
							in .env to enable (Azure app registration, personal accounts).
						</p>
					)}
					{oauthConfigured && (
						<div className="flex flex-wrap gap-2">
							{Object.entries(oauthFamilies).map(([fam, st]) => (
								<span
									key={fam}
									className={`text-xs px-2 py-1 rounded-full border ${
										st.authorized
											? "text-emerald-400 border-emerald-900 bg-emerald-950/30"
											: "text-slate-500 border-slate-700 bg-slate-900/40"
									}`}
								>
									{fam}: {st.authorized ? "authorized" : "not connected"}
								</span>
							))}
						</div>
					)}
					{oauthConfigured && oauthAuthorized && (
						<p className="text-sm text-emerald-400 flex items-center gap-2">
							<CheckCircle2 className="h-4 w-4" /> Authorized as {oauthAccount}
						</p>
					)}
					{!flow && oauthConfigured && (
						<div className="flex gap-2">
							<select
								data-testid="oauth-scope"
								className="bg-slate-900 border border-slate-700 text-white text-sm rounded px-2 py-1.5"
								value={oauthScope}
								onChange={(e) =>
									setOauthScope(e.target.value as "exchange" | "graph")
								}
							>
								<option value="exchange">Exchange (IMAP/SMTP)</option>
								<option value="graph">Graph (Mail API)</option>
							</select>
							<Button
								size="sm"
								data-testid="oauth-connect"
								className="bg-blue-600 hover:bg-blue-700"
								onClick={startOAuthFlow}
							>
								{oauthAuthorized ? "Reconnect Outlook" : "Connect Outlook"}
							</Button>
						</div>
					)}
					{flow && (
						<div className="space-y-2" data-testid="oauth-flow">
							<p className="text-sm text-slate-300">
								Open{" "}
								<a
									href={flow.verification_uri}
									target="_blank"
									rel="noreferrer"
									className="text-blue-400 underline"
								>
									{flow.verification_uri}
								</a>{" "}
								and enter code{" "}
								<span
									className="font-mono text-white bg-slate-800 px-2 py-0.5 rounded"
									data-testid="oauth-user-code"
								>
									{flow.user_code}
								</span>
							</p>
							<p className="text-sm text-slate-400 flex items-center gap-2">
								<Loader2 className="h-3.5 w-3.5 animate-spin" /> Waiting for
								authorization...
							</p>
							<Button
								size="sm"
								variant="outline"
								className="border-slate-700 text-slate-300"
								onClick={cancelOAuthFlow}
							>
								Cancel
							</Button>
						</div>
					)}
				</CardContent>
			</Card>
		</div>
	);
}
