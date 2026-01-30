export type Currency = 'USD' | 'EUR' | 'GBP' | 'RUB' | 'CHF' | 'JPY' | 'CNY';

export type Account = {
  account_id: string;
  name: string;
  currency: Currency | string;
  initial_balance: string;
};

export type Category = {
  category_id: string;
  name: string;
};

export type PostingType = 'EXPENSE' | 'INCOME';

export type Posting = {
  posting_id: string;
  account_id: string;
  amount: string;
  posting_date: string; // ISO date
  posting_type: PostingType;
  category_id: string | null;
};

export type Transfer = {
  transfer_id: string;
  source_account_id: string;
  dest_account_id: string;
  debit_amount: string;
  credit_amount: string;
  transfer_date: string; // ISO date
  description?: string | null;
};
