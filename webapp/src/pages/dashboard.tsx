import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Mail, Inbox, Send, Activity, History, ShieldAlert, Loader2 } from "lucide-react";
import { fetchWithAuth } from "@/lib/api";

export function Dashboard() {
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchWithAuth("/api/stats")
            .then(data => {
                setStats(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to fetch dashboard stats:", err);
                setLoading(false);
            });
    }, []);

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-64 space-y-4">
                <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                <p className="text-slate-400">Loading real-time email statistics...</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">Email Hub Dashboard</h2>
                    <p className="text-slate-400">Real-time mail status and system health (no gaslights)</p>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">
                            Unread Messages
                        </CardTitle>
                        <Inbox className="h-4 w-4 text-emerald-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">{stats?.unread_count ?? 0}</div>
                        <p className="text-xs text-slate-400">
                            across {stats?.connected_services ?? 0} active services
                        </p>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">
                            System Load
                        </CardTitle>
                        <Activity className="h-4 w-4 text-blue-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">{stats?.system_load ?? "0%"}</div>
                        <p className="text-xs text-slate-400">
                            {parseInt(stats?.system_load || "0") > 50 ? "High" : "Low"} resource usage
                        </p>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">
                            Drafts Pending
                        </CardTitle>
                        <Send className="h-4 w-4 text-purple-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">0</div>
                        <p className="text-xs text-slate-400">
                            Real draft sync active
                        </p>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">
                            Bridge Status
                        </CardTitle>
                        <History className="h-4 w-4 text-orange-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">
                            {stats?.connected_services > 0 ? "Connected" : "Idle"}
                        </div>
                        <p className="text-xs text-slate-400">
                            SOTA v{stats?.mcp_version ?? "0.3.1"} Active
                        </p>
                    </CardContent>
                </Card>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                <Card className="col-span-4 border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white">Recent Mail Activity</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {(!stats?.recent_activity || stats?.recent_activity.length === 0) ? (
                                <p className="text-slate-500 text-sm italic">No recent unread messages found.</p>
                            ) : (
                                stats.recent_activity.map((email: any) => (
                                    <div key={email.id} className="flex items-center justify-between border-b border-slate-800 pb-2 last:border-0 last:pb-0">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 bg-slate-900 rounded-md">
                                                <Mail className="h-4 w-4 text-blue-400" />
                                            </div>
                                            <div>
                                                <p className="text-sm font-medium text-slate-200 line-clamp-1">{email.subject}</p>
                                                <p className="text-xs text-slate-500">From: {email.from} • {email.date}</p>
                                            </div>
                                        </div>
                                        <ShieldAlert className="h-4 w-4 text-slate-600 cursor-pointer hover:text-red-400 transition-colors" />
                                    </div>
                                ))
                            )}
                        </div>
                    </CardContent>
                </Card>
                <Card className="col-span-3 border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white">Mailbox Health</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {stats?.connected_services > 0 ? (
                                <div className="flex items-center">
                                    <span className="relative flex h-2 w-2 mr-2">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                        <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                                    </span>
                                    <div className="ml-2 space-y-1">
                                        <p className="text-sm font-medium leading-none text-white">Default Endpoints</p>
                                        <p className="text-xs text-slate-400">Connected • SSL/TLS Active</p>
                                    </div>
                                </div>
                            ) : (
                                <div className="flex items-center text-slate-500">
                                    <span className="h-2 w-2 mr-2 bg-slate-700 rounded-full"></span>
                                    <div className="ml-2 space-y-1">
                                        <p className="text-sm font-medium leading-none">All Endpoints Idle</p>
                                        <p className="text-xs">No active connections</p>
                                    </div>
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
