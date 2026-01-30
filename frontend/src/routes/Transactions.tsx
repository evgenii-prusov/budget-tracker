import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useOutletContext } from 'react-router-dom';
import { createPosting, deletePosting, listCategories, listPostings } from '../lib/api';
import type { AccountWithBalance } from '../lib/aggregates';
import type { PostingType } from '../lib/types';
import { Trash } from '@phosphor-icons/react';

type OutletCtx = { accounts: AccountWithBalance[] };

export default function TransactionsPage() {
  const { accounts } = useOutletContext<OutletCtx>();
  const [accountFilter, setAccountFilter] = useState<string>('');

  const { data: postings } = useQuery({
    queryKey: ['postings', accountFilter],
    queryFn: () => listPostings(accountFilter ? { account_id: accountFilter } : undefined),
  });
  const { data: categories } = useQuery({ queryKey: ['categories'], queryFn: listCategories });
  const qc = useQueryClient();
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: createPosting,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['postings'] });
      qc.invalidateQueries({ queryKey: ['accounts'] });
    },
  });
  const deleteMutation = useMutation({
    mutationFn: deletePosting,
    onMutate: (postingId) => {
      setDeletingId(postingId);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['postings'] });
      qc.invalidateQueries({ queryKey: ['accounts'] });
    },
    onSettled: () => {
      setDeletingId(null);
    },
  });

  const sorted = useMemo(
    () => (postings ?? []).slice().sort((a, b) => a.posting_date.localeCompare(b.posting_date)).reverse(),
    [postings],
  );

  return (
    <div className="flex flex-col gap-6">
      <AddPostingForm
        accounts={accounts}
        categories={categories ?? []}
        onCreate={(payload) => mutation.mutateAsync(payload)}
        loading={mutation.isPending}
        error={mutation.error instanceof Error ? mutation.error.message : null}
      />

      <div className="flex items-center gap-3">
        <label className="text-sm text-slate-300">Filter by account</label>
        <select
          value={accountFilter}
          onChange={(e) => setAccountFilter(e.target.value)}
          className="rounded-lg bg-base-700/70 border border-white/10 px-3 py-2 text-sm"
        >
          <option value="">All</option>
          {accounts.map((acc) => (
            <option key={acc.account_id} value={acc.account_id}>
              {acc.name}
            </option>
          ))}
        </select>
      </div>

      <div className="overflow-hidden rounded-2xl border border-white/10 bg-base-800/50">
        <table className="w-full text-sm">
          <thead className="bg-white/5 text-slate-300 uppercase tracking-[0.2em] text-[11px]">
            <tr>
              <th className="text-left px-4 py-3">Date</th>
              <th className="text-left px-4 py-3">Account</th>
              <th className="text-left px-4 py-3">Category</th>
              <th className="text-right px-4 py-3">Amount</th>
              <th className="text-right px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((p) => {
              const account = accounts.find((a) => a.account_id === p.account_id);
              const category = categories?.find((c) => c.category_id === p.category_id);
              const isIncome = p.posting_type === 'INCOME';
              return (
                <tr key={p.posting_id} className="border-t border-white/5 hover:bg-white/5">
                  <td className="px-4 py-3 text-slate-200">{p.posting_date}</td>
                  <td className="px-4 py-3">
                    <div className="text-slate-100">{account?.name ?? 'Unknown account'}</div>
                  </td>
                  <td className="px-4 py-3 text-slate-200">{category?.name ?? '—'}</td>
                  <td className="px-4 py-3 text-right font-semibold">
                    <span className={isIncome ? 'text-emerald-300' : 'text-red-300'}>
                      {isIncome ? '+' : ''}
                      {Number(p.amount).toLocaleString(undefined, {
                        minimumFractionDigits: 0,
                        maximumFractionDigits: 2,
                      })}{' '}
                      {account?.currency ?? ''}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      onClick={() => {
                        if (!window.confirm('Delete this posting?')) return;
                        void deleteMutation.mutateAsync(p.posting_id);
                      }}
                      disabled={deleteMutation.isPending && deletingId === p.posting_id}
                      className="inline-flex items-center justify-center rounded-lg bg-red-500/20 text-red-200 hover:bg-red-500/30 p-2 disabled:opacity-60"
                      title="Delete"
                    >
                      <Trash size={16} />
                    </button>
                  </td>
                </tr>
              );
            })}
            {sorted.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-slate-400">
                  No postings yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {deleteMutation.error instanceof Error && (
        <p className="text-sm text-red-200">{deleteMutation.error.message}</p>
      )}
    </div>
  );
}

function AddPostingForm({
  accounts,
  categories,
  onCreate,
  loading,
  error,
}: {
  accounts: AccountWithBalance[];
  categories: { category_id: string; name: string }[];
  onCreate: (payload: {
    account_id: string;
    amount: string;
    posting_date: string;
    posting_type: PostingType;
    category_id?: string | null;
  }) => Promise<unknown> | void;
  loading: boolean;
  error: string | null;
}) {
  const [accountId, setAccountId] = useState<string>('');
  const [amount, setAmount] = useState('');
  const [date, setDate] = useState<string>('');
  const [type, setType] = useState<PostingType>('EXPENSE');
  const [category, setCategory] = useState<string>('');
  const [localError, setLocalError] = useState<string | null>(null);

  const canSubmit = accountId && amount && date;

  return (
    <div className="glass-card p-4 border border-white/10">
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Add posting</p>
          <h3 className="text-lg font-semibold">Track income or expense</h3>
        </div>
      </div>
      <form
        className="grid gap-3 md:grid-cols-5"
        onSubmit={async (e) => {
          e.preventDefault();
          if (!canSubmit) return;
          setLocalError(null);
          try {
            await onCreate({
              account_id: accountId,
              amount,
              posting_date: date,
              posting_type: type,
              category_id: category || null,
            });
            setAmount('');
          } catch (err) {
            const msg = err instanceof Error ? err.message : 'Could not create posting';
            setLocalError(msg);
          }
        }}
      >
        <select
          required
          value={accountId}
          onChange={(e) => setAccountId(e.target.value)}
          className="rounded-lg bg-base-700/70 border border-white/10 px-3 py-2 text-sm"
        >
          <option value="">Select account</option>
          {accounts.map((acc) => (
            <option key={acc.account_id} value={acc.account_id}>
              {acc.name}
            </option>
          ))}
        </select>
        <input
          required
          type="number"
          step="0.01"
          placeholder="Amount"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="rounded-lg bg-base-700/70 border border-white/10 px-3 py-2 text-sm"
        />
        <input
          required
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="rounded-lg bg-base-700/70 border border-white/10 px-3 py-2 text-sm"
        />
        <select
          value={type}
          onChange={(e) => setType(e.target.value as PostingType)}
          className="rounded-lg bg-base-700/70 border border-white/10 px-3 py-2 text-sm"
        >
          <option value="EXPENSE">Expense</option>
          <option value="INCOME">Income</option>
        </select>
        <div className="flex gap-2">
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full rounded-lg bg-base-700/70 border border-white/10 px-3 py-2 text-sm"
          >
            <option value="">No category</option>
            {categories.map((c) => (
              <option key={c.category_id} value={c.category_id}>
                {c.name}
              </option>
            ))}
          </select>
          <button
            type="submit"
            disabled={!canSubmit || loading}
            className="rounded-lg bg-neon-cyan/90 text-base-900 px-4 py-2 text-sm font-semibold hover:bg-neon-cyan transition shadow-glow disabled:opacity-60"
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
