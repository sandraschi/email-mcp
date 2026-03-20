import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Mail, Inbox, Send, Activity, History, ShieldAlert } from "lucide-react";

export function Dashboard() {
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">Email Hub Dashboard</h2>
                    <p className="text-slate-400">Real-time mail status and system health</p>
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
                        <div className="text-2xl font-bold text-white">24</div>
                        <p className="text-xs text-slate-400">
                            across 3 mailboxes
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
                        <div className="text-2xl font-bold text-white">4%</div>
                        <p className="text-xs text-slate-400">
                            Low resource usage
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
                        <div className="text-2xl font-bold text-white">2</div>
                        <p className="text-xs text-slate-400">
                            AI-generated drafts
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
                        <div className="text-2xl font-bold text-white">Connected</div>
                        <p className="text-xs text-slate-400">
                            FastAPI Tunnel Active
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
                            {[1, 2, 3].map((i) => (
                                <div key={i} className="flex items-center justify-between border-b border-slate-800 pb-2 last:border-0 last:pb-0">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 bg-slate-900 rounded-md">
                                            <Mail className="h-4 w-4 text-blue-400" />
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-slate-200">Re: System Architecture Review</p>
                                            <p className="text-xs text-slate-500">From: Steve Schipal • 5m ago</p>
                                        </div>
                                    </div>
                                    <ShieldAlert className="h-4 w-4 text-slate-600 cursor-pointer hover:text-red-400 transition-colors" />
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
                <Card className="col-span-3 border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white">Mailbox Health</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div className="flex items-center">
                                <span className="relative flex h-2 w-2 mr-2">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                                </span>
                                <div className="ml-2 space-y-1">
                                    <p className="text-sm font-medium leading-none text-white">Gmail Endpoint</p>
                                    <p className="text-xs text-slate-400">Connected • SSL/TLS</p>
                                </div>
                            </div>
                            <div className="flex items-center">
                                <span className="relative flex h-2 w-2 mr-2 bg-emerald-500 rounded-full"></span>
                                <div className="ml-2 space-y-1">
                                    <p className="text-sm font-medium leading-none text-white">Custom IMAP</p>
                                    <p className="text-xs text-slate-400">vienna.at • Connected</p>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
