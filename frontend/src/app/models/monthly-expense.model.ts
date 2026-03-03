export interface MonthlyExpenseSummary {
  year: number;
  month: number;
  month_name: string;
  total_amount: number;
  transaction_count: number;
  categories: CategoryExpense[];
}

export interface CategoryExpense {
  category: string | null;
  source: string;
  amount: number;
  count: number;
}

export interface PDFUploadResponse {
  message: string;
  transactions_inserted: number;
  duplicates_skipped: number;
  monthly_summary: MonthlyExpenseSummary[];
}
