import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppLayout } from '@/components/layout/app-layout';
import { ToastProvider } from '@/components/toast';
import { Dashboard } from '@/pages/dashboard';
import { Inbox } from '@/pages/inbox';
import { Compose } from '@/pages/compose';
import { Chat } from '@/pages/chat';
import { Tools } from '@/pages/tools';
import { Help } from '@/pages/help';
import { Skill } from '@/pages/skill';
import { Settings } from '@/pages/settings';
import { ApiDocs } from '@/pages/api-docs';
import { EmailDetail } from '@/pages/email-detail';
import { SearchPage } from '@/pages/search';
import { Services } from '@/pages/services';
import { Lab } from '@/pages/lab';
import { Contacts } from '@/pages/contacts';
import { AutoRespond } from '@/pages/auto-respond';
import { MailReader } from '@/pages/mail-reader';

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
              <Route path="/skill" element={<Skill />} />
              <Route path="/api-docs" element={<ApiDocs />} />
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
