// --- Enums ---

export type PostingType = "EXPENSE" | "INCOME";
export type CategoryType = "EXPENSE" | "INCOME";

// --- Accounts ---

export interface AccountCreate {
  name: string;
  currency: string;
  initial_balance?: string;
  is_savings?: boolean;
  description?: string | null;
}

export interface AccountUpdate {
  name?: string;
  description?: string | null;
  initial_balance?: string;
}

export interface AccountResponse {
  account_id: string;
  name: string;
  currency: string;
  initial_balance: string;
  is_savings: boolean;
  balance: string;
  description: string | null;
}

// --- Categories ---

export interface CategoryCreate {
  name: string;
  category_type: CategoryType;
  parent_id?: string | null;
  description?: string | null;
}

export interface CategoryUpdate {
  name?: string;
  description?: string | null;
  parent_id?: string | null;
}

export interface CategoryResponse {
  category_id: string;
  name: string;
  category_type: CategoryType;
  parent_id: string | null;
  description: string | null;
}

export interface CategoryWithChildrenResponse extends CategoryResponse {
  children: CategoryResponse[];
}

// --- Postings ---

export interface PostingCreate {
  account_id: string;
  amount: string;
  posting_date: string;
  posting_type: PostingType;
  category_id?: string | null;
  payee?: string | null;
  description?: string | null;
}

export interface PostingUpdate {
  amount?: string;
  posting_date?: string;
  posting_type?: PostingType;
  category_id?: string | null;
  payee?: string | null;
  description?: string | null;
}

export interface PostingResponse {
  posting_id: string;
  account_id: string;
  amount: string;
  posting_date: string;
  posting_type: PostingType;
  category_id: string | null;
  payee: string | null;
  description: string | null;
}

// --- Transfers ---

export interface TransferCreate {
  source_account_id: string;
  dest_account_id: string;
  debit_amount: string;
  credit_amount: string;
  transfer_date: string;
  description?: string | null;
}

export interface TransferResponse {
  transfer_id: string;
  source_account_id: string;
  dest_account_id: string;
  debit_amount: string;
  credit_amount: string;
  transfer_date: string;
  description: string | null;
}

// --- Reports ---

export type ReportPeriod = "week" | "month" | "year";

export interface CategorySpendingResponse {
  parent_category_id: string;
  parent_category_name: string;
  currency: string;
  total: string;
}

export interface SpendingReportResponse {
  period: ReportPeriod;
  start_date: string;
  end_date: string;
  rows: CategorySpendingResponse[];
}

// --- Dashboard ---

export interface IncomeVsSpendingResponse {
  start_date: string;
  end_date: string;
  currency: string;
  total_income: string;
  total_spending: string;
  net_income: string;
  prev_total_income: string;
  prev_total_spending: string;
  spending_ratio: string | null;
  prev_spending_ratio: string | null;
}

export interface DailySpendingEntry {
  spending_date: string;
  daily_total: string;
  cumulative_total: string;
}

export interface SpendingTimelineResponse {
  start_date: string;
  end_date: string;
  currency: string;
  current_period: DailySpendingEntry[];
  previous_period: DailySpendingEntry[];
  projected_total: string | null;
}

// --- Settings ---

export interface SettingsResponse {
  primary_currency: string;
}

export interface UpdateSettingsRequest {
  primary_currency: string;
}

// --- Errors ---

export interface ApiErrorSimple {
  detail: string;
}

export interface ApiErrorValidation {
  detail: Array<{ loc: (string | number)[]; msg: string; type: string }>;
}
