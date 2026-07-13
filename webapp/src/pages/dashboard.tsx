import {
	Activity,
	FileText,
	History,
	Inbox,
	Loader2,
	Mail,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchWithAuth } from "@/lib/api";

type Stats = {
	unread_count: number;
	connected_services: number;
	total_services: number;
	configured_services: number;
	tools_count: number;
	drafts_count: number;
	recent_activity: Array<{
		id: string;
		subject: string;
		from: string;
		date: string;
		_service?: string;
	}>;
	mcp_version: string;
	error?: string;
};

export function Dashboard() {
	const navigate = useNavigate();
	const [stats, setStats] = useState<Stats | null>(null);
	const [loading, setLoading] = useState(true);
	const [_refreshKey, setRefreshKey] = useState(0);

	const fetchStats = useCallback(async () => {
		try {
			const data = await fetchWithAuth("/api/stats");
			setStats(data);
		} catch (err) {
			console.error("Failed to fetch dashboard stats:", err);
		} finally {
			setLoading(false);
		}
	}, []);

	useEffect(() => {
		fetchStats();
	}, [fetchStats]);

	// Auto-refresh every 60s
	useEffect(() => {
		const interval = setInterval(() => setRefreshKey((k) => k + 1), 60_000);
		return () => clearInterval(interval);
	}, []);

	if (loading) {
		return (
			<div className="flex flex-col items-center justify-center h-64 space-y-4">
				<Loader2 className="h-8 w-8 animate-spin text-blue-500" />
				<p className="text-slate-400">Loading real-time email statistics...</p>
			</div>
		);
	}

	const connected = (stats?.connected_services ?? 0) > 0;

	return (
		<div className="space-y-6">
			<div className="flex items-center justify-between">
				<div>
					<h2 className="text-2xl font-bold tracking-tight text-white">
						Email Hub Dashboard
					</h2>
					<p className="text-slate-400">
						Real-time mail status and system health
					</p>
				</div>
			</div>

			{/* KPI Cards */}
			<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
				<Card
					className="border-slate-800 bg-slate-950/50 cursor-pointer hover:bg-slate-900/30 transition-colors"
					onClick={() => navigate("/inbox")}
				>
					<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
						<CardTitle className="text-sm font-medium text-slate-200">
							Unread Messages
						</CardTitle>
						<Inbox className="h-4 w-4 text-emerald-500" />
					</CardHeader>
					<CardContent>
						<div className="text-2xl font-bold text-white">
							{stats?.unread_count ?? 0}
						</div>
						<p className="text-xs text-slate-400">
							across {stats?.connected_services ?? 0} active services
						</p>
					</CardContent>
				</Card>

				<Card
					className="border-slate-800 bg-slate-950/50 cursor-pointer hover:bg-slate-900/30 transition-colors"
					onClick={() => navigate("/services")}
				>
					<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
						<CardTitle className="text-sm font-medium text-slate-200">
							Services
						</CardTitle>
						<Activity className="h-4 w-4 text-blue-500" />
					</CardHeader>
					<CardContent>
						<div className="text-2xl font-bold text-white">
							{stats?.configured_services ?? 0}
						</div>
						<p className="text-xs text-slate-400">
							{stats?.connected_services ?? 0} connected of{" "}
							{stats?.total_services ?? 0} registered
						</p>
					</CardContent>
				</Card>

				<Card
					className="border-slate-800 bg-slate-950/50 cursor-pointer hover:bg-slate-900/30 transition-colors"
					onClick={() => navigate("/compose")}
				>
					<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
						<CardTitle className="text-sm font-medium text-slate-200">
							Drafts
						</CardTitle>
						<FileText className="h-4 w-4 text-purple-500" />
					</CardHeader>
					<CardContent>
						<div className="text-2xl font-bold text-white">
							{stats?.drafts_count ?? 0}
						</div>
						<p className="text-xs text-slate-400">Saved locally</p>
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
							{connected ? "Connected" : "Idle"}
						</div>
						<p className="text-xs text-slate-400">
							SOTA v{stats?.mcp_version ?? "0.3.2"} • {stats?.tools_count ?? 0}{" "}
							tools
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
							{!stats?.recent_activity || stats.recent_activity.length === 0 ? (
								<p className="text-slate-500 text-sm italic">
									No recent unread messages found.
								</p>
							) : (
								stats.recent_activity.map((email) => (
									<div
										key={email.id}
										className="flex items-center justify-between border-b border-slate-800 pb-2 last:border-0 last:pb-0 cursor-pointer hover:bg-slate-900/30 px-2 rounded transition-colors"
										onClick={() =>
											navigate(
												`/email?id=${encodeURIComponent(email.id)}&service=${email._service || "default"}&folder=INBOX`,
											)
										}
									>
										<div className="flex items-center gap-3">
											<div className="p-2 bg-slate-900 rounded-md">
												<Mail className="h-4 w-4 text-blue-400" />
											</div>
											<div>
												<p className="text-sm font-medium text-slate-200 line-clamp-1">
													{email.subject}
												</p>
												<p className="text-xs text-slate-500">
													From: {email.from} • {email.date}
												</p>
											</div>
										</div>
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
							{connected ? (
								<div className="space-y-3">
									<div className="flex items-center">
										<span className="relative flex h-2 w-2 mr-2">
											<span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
											<span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
										</span>
										<div className="ml-2 space-y-1">
											<p className="text-sm font-medium leading-none text-white">
												Services Online
											</p>
											<p className="text-xs text-slate-400">
												{stats?.connected_services} of{" "}
												{stats?.configured_services} services connected
											</p>
										</div>
									</div>
								</div>
							) : (
								<div className="flex items-center text-slate-500">
									<span className="h-2 w-2 mr-2 bg-slate-700 rounded-full"></span>
									<div className="ml-2 space-y-1">
										<p className="text-sm font-medium leading-none">
											All Endpoints Idle
										</p>
										<p className="text-xs">
											No active connections — configure services in Settings
										</p>
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
