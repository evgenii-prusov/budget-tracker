const API_BASE = "/api";

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown) {
    super(`API error ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

function getAuthHeaders(): HeadersInit {
  const key = localStorage.getItem("api_key");
  return key ? { Authorization: `Bearer ${key}` } : {};
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(response.status, body);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

function buildQuery(params: Record<string, unknown>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      search.set(key, String(value));
    }
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

// --- Accounts ---

import type {
  AccountCreate,
  AccountUpdate,
  AccountResponse,
  CategoryCreate,
  CategoryUpdate,
  CategoryResponse,
  CategoryWithChildrenResponse,
  PostingCreate,
  PostingResponse,
  ReportPeriod,
  TransferCreate,
  TransferResponse,
  SpendingReportResponse,
} from "./types";

export const api = {
  accounts: {
    list: (skip = 0, limit = 50) =>
      request<AccountResponse[]>(`/accounts${buildQuery({ skip, limit })}`),
    get: (id: string) => request<AccountResponse>(`/accounts/${id}`),
    create: (data: AccountCreate) =>
      request<AccountResponse>("/accounts", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    update: (id: string, data: AccountUpdate) =>
      request<AccountResponse>(`/accounts/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      request<void>(`/accounts/${id}`, { method: "DELETE" }),
  },

  categories: {
    list: (skip = 0, limit = 50) =>
      request<CategoryResponse[]>(
        `/categories${buildQuery({ skip, limit })}`,
      ),
    parents: (skip = 0, limit = 50) =>
      request<CategoryWithChildrenResponse[]>(
        `/categories/parents${buildQuery({ skip, limit })}`,
      ),
    get: (id: string) => request<CategoryResponse>(`/categories/${id}`),
    children: (id: string) =>
      request<CategoryResponse[]>(`/categories/${id}/children`),
    create: (data: CategoryCreate) =>
      request<CategoryResponse>("/categories", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    update: (id: string, data: CategoryUpdate) =>
      request<CategoryResponse>(`/categories/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      request<void>(`/categories/${id}`, { method: "DELETE" }),
  },

  postings: {
    list: (params: { account_id?: string; skip?: number; limit?: number } = {}) =>
      request<PostingResponse[]>(
        `/postings/${buildQuery({
          account_id: params.account_id,
          skip: params.skip ?? 0,
          limit: params.limit ?? 50,
        })}`,
      ),
    get: (id: string) => request<PostingResponse>(`/postings/${id}`),
    create: (data: PostingCreate) =>
      request<PostingResponse>("/postings/", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      request<void>(`/postings/${id}`, { method: "DELETE" }),
  },

  transfers: {
    list: (skip = 0, limit = 50) =>
      request<TransferResponse[]>(
        `/transfers/${buildQuery({ skip, limit })}`,
      ),
    get: (id: string) => request<TransferResponse>(`/transfers/${id}`),
    create: (data: TransferCreate) =>
      request<TransferResponse>("/transfers/", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      request<void>(`/transfers/${id}`, { method: "DELETE" }),
  },

  reports: {
    spending: (params: {
      period: ReportPeriod;
      reference_date?: string;
      exclude_savings?: boolean;
    }) =>
      request<SpendingReportResponse>(
        `/reports/spending${buildQuery(params)}`,
      ),
  },
};
