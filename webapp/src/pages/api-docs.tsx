import { BookOpen, Code2, ExternalLink } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const BACKEND_PORT = 10813;
const BACKEND_BASE = `http://localhost:${BACKEND_PORT}`;

const ENDPOINTS = [
	{ method: "GET", path: "/api/status", desc: "Server health" },
	{ method: "GET", path: "/api/capabilities", desc: "Feature flags" },
	{ method: "GET", path: "/api/tools", desc: "List MCP tools" },
	{ method: "GET", path: "/api/stats", desc: "Dashboard KPIs" },
	{ method: "GET", path: "/api/services", desc: "Service list + connectivity" },
	{
		method: "GET",
		path: "/api/inbox",
		desc: "Fetch inbox (service, folder, limit, unread_only)",
	},
	{
		method: "POST",
		path: "/api/send",
		desc: "Send email {to, subject, body, service?}",
	},
	{ method: "GET", path: "/api/skills", desc: "List skill:// resources" },
	{ method: "GET", path: "/api/skills/{name}", desc: "Skill markdown content" },
	{ method: "GET", path: "/api/llm/models", desc: "Probe Ollama / LM Studio" },
	{
		method: "POST",
		path: "/api/llm/configure",
		desc: "Update AI provider at runtime",
	},
	{ method: "POST", path: "/api/chat", desc: "NL query → AI router" },
	{ method: "GET", path: "/mcp", desc: "MCP streamable HTTP transport" },
];

const METHOD_COLOR: Record<string, string> = {
	GET: "text-emerald-400 border-emerald-800 bg-emerald-950/30",
	POST: "text-blue-400 border-blue-800 bg-blue-950/30",
	PUT: "text-amber-400 border-amber-800 bg-amber-950/30",
	DELETE: "text-red-400 border-red-800 bg-red-950/30",
};

export function ApiDocs() {
	const [view, setView] = useState<"swagger" | "redoc">("swagger");

	return (
		<div className="space-y-4" data-testid="api-docs-page">
			<div className="flex items-center justify-between">
				<div>
					<h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
						<Code2 className="h-6 w-6 text-blue-400" />
						API Docs
					</h2>
					<p className="text-slate-400">
						FastAPI auto-generated docs for Email-MCP REST surface
					</p>
				</div>
				<div className="flex gap-2">
					<Button
						variant={view === "swagger" ? "default" : "outline"}
						size="sm"
						data-testid="api-docs-swagger"
						className={
							view === "swagger"
								? "bg-blue-600 hover:bg-blue-700"
								: "border-slate-700 text-slate-300 hover:bg-slate-800"
						}
						onClick={() => setView("swagger")}
					>
						Swagger UI
					</Button>
					<Button
						variant={view === "redoc" ? "default" : "outline"}
						size="sm"
						data-testid="api-docs-redoc"
						className={
							view === "redoc"
								? "bg-blue-600 hover:bg-blue-700"
								: "border-slate-700 text-slate-300 hover:bg-slate-800"
						}
						onClick={() => setView("redoc")}
					>
						ReDoc
					</Button>
					<Button
						variant="outline"
						size="sm"
						className="border-slate-700 text-slate-300 hover:bg-slate-800"
						onClick={() =>
							window.open(
								`${BACKEND_BASE}/${view === "redoc" ? "redoc" : "docs"}`,
								"_blank",
							)
						}
					>
						<ExternalLink className="h-3.5 w-3.5 mr-1" />
						Open in browser
					</Button>
				</div>
			</div>

			{/* Quick-ref endpoint strip */}
			<Card className="border-slate-800 bg-slate-950/50">
				<CardHeader className="pb-2">
					<CardTitle className="text-white text-sm flex items-center gap-2">
						<BookOpen className="h-4 w-4 text-slate-400" />
						Endpoint Reference — port {BACKEND_PORT}
					</CardTitle>
				</CardHeader>
				<CardContent>
					<div className="grid gap-1.5">
						{ENDPOINTS.map((ep) => (
							<div
								key={ep.method + ep.path}
								className="flex items-center gap-3 py-1"
							>
								<span
									className={`text-xs font-mono px-1.5 py-0.5 rounded border w-14 text-center shrink-0 ${METHOD_COLOR[ep.method] || "text-slate-400 border-slate-700"}`}
								>
									{ep.method}
								</span>
								<code className="text-xs text-slate-300 font-mono w-52 shrink-0">
									{ep.path}
								</code>
								<span className="text-xs text-slate-500">{ep.desc}</span>
							</div>
						))}
					</div>
				</CardContent>
			</Card>

			{/* Embedded docs iframe */}
			<Card className="border-slate-800 bg-slate-950/50 overflow-hidden">
				<CardContent className="p-0">
					<iframe
						key={view}
						src={`${BACKEND_BASE}/${view === "redoc" ? "redoc" : "docs"}`}
						className="w-full border-0"
						style={{ height: "70vh", minHeight: 500 }}
						title={view === "redoc" ? "ReDoc" : "Swagger UI"}
						onError={() => {}}
					/>
				</CardContent>
			</Card>
			<p className="text-xs text-slate-600 text-center">
				If the iframe is blank, the backend may not be running on port{" "}
				{BACKEND_PORT}.{" "}
				<a
					href={`${BACKEND_BASE}/docs`}
					target="_blank"
					rel="noreferrer"
					className="text-blue-500 hover:underline"
				>
					Open directly →
				</a>
			</p>
		</div>
	);
}
