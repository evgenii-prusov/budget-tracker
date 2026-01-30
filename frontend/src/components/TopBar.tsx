import { Link, useLocation } from 'react-router-dom';
import { Plus, Lightning } from '@phosphor-icons/react';

type Props = {
  totalsByCurrency: Record<string, string>;
};

export function TopBar({ totalsByCurrency }: Props) {
  const location = useLocation();
  const title = pathTitle(location.pathname);
  const totalString = formatTotals(totalsByCurrency);

  return (
    <header className="sticky top-0 z-10 bg-base-900/80 backdrop-blur border-b border-white/5">
      <div className="flex items-center justify-between px-4 md:px-6 py-3">
        <div className="flex items-center gap-2">
          <Lightning size={20} weight="duotone" className="text-neon-cyan" />
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">{title.section}</p>
            <p className="text-lg font-semibold text-white">{title.label}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <p className="text-[11px] uppercase tracking-[0.18em] text-slate-400">Total Balance</p>
            <p className="text-sm font-semibold text-neon-cyan">{totalString}</p>
          </div>
          <Link
            to="/transactions"
            className="inline-flex items-center gap-2 rounded-full bg-neon-pink/90 hover:bg-neon-pink text-base-900 px-3 py-2 text-sm font-semibold transition shadow-glow"
          >
            <Plus size={16} weight="bold" />
            New Transaction
          </Link>
        </div>
      </div>
    </header>
  );
}

function pathTitle(path: string) {
  if (path.startsWith('/transactions')) return { section: 'Ledger', label: 'Transactions' };
  if (path.startsWith('/transfers')) return { section: 'Flows', label: 'Transfers' };
  if (path.startsWith('/categories')) return { section: 'Tags', label: 'Categories' };
  return { section: 'Accounts', label: 'Accounts' };
}

function formatTotals(totals: Record<string, string>): string {
  const formatter = new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 });
  const entries = Object.entries(totals);
  if (!entries.length) return '—';
  return entries
    .map(([cur, val]) => `${cur} ${formatter.format(Number(val))}`)
    .join(' · ');
}
