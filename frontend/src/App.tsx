import { Outlet, Route, Routes, BrowserRouter } from 'react-router-dom';
import { QueryClientProvider, QueryClient, useQuery } from '@tanstack/react-query';
import { SidebarNav } from './components/SidebarNav';
import { TopBar } from './components/TopBar';
import AccountsPage from './routes/Accounts';
import TransactionsPage from './routes/Transactions';
import TransfersPage from './routes/Transfers';
import CategoriesPage from './routes/Categories';
import { computeBalances, sumBalancesByCurrency } from './lib/aggregates';
import { listAccounts, listPostings, listTransfers } from './lib/api';

const queryClient = new QueryClient();

function ShellLayout() {
  const { data: accounts } = useQuery({ queryKey: ['accounts'], queryFn: listAccounts });
  const { data: postings } = useQuery({ queryKey: ['postings'], queryFn: () => listPostings() });
  const { data: transfers } = useQuery({ queryKey: ['transfers'], queryFn: listTransfers });

  const withBalances = computeBalances(accounts, postings, transfers);
  const totalsByCurrency = sumBalancesByCurrency(withBalances);

  return (
    <div className="min-h-screen flex bg-base-900 text-slate-100">
      <SidebarNav />
      <div className="flex-1 flex flex-col">
        <TopBar totalsByCurrency={totalsByCurrency} />
        <main className="px-4 md:px-6 py-6 flex-1">
          <Outlet context={{ accounts: withBalances }} />
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<ShellLayout />}>
            <Route index element={<AccountsPage />} />
            <Route path="transactions" element={<TransactionsPage />} />
            <Route path="transfers" element={<TransfersPage />} />
            <Route path="categories" element={<CategoriesPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
