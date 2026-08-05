import { KeyRound } from "lucide-react";
import { useEffect, useState } from "react";
import { useZoom } from "@/common/use-zoom";
import { fetchWithAuth } from "@/lib/api";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";

// import { Toaster } from '@/components/ui/toaster';

interface AppLayoutProps {
	children: React.ReactNode;
}

function OAuthReauthBanner() {
	const [flow, setFlow] = useState<{
		user_code: string;
		verification_uri: string;
	} | null>(null);
	const [dismissed, setDismissed] = useState(false);

	useEffect(() => {
		let cancelled = false;
		const check = async () => {
			try {
				const data = await fetchWithAuth("/api/oauth/flow");
				if (!cancelled) setFlow(data.pending ? data : null);
			} catch {
				// backend unreachable - skip this poll
			}
		};
		check();
		const t = setInterval(check, 10_000);
		return () => {
			cancelled = true;
			clearInterval(t);
		};
	}, []);

	if (!flow || dismissed) return null;
	return (
		<div
			className="flex items-center justify-between gap-4 border-b border-amber-500/30 bg-amber-500/15 px-6 py-2 text-sm"
			data-testid="oauth-reauth-banner"
		>
			<div className="flex items-center gap-2 text-amber-300">
				<KeyRound className="h-4 w-4 shrink-0" />
				<span>
					Outlook re-auth needed: enter code{" "}
					<strong className="font-mono tracking-widest">
						{flow.user_code}
					</strong>{" "}
					at{" "}
					<a
						href={flow.verification_uri}
						target="_blank"
						rel="noreferrer"
						className="underline underline-offset-2 hover:text-amber-200"
					>
						microsoft.com/devicelogin
					</a>{" "}
					- email access resumes automatically.
				</span>
			</div>
			<button
				type="button"
				onClick={() => setDismissed(true)}
				className="text-amber-400 hover:text-amber-200"
				aria-label="Dismiss reauth banner"
			>
				&times;
			</button>
		</div>
	);
}

export function AppLayout({ children }: AppLayoutProps) {
	const [collapsed, setCollapsed] = useState(false);
	useZoom();

	// Persist sidebar state
	useEffect(() => {
		const stored = localStorage.getItem("sidebar-collapsed");
		if (stored !== null) setCollapsed(stored === "true");
	}, []);

	const handleToggle = () => {
		const newState = !collapsed;
		setCollapsed(newState);
		localStorage.setItem("sidebar-collapsed", String(newState));
	};

	return (
		<div className="flex min-h-screen flex-col bg-slate-950 text-slate-50 font-sans selection:bg-emerald-500/30">
			<div className="flex flex-1 overflow-hidden">
				<Sidebar collapsed={collapsed} onToggle={handleToggle} />
				<div className="flex flex-1 flex-col overflow-hidden">
					<OAuthReauthBanner />
					<Topbar />
					<main className="flex-1 overflow-y-auto p-6 scroll-smooth">
						<div className="mx-auto max-w-7xl animate-in fade-in duration-500">
							{children}
						</div>
					</main>
				</div>
			</div>
			{/* <Toaster /> */}
		</div>
	);
}
