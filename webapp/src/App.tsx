import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
	Navigate,
	Route,
	BrowserRouter as Router,
	Routes,
} from "react-router-dom";
import { AppLayout } from "@/components/layout/app-layout";
import { ToastProvider } from "@/components/toast";
import { ApiDocs } from "@/pages/api-docs";
import { AutoRespond } from "@/pages/auto-respond";
import { Chat } from "@/pages/chat";
import { Compose } from "@/pages/compose";
import { Contacts } from "@/pages/contacts";
import { Dashboard } from "@/pages/dashboard";
import { EmailDetail } from "@/pages/email-detail";
import { Help } from "@/pages/help";
import { Inbox } from "@/pages/inbox";
import { Lab } from "@/pages/lab";
import Logs from "@/pages/logs";
import { MailReader } from "@/pages/mail-reader";
import { Rules } from "@/pages/rules";
import { SearchPage } from "@/pages/search";
import { Services } from "@/pages/services";
import { Settings } from "@/pages/settings";
import { Skill } from "@/pages/skill";
import { Tools } from "@/pages/tools";

const queryClient = new QueryClient({
	defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
});

function App() {
	return (
		<QueryClientProvider client={queryClient}>
			<ToastProvider>
				<Router>
					<AppLayout>
						<Routes>
							<Route path="/" element={<Dashboard />} />
							<Route path="/inbox" element={<Inbox />} />
							<Route path="/compose" element={<Compose />} />
							<Route path="/email" element={<EmailDetail />} />
							<Route path="/search" element={<SearchPage />} />
							<Route path="/mail" element={<MailReader />} />
							<Route path="/chat" element={<Chat />} />
							<Route path="/tools" element={<Tools />} />
							<Route path="/services" element={<Services />} />
							<Route path="/lab" element={<Lab />} />
							<Route path="/contacts" element={<Contacts />} />
							<Route path="/auto-respond" element={<AutoRespond />} />
							<Route path="/rules" element={<Rules />} />
							<Route path="/skill" element={<Skill />} />
							<Route path="/api-docs" element={<ApiDocs />} />
							<Route path="/logs" element={<Logs />} />
							<Route path="/help" element={<Help />} />
							<Route path="/settings" element={<Settings />} />
							<Route path="*" element={<Navigate to="/" replace />} />
						</Routes>
					</AppLayout>
				</Router>
			</ToastProvider>
		</QueryClientProvider>
	);
}

export default App;
