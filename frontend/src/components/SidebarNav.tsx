import { NavLink } from 'react-router-dom';
import { Gauge, CreditCard, ArrowsLeftRight, Tag } from '@phosphor-icons/react';
import clsx from 'clsx';

const links = [
  { to: '/', label: 'Accounts', icon: Gauge },
  { to: '/transactions', label: 'Transactions', icon: CreditCard },
  { to: '/transfers', label: 'Transfers', icon: ArrowsLeftRight },
  { to: '/categories', label: 'Categories', icon: Tag },
];

export function SidebarNav() {
  return (
    <aside className="hidden md:flex md:flex-col gap-4 w-60 shrink-0 p-4 bg-base-800/80 border-r border-white/5 backdrop-blur-lg">
      <div className="flex items-center gap-2 text-lg font-semibold tracking-tight">
        <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-neon-pink to-neon-cyan flex items-center justify-center text-base font-bold text-base-900 shadow-glow">
          BT
        </div>
        Budget Tracker
      </div>
      <nav className="flex flex-col gap-1 text-sm">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 rounded-xl px-3 py-2 transition-colors',
                isActive
                  ? 'bg-white/10 text-white shadow-glow'
                  : 'text-slate-300 hover:bg-white/5',
              )
            }
          >
            <Icon size={18} weight="duotone" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
