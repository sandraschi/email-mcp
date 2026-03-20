import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { HelpCircle, Terminal, Mail, User2, ShieldCheck, Zap } from "lucide-react";

export function Help() {
    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold tracking-tight text-white">Email Hub Documentation</h2>
                <p className="text-slate-400">Technical guide for the Email MCP service.</p>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <Zap className="h-5 w-5 text-yellow-500" />
                            <CardTitle className="text-white text-md">Quick Start</CardTitle>
                        </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <p className="text-sm text-slate-300 font-medium">1. Authentication</p>
                            <p className="text-xs text-slate-500">Configure your IMAP/SMTP credentials in the Settings page. Ensure OAuth2 is used for Gmail/Outlook.</p>
                        </div>
                        <div className="space-y-2">
                            <p className="text-sm text-slate-300 font-medium">2. AI Commands</p>
                            <p className="text-xs text-slate-500">Use the AI Command interface to manage emails in natural language (e.g., "Find all bills from last month").</p>
                        </div>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <ShieldCheck className="h-5 w-5 text-emerald-500" />
                            <CardTitle className="text-white text-md">SOTA Compliance</CardTitle>
                        </div>
                    </CardHeader>
                    <CardContent className="text-xs text-slate-400 leading-relaxed">
                        The Email Hub follows the January 2026 SOTA standard for MCP fleet integration:
                        <ul className="list-disc pl-4 mt-2 space-y-1">
                            <li>FastAPI bridge for secure web communication</li>
                            <li>Dual Transport: STDIO and HTTP Streamable</li>
                            <li>Standard port assignment: 10813 (Backend)</li>
                            <li>Real-time status monitoring and tool discovery</li>
                            <li>Skill page: shows MCP skill content (FastMCP 3.1 / Anthropic skill format) so the client/IDE knows how to use the server</li>
                        </ul>
                    </CardContent>
                </Card>

                <Card className="col-span-full border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white text-md">Common Operations</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid gap-4 md:grid-cols-3">
                            <div className="p-3 bg-slate-900/50 rounded-md border border-slate-800">
                                <Mail className="h-4 w-4 text-blue-400 mb-2" />
                                <p className="text-sm font-medium text-slate-200">Retrieval</p>
                                <p className="text-xs text-slate-500">Fetch headers, bodies, and attachments via IMAP.</p>
                            </div>
                            <div className="p-3 bg-slate-900/50 rounded-md border border-slate-800">
                                <User2 className="h-4 w-4 text-purple-400 mb-2" />
                                <p className="text-sm font-medium text-slate-200">Management</p>
                                <p className="text-xs text-slate-500">Move, flag, and archive messages across folders.</p>
                            </div>
                            <div className="p-3 bg-slate-900/50 rounded-md border border-slate-800">
                                <Terminal className="h-4 w-4 text-emerald-400 mb-2" />
                                <p className="text-sm font-medium text-slate-200">API Access</p>
                                <p className="text-xs text-slate-500">Direct JSON-RPC access for custom automation.</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
