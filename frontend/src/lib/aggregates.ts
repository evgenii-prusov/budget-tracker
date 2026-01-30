import Decimal from 'decimal.js';
import { Account, Posting, Transfer } from './types';

export type AccountWithBalance = Account & { balance: string };

export function computeBalances(
  accounts: Account[] | undefined,
  postings: Posting[] | undefined,
  transfers: Transfer[] | undefined,
): AccountWithBalance[] {
  if (!accounts) return [];
  const byAccount = new Map<string, Decimal>();

  for (const acc of accounts) {
    byAccount.set(acc.account_id, new Decimal(acc.initial_balance));
  }

  for (const p of postings ?? []) {
    const current = byAccount.get(p.account_id);
    if (current) byAccount.set(p.account_id, current.plus(new Decimal(p.amount)));
  }

  for (const t of transfers ?? []) {
    const source = byAccount.get(t.source_account_id);
    if (source) byAccount.set(t.source_account_id, source.minus(new Decimal(t.debit_amount)));
    const dest = byAccount.get(t.dest_account_id);
    if (dest) byAccount.set(t.dest_account_id, dest.plus(new Decimal(t.credit_amount)));
  }

  return accounts.map((acc) => ({
    ...acc,
    balance: (byAccount.get(acc.account_id) ?? new Decimal(0)).toFixed(2),
  }));
}

export function sumBalancesByCurrency(accounts: AccountWithBalance[]): Record<string, string> {
  const totals = new Map<string, Decimal>();
  for (const acc of accounts) {
    const cur = acc.currency;
    const existing = totals.get(cur) ?? new Decimal(0);
    totals.set(cur, existing.plus(new Decimal(acc.balance)));
  }
  const result: Record<string, string> = {};
  for (const [currency, total] of totals.entries()) {
    result[currency] = total.toFixed(2);
  }
  return result;
}
