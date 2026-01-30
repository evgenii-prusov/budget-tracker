import { useMemo, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useOutletContext } from 'react-router-dom';
import { createAccount, deleteAccount, renameAccount } from '../lib/api';
import type { AccountWithBalance } from '../lib/aggregates';
import type { Currency } from '../lib/types';
import { Trash, PencilSimple, Check } from '@phosphor-icons/react';

const currencies: Currency[] = ['USD', 'EUR', 'GBP', 'RUB', 'CHF', 'JPY', 'CNY'];

type OutletCtx = { accounts: AccountWithBalance[] };

export default function AccountsPage() {
  const { accounts } = useOutletContext<OutletCtx>();
  const qc = useQueryClient();
  const [pageError, setPageError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: createAccount,
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['accounts'] });
      setPageError(null);
      qc.setQueryData(['accounts'], (old: AccountWithBalance[] | undefined) => {
        if (!old) return undefined;
        // new account starts with its initial balance
        return [...old, { ...data, balance: String(data.initial_balance) }];
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAccount,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['accounts'] });
      setPageError(null);
    },
  });

  const renameMutation = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) => renameAccount(id, name),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['accounts'] });
      setPageError(null);
    },
  });

  const handleRename = async (id: string, name: string) => {
    setPageError(null);
    try {
      await renameMutation.mutateAsync({ id, name });
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Could not rename account';
      setPageError(msg);
      throw err;
    }
  };

  const handleDelete = async (id: string) => {
    setPageError(null);
    try {
      await deleteMutation.mutateAsync(id);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Could not delete account';
      setPageError(msg);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <AddAccountCard
        onCreate={(payload) => createMutation.mutateAsync(payload)}
        loading={createMutation.isPending}
        error={createMutation.error instanceof Error ? createMutation.error.message : null}
      />
      {pageError && <p className="text-sm text-red-200">{pageError}</p>}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {accounts.map((acc) => (
          <AccountCard
            key={acc.account_id}
            account={acc}
            onDelete={() => handleDelete(acc.account_id)}
            onRename={(name) => handleRename(acc.account_id, name)}
          />
        ))}
      </section>
    </div>
  );
}

function AddAccountCard({
  onCreate,
  loading,
  error,
}: {
  onCreate: (
    payload: { name: string; currency: string; initial_balance: string },
  ) => Promise<unknown> | void;
  loading: boolean;
  error: string | null;
}) {
  const [name, setName] = useState('');
  const [currency, setCurrency] = useState<Currency>('USD');
  const [initial, setInitial] = useState('0');
  const [localError, setLocalError] = useState<string | null>(null);

  return (
    <div className="glass-card p-4 border border-white/10">
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">New account</p>
          <h3 className="text-lg font-semibold">Create a container for your cash</h3>
        </div>
      </div>
      <form
        className="grid gap-3 sm:grid-cols-[2fr,1fr,1fr]"
        onSubmit={async (e) => {
          e.preventDefault();
          setLocalError(null);
          try {
            await onCreate({ name, currency, initial_balance: initial || '0' });
          } catch (err) {
            const msg = err instanceof Error ? err.message : 'Could not create account';
            setLocalError(msg);
          }
        }}
      >
        <input
          className="rounded-lg bg-base-700/70 border border-white/10 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-neon-cyan/50"
          placeholder="Name (e.g. Checking)"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          minLength={3}
        />
        <select
          className="rounded-lg bg-base-700/70 border border-white/10 px-3 py-2 text-sm focus:outline-none"
          value={currency}
          onChange={(e) => setCurrency(e.target.value as Currency)}
        >
          {currencies.map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
        <div className="flex gap-2">
          <input
            className="w-full rounded-lg bg-base-700/70 border border-white/10 px-3 py-2 text-sm"
            type="number"
            step="0.01"
            min="0"
            value={initial}
            onChange={(e) => setInitial(e.target.value)}
            placeholder="Initial balance"
          />
          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-neon-pink/90 text-base-900 px-4 py-2 text-sm font-semibold hover:bg-neon-pink transition shadow-glow disabled:opacity-60"
          >
            {loading ? 'Saving…' : 'Add'}
          </button>
        </div>
      </form>
      {(localError || error) && (
        <p className="mt-2 text-sm text-red-200">{localError || error}</p>
      )}
    </div>
  );
}

function AccountCard({
  account,
  onDelete,
  onRename,
}: {
  account: AccountWithBalance;
  onDelete: () => Promise<void> | void;
  onRename: (name: string) => Promise<void> | void;
}) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(account.name);
  const [error, setError] = useState<string | null>(null);

  const roundedBalance = Math.round(parseFloat(account.balance || '0')).toLocaleString();

  return (
    <div className="glass-card p-4 border border-white/10 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          {editing ? (
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                setError(null);
                try {
                  await onRename(name);
                  setEditing(false);
                } catch (err) {
                  const msg = err instanceof Error ? err.message : 'Could not rename';
                  setError(msg);
                }
              }}
              className="flex items-center gap-2"
            >
              <input
                className="rounded-lg bg-base-700/70 border border-white/10 px-2 py-1 text-sm"
                value={name}
                onChange={(e) => setName(e.target.value)}
                minLength={3}
              />
              <button type="submit" className="p-1 rounded-lg bg-neon-cyan/80 text-base-900">
                <Check size={16} weight="bold" />
              </button>
            </form>
          ) : (
            <div className="flex items-center gap-3">
              <h3 className="text-lg font-semibold">{account.name}</h3>
              <span className="pill bg-white/5 text-slate-200">{account.currency}</span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setEditing((v) => !v)}
            className="p-2 rounded-lg bg-white/5 text-slate-200 hover:bg-white/10"
            title="Rename"
          >
            <PencilSimple size={16} />
          </button>
          <button
            onClick={() => {
              void onDelete();
            }}
            className="p-2 rounded-lg bg-red-500/20 text-red-200 hover:bg-red-500/30"
            title="Delete"
          >
            <Trash size={16} />
          </button>
        </div>
      </div>

      <div className="flex items-baseline gap-2">
        <p className="text-2xl font-semibold text-neon-cyan">
          {account.currency} {roundedBalance}
        </p>
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Current balance</p>
      </div>
      {error && <p className="text-sm text-red-200">{error}</p>}
    </div>
  );
}
