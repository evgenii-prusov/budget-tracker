import type { ReportPeriod } from "./types";

export const queryKeys = {
  accounts: {
    all: ["accounts"] as const,
    detail: (id: string) => ["accounts", id] as const,
  },
  categories: {
    all: ["categories"] as const,
    parents: ["categories", "parents"] as const,
    detail: (id: string) => ["categories", id] as const,
  },
  postings: {
    all: ["postings"] as const,
    list: (accountId?: string) =>
      accountId
        ? (["postings", { accountId }] as const)
        : (["postings"] as const),
  },
  transfers: {
    all: ["transfers"] as const,
  },
  reports: {
    spending: (
      period: ReportPeriod,
      referenceDate?: string,
      excludeSavings: boolean = true,
    ) =>
      ["reports", "spending", { period, referenceDate, excludeSavings }] as const,
  },
  dashboard: {
    incomeVsSpending: (
      currency: string,
      referenceDate?: string,
      excludeSavings: boolean = true,
    ) =>
      [
        "dashboard",
        "income-vs-spending",
        { currency, referenceDate, excludeSavings },
      ] as const,
    spendingByCategories: (
      currency: string,
      referenceDate?: string,
      excludeSavings: boolean = true,
    ) =>
      [
        "dashboard",
        "spending-by-categories",
        { currency, referenceDate, excludeSavings },
      ] as const,
    spendingTimeline: (
      currency: string,
      referenceDate?: string,
      excludeSavings: boolean = true,
    ) =>
      [
        "dashboard",
        "spending-timeline",
        { currency, referenceDate, excludeSavings },
      ] as const,
  },
  settings: {
    all: ["settings"] as const,
  },
};
