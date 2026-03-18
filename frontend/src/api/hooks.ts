import {
  useQuery,
  useInfiniteQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { api } from "./client";
import { queryKeys } from "./keys";
import type {
  AccountCreate,
  AccountUpdate,
  AccountResponse,
  CategoryCreate,
  CategoryUpdate,
  CategoryResponse,
  CategoryWithChildrenResponse,
  PostingCreate,
  PostingUpdate,
  PostingResponse,
  ReportPeriod,
  DashboardPeriod,
  TransferCreate,
  TransferResponse,
  SpendingReportResponse,
  IncomeVsSpendingResponse,
  SpendingTimelineResponse,
  CategorySpendingResponse,
  SettingsResponse,
  UpdateSettingsRequest,
} from "./types";

const PAGE_SIZE = 50;

// --- Accounts ---

export function useAccounts() {
  return useQuery<AccountResponse[]>({
    queryKey: queryKeys.accounts.all,
    queryFn: () => api.accounts.list(0, 100),
  });
}

export function useAccount(id: string) {
  return useQuery<AccountResponse>({
    queryKey: queryKeys.accounts.detail(id),
    queryFn: () => api.accounts.get(id),
    enabled: !!id,
  });
}

export function useCreateAccount() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: AccountCreate) => api.accounts.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.accounts.all });
    },
  });
}

export function useUpdateAccount() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: AccountUpdate }) =>
      api.accounts.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.accounts.all });
    },
  });
}

export function useDeleteAccount() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.accounts.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.accounts.all });
    },
  });
}

// --- Categories ---

export function useCategories() {
  return useQuery<CategoryResponse[]>({
    queryKey: queryKeys.categories.all,
    queryFn: () => api.categories.list(0, 100),
  });
}

export function useCategoryParents() {
  return useQuery<CategoryWithChildrenResponse[]>({
    queryKey: queryKeys.categories.parents,
    queryFn: () => api.categories.parents(0, 100),
  });
}

export function useCreateCategory() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CategoryCreate) => api.categories.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.categories.all });
      qc.invalidateQueries({ queryKey: queryKeys.categories.parents });
    },
  });
}

export function useUpdateCategory() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CategoryUpdate }) =>
      api.categories.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.categories.all });
      qc.invalidateQueries({ queryKey: queryKeys.categories.parents });
    },
  });
}

export function useDeleteCategory() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.categories.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.categories.all });
      qc.invalidateQueries({ queryKey: queryKeys.categories.parents });
    },
  });
}

// --- Postings (useInfiniteQuery) ---

export function usePostings(accountId?: string) {
  return useInfiniteQuery<PostingResponse[]>({
    queryKey: queryKeys.postings.list(accountId),
    queryFn: ({ pageParam = 0 }) =>
      api.postings.list({
        account_id: accountId,
        skip: pageParam as number,
        limit: PAGE_SIZE,
      }),
    initialPageParam: 0,
    getNextPageParam: (lastPage, _allPages, lastPageParam) =>
      lastPage.length === PAGE_SIZE
        ? (lastPageParam as number) + PAGE_SIZE
        : undefined,
  });
}

export function useCreatePosting() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: PostingCreate) => api.postings.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.postings.all });
      qc.invalidateQueries({ queryKey: queryKeys.accounts.all });
    },
  });
}

export function useUpdatePosting() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: PostingUpdate }) =>
      api.postings.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.postings.all });
      qc.invalidateQueries({ queryKey: queryKeys.accounts.all });
    },
  });
}

export function useDeletePosting() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.postings.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.postings.all });
      qc.invalidateQueries({ queryKey: queryKeys.accounts.all });
    },
  });
}

// --- Transfers (useInfiniteQuery) ---

export function useTransfers() {
  return useInfiniteQuery<TransferResponse[]>({
    queryKey: queryKeys.transfers.all,
    queryFn: ({ pageParam = 0 }) =>
      api.transfers.list(pageParam as number, PAGE_SIZE),
    initialPageParam: 0,
    getNextPageParam: (lastPage, _allPages, lastPageParam) =>
      lastPage.length === PAGE_SIZE
        ? (lastPageParam as number) + PAGE_SIZE
        : undefined,
  });
}

export function useCreateTransfer() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: TransferCreate) => api.transfers.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.transfers.all });
      qc.invalidateQueries({ queryKey: queryKeys.accounts.all });
    },
  });
}

export function useDeleteTransfer() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.transfers.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.transfers.all });
      qc.invalidateQueries({ queryKey: queryKeys.accounts.all });
    },
  });
}

// --- Reports ---

export function useSpendingReport(
  period: ReportPeriod,
  referenceDate?: string,
  excludeSavings: boolean = true,
) {
  return useQuery<SpendingReportResponse>({
    queryKey: queryKeys.reports.spending(period, referenceDate, excludeSavings),
    queryFn: () =>
      api.reports.spending({
        period,
        reference_date: referenceDate,
        exclude_savings: excludeSavings,
      }),
  });
}

// --- Dashboard ---

export function useIncomeVsSpending(
  currency: string,
  referenceDate?: string,
  excludeSavings: boolean = true,
  period: DashboardPeriod = "month",
) {
  return useQuery<IncomeVsSpendingResponse>({
    queryKey: queryKeys.dashboard.incomeVsSpending(
      currency,
      referenceDate,
      excludeSavings,
      period,
    ),
    queryFn: () =>
      api.dashboard.incomeVsSpending({
        currency,
        reference_date: referenceDate,
        exclude_savings: excludeSavings,
        period,
      }),
    enabled: !!currency,
  });
}

export function useSpendingByCategories(
  currency: string,
  referenceDate?: string,
  excludeSavings: boolean = true,
  period: DashboardPeriod = "month",
) {
  return useQuery<CategorySpendingResponse[]>({
    queryKey: queryKeys.dashboard.spendingByCategories(
      currency,
      referenceDate,
      excludeSavings,
      period,
    ),
    queryFn: () =>
      api.dashboard.spendingByCategories({
        currency,
        reference_date: referenceDate,
        exclude_savings: excludeSavings,
        period,
      }),
    enabled: !!currency,
  });
}

export function useSpendingTimeline(
  currency: string,
  referenceDate?: string,
  excludeSavings: boolean = true,
  period: DashboardPeriod = "month",
) {
  return useQuery<SpendingTimelineResponse>({
    queryKey: queryKeys.dashboard.spendingTimeline(
      currency,
      referenceDate,
      excludeSavings,
      period,
    ),
    queryFn: () =>
      api.dashboard.spendingTimeline({
        currency,
        reference_date: referenceDate,
        exclude_savings: excludeSavings,
        period,
      }),
    enabled: !!currency,
  });
}

// --- Settings ---

export function useSettings() {
  return useQuery<SettingsResponse>({
    queryKey: queryKeys.settings.all,
    queryFn: () => api.settings.get(),
  });
}

export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: UpdateSettingsRequest) => api.settings.update(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.settings.all });
    },
  });
}
