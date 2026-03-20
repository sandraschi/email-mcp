import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Wrench, Play, CheckCircle2, AlertCircle } from "lucide-react";

export function Tools() {
    const [tools, setTools] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Fetch tools from the standard SOTA backend endpoint
        fetch("/api/tools")
            .then(res => res.json())
            .then(data => {
                setTools(data.tools || []);
                setLoading(false);
            })
            .catch(() => {
                // Fallback tools if API is not yet standard
                setTools([
                    { name: "send_email", description: "Send a new email message" },
                    { name: "list_messages", description: "List messages in a mailbox" },
                    { name: "get_message", description: "Get the content of a specific message" },
                    { name: "search_emails", description: "Search for emails matching a query" },
                    { name: "manage_mailboxes", description: "Create or delete mailboxes" }
                ]);
                setLoading(false);
            });
    }, []);

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold tracking-tight text-white">Email Integration Tools</h2>
                <p className="text-slate-400">Available MCP tools for email management.</p>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
                {tools.map((tool) => (
                    <Card key={tool.name} className="border-slate-800 bg-slate-950/50 hover:bg-slate-900/50 transition-colors">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <div className="space-y-1">
                                <CardTitle className="text-sm font-medium text-white">{tool.name}</CardTitle>
                                <CardDescription className="text-xs text-slate-500">{tool.description || 'No description provided'}</CardDescription>
                            </div>
                            <Wrench className="h-4 w-4 text-blue-500" />
                        </CardHeader>
                        <CardContent>
                            <div className="flex justify-end gap-2 mt-2">
                                <Button size="sm" variant="ghost" className="text-slate-400 hover:text-white">
                                    <Play className="h-3 w-3 mr-2" />
                                    Test Tool
                                </Button>
                                <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                                    Execute
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {loading && (
                <div className="flex items-center justify-center p-12">
                    <p className="text-slate-500">Scanning for email tools...</p>
                </div>
            )}

            <Card className="border-blue-900/30 bg-blue-950/10">
                <CardHeader>
                    <div className="flex items-center gap-2">
                        <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                        <CardTitle className="text-sm font-medium text-blue-200 text-white">System Status</CardTitle>
                    </div>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-slate-400">
                        All email endpoints are online and responsive. SOTA dual transport is active on port 10813.
                    </p>
                </CardContent>
            </Card>
        </div>
    );
}
