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
      period: string,
      referenceDate?: string,
      excludeSavings?: boolean,
    ) =>
      ["reports", "spending", { period, referenceDate, excludeSavings }] as const,
  },
};
