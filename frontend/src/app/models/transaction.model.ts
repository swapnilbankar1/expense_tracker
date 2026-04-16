export interface Transaction {
  id: number;
  transaction_id?: string | null;
  date: string;
  merchant_raw: string;
  merchant_clean: string;
  amount: number;
  category: string | null;
  transaction_type: string;
  source: string;
}

export interface TransactionsByMerchant {
  merchant: string;
  total_amount: number;
  transaction_count: number;
  average_amount: number;
}
