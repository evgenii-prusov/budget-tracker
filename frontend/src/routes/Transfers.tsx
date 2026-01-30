import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useOutletContext } from 'react-router-dom';
import { createTransfer, deleteTransfer, listTransfers } from '../lib/api';
import type { AccountWithBalance } from '../lib/aggregates';
import { ArrowsLeftRight, ArrowUpRight, Trash } from '@phosphor-icons/react';

type OutletCtx = { accounts: AccountWithBalance[] };

export default function TransfersPage() {
  const { accounts } = useOutletContext<OutletCtx>();
  const { data: transfers } = useQuery({ queryKey: ['transfers'], queryFn: listTransfers });
  const qc = useQueryClient();
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const formatAmount = (value: string) =>
    Number(value).toLocaleString(undefined, {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });

  const mutation = useMutation({
    mutationFn: createTransfer,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transfers'] });
      qc.invalidateQueries({ queryKey: ['accounts'] });
    },
  });
  const deleteMutation = useMutation({
    mutationFn: deleteTransfer,
    onMutate: (transferId) => {
      setDeletingId(transferId);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transfers'] });
      qc.invalidateQueries({ queryKey: ['accounts'] });
    },
    onSettled: () => {
      setDeletingId(null);
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <TransferForm
        accounts={accounts}
        onCreate={(p) => mutation.mutateAsync(p)}
        loading={mutation.isPending}
        error={mutation.error instanceof Error ? mutation.error.message : null}
      />

      <div className="glass-card border border-white/10 overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
          <ArrowsLeftRight size={18} className="text-neon-cyan" />
          <p className="text-sm font-semibold">Recent transfers</p>
        </div>
        <ul className="divide-y divide-white/5 text-sm">
          {(transfers ?? []).map((t) => {
            const from = accounts.find((a) => a.account_id === t.source_account_id);
            const to = accounts.find((a) => a.account_id === t.dest_account_id);
            return (
              <li key={t.transfer_id} className="px-4 py-3 flex items-center justify-between">
                <div>
                  <div className="font-semibold text-slate-100">
                    {from?.name ?? 'Unknown'} → {to?.name ?? 'Unknown'}
                  </div>
                  <div className="text-[11px] text-slate-400">{t.transfer_date}</div>
                  {t.description && <div className="text-slate-300">{t.description}</div>}
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <div className="text-red-300">
                      - {formatAmount(t.debit_amount)} {from?.currency ?? ''}
                    </div>
                    <div className="text-emerald-300">
                      + {formatAmount(t.credit_amount)} {to?.currency ?? ''}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      if (!window.confirm('Delete this transfer?')) return;
                      void deleteMutation.mutateAsync(t.transfer_id);
                    }}
                    disabled={deleteMutation.isPending && deletingId === t.transfer_id}
                    className="inline-flex items-center justify-center rounded-lg bg-red-500/20 text-red-200 hover:bg-red-500/30 p-2 disabled:opacity-60"
                    title="Delete"
                  >
                    <Trash size={16} />
                  </button>
                </div>
              </li>
            );
          })}
          {(transfers ?? []).length === 0 && (
            <li className="px-4 py-5 text-center text-slate-400">No transfers yet.</li>
          )}
        </ul>
      </div>
      {deleteMutation.error instanceof Error && (
        <p className="text-sm text-red-200">{deleteMutation.error.message}</p>
      )}
    </div>
  );
}

function TransferForm({
  accounts,
  onCreate,
  loading,
  error,
}: {
  accounts: AccountWithBalance[];
  onCreate: (payload: {
    source_account_id: string;
    dest_account_id: string;
    debit_amount: string;
    credit_amount: string;
    transfer_date: string;
    description?: string | null;
  }) => Promise<unknown> | void;
  loading: boolean;
  error: string | null;
}) {
  const [source, setSource] = useState('');
  const [dest, setDest] = useState('');
  const [debit, setDebit] = useState('');
  const [credit, setCredit] = useState('');
  const [date, setDate] = useState('');
  const [desc, setDesc] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);

  const canSubmit = source && dest && debit && credit && date;

  return (
    <div className="glass-card p-4 border border-white/10">
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Move funds</p>
          <h3 className="text-lg font-semibold">Transfer between accounts</h3>
        </div>
        <ArrowUpRight size={18} className="text-neon-pink" />
      </div>
      <form
        className="grid gap-3 md:grid-cols-6"
        onSubmit={async (e) => {
          e.preventDefault();
          if (!canSubmit) return;
          setLocalError(null);
          try {
            await onCreate({
              source_account_id: source,
              dest_account_id: dest,
              debit_amount: debit,
              credit_amount: credit,
              transfer_date: date,
              description: desc || null,
            });
            setDebit('');
            setCredit('');
            setDesc('');
          } catch (err) {
            const msg = err instanceof Error ? err.message : 'Could not create transfer';
            setLocalError(msg);
          }
        }}
      >
        <select
          value={source}
          onChange={(e) => setSource(e.target.value)}
          className="rounded-lg bg-base-700/70 border border-white/10 px-3 py-2 text-sm"
          required
        >
          <option value="">Source</option>
          {accounts.map((a) => (
            <option key={a.account_id} value={a.account_id}>
              {a.name}
            </option>
          ))}
        </select>
        <select
          value={dest}
          onChange={(e) => setDest(e.target.value)}
          className="rounded-lg bg-base-700/70 border border-white/10 px-3 py-2 text-sm"
          required
        >
          <option value="">Destination</option>
          {accounts.map((a) => (
            <option key={a.account_id} value={a.account_id}>
              {a.name}
            </option>
          ))}
        </select>
        <input
          type="number"
          step="0.01"
          placeholder="Debit"
          value={debit}
          onChange={(e) => setDebit(e.target.value)}
          className="rounded-lg bg-base-700/70 border border-white/10 px-3 py-2 text-sm"
          required
        />
        <input
          type="number"
          step="0.01"
          placeholder="Credit"
          value={credit}
          onChange={(e) => setCredit(e.target.value)}
          className="rounded-lg bg-base-700/70 border border-white/10 px-3 py-2 text-sm"
          required
        />
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="rounded-lg bg-base-700/70 border border-white/10 px-3 py-2 text-sm"
          required
        />
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Description (optional)"
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
            className="w-full rounded-lg bg-base-700/70 border border-white/10 px-3 py-2 text-sm"
          />
          <button
            type="submit"
            disabled={!canSubmit || loading}
            className="rounded-lg bg-neon-pink/90 text-base-900 px-4 py-2 text-sm font-semibold hover:bg-neon-pink transition shadow-glow disabled:opacity-60"
          >
            {loading ? 'Saving…' : 'Transfer'}
          </button>
        </div>
      </form>
      {(localError || error) && (
        <p className="mt-2 text-sm text-red-200">{localError || error}</p>
      )}
    </div>
  );
}
