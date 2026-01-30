import { Account, Category, Posting, PostingType, Transfer } from './types';

const API_BASE = (import.meta.env.VITE_API_BASE ?? '/api').replace(/\/$/, '');

type FetchOptions = RequestInit & { json?: unknown };

function formatErrorMessage(detail: unknown, statusText: string): string {
  if (detail == null) return statusText;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object' && 'msg' in item) {
          const msg = (item as { msg?: string }).msg;
          return msg ?? JSON.stringify(item);
        }
        return JSON.stringify(item);
      })
      .filter(Boolean);
    return messages.length ? messages.join('; ') : statusText;
  }
  if (typeof detail === 'object') {
    if ('msg' in (detail as Record<string, unknown>)) {
      const msg = (detail as { msg?: string }).msg;
      return msg ?? statusText;
    }
    return JSON.stringify(detail);
  }
  return String(detail);
}

async function request<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const { json, headers, ...rest } = options;
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
      body: json ? JSON.stringify(json) : undefined,
      ...rest,
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Network error';
    throw new Error(`Network error: ${msg}`);
  }

  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    const message = formatErrorMessage(detail?.detail, res.statusText);
    throw new Error(message);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

// Accounts
export const listAccounts = () => request<Account[]>('/accounts');
export const createAccount = (payload: {
  name: string;
  currency: string;
  initial_balance: string | number;
}) => request<Account>('/accounts', { method: 'POST', json: payload });
export const renameAccount = (account_id: string, name: string) =>
  request<Account>(`/accounts/${account_id}`, {
    method: 'PATCH',
    json: { name },
  });
export const deleteAccount = (account_id: string) =>
  request<void>(`/accounts/${account_id}`, { method: 'DELETE' });

// Categories
export const listCategories = () => request<Category[]>('/categories');
export const createCategory = (name: string) =>
  request<Category>('/categories', { method: 'POST', json: { name } });
export const updateCategory = (category_id: string, name: string) =>
  request<Category>(`/categories/${category_id}`, {
    method: 'PATCH',
    json: { name },
  });
export const deleteCategory = (category_id: string) =>
  request<void>(`/categories/${category_id}`, { method: 'DELETE' });

// Postings
export const listPostings = (params?: { account_id?: string }) => {
  const search = params?.account_id ? `?account_id=${params.account_id}` : '';
  return request<Posting[]>(`/postings/${search}`);
};
export const createPosting = (payload: {
  account_id: string;
  amount: string | number;
  posting_date: string;
  posting_type: PostingType;
  category_id?: string | null;
}) => request<Posting>('/postings/', { method: 'POST', json: payload });
export const deletePosting = (posting_id: string) =>
  request<void>(`/postings/${posting_id}`, { method: 'DELETE' });

// Transfers
export const listTransfers = () => request<Transfer[]>('/transfers/');
export const createTransfer = (payload: {
  source_account_id: string;
  dest_account_id: string;
  debit_amount: string | number;
  credit_amount: string | number;
  transfer_date: string;
  description?: string | null;
}) => request<Transfer>('/transfers/', { method: 'POST', json: payload });
export const deleteTransfer = (transfer_id: string) =>
  request<void>(`/transfers/${transfer_id}`, { method: 'DELETE' });
