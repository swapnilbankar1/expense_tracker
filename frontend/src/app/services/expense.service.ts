import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Transaction, TransactionsByMerchant } from '../models/transaction.model';
import { MonthlyExpenseSummary, PDFUploadResponse } from '../models/monthly-expense.model';

@Injectable({
  providedIn: 'root'
})
export class ExpenseService {
  private http = inject(HttpClient);
  private apiUrl = 'http://localhost:8000';

  // Transaction APIs
  getTransactions(filters?: {
    category?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
  }): Observable<Transaction[]> {
    let params = new HttpParams();
    if (filters) {
      if (filters.category) params = params.set('category', filters.category);
      if (filters.start_date) params = params.set('start_date', filters.start_date);
      if (filters.end_date) params = params.set('end_date', filters.end_date);
      if (filters.limit) params = params.set('limit', filters.limit.toString());
      if (filters.offset) params = params.set('offset', filters.offset.toString());
    }
    return this.http.get<Transaction[]>(`${this.apiUrl}/transactions`, { params });
  }

  getTransactionsByMerchant(filters?: {
    start_date?: string;
    end_date?: string;
    merchant?: string;
    sort_by?: 'amount' | 'count' | 'merchant';
  }): Observable<TransactionsByMerchant[]> {
    let params = new HttpParams();
    if (filters) {
      if (filters.start_date) params = params.set('start_date', filters.start_date);
      if (filters.end_date) params = params.set('end_date', filters.end_date);
      if (filters.merchant) params = params.set('merchant', filters.merchant);
      if (filters.sort_by) params = params.set('sort_by', filters.sort_by);
    }
    return this.http.get<TransactionsByMerchant[]>(`${this.apiUrl}/transactions/by-merchant`, { params });
  }

  // Monthly Expense APIs
  getMonthlyExpenseSummary(filters?: {
    year?: number;
    month?: number;
  }): Observable<MonthlyExpenseSummary[]> {
    let params = new HttpParams();
    if (filters) {
      if (filters.year) params = params.set('year', filters.year.toString());
      if (filters.month) params = params.set('month', filters.month.toString());
    }
    return this.http.get<MonthlyExpenseSummary[]>(`${this.apiUrl}/monthly-expenses/summary`, { params });
  }

  getExpensesByCategory(filters?: {
    year?: number;
    month?: number;
  }): Observable<any> {
    let params = new HttpParams();
    if (filters) {
      if (filters.year) params = params.set('year', filters.year.toString());
      if (filters.month) params = params.set('month', filters.month.toString());
    }
    return this.http.get(`${this.apiUrl}/monthly-expenses/categories`, { params });
  }

  syncMonthlyExpenses(): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(`${this.apiUrl}/monthly-expenses/sync`, {});
  }

  // File Upload APIs
  uploadStatement(file: File): Observable<{ message: string; transactions_inserted: number; duplicates_skipped: number }> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<any>(`${this.apiUrl}/statements/upload`, formData);
  }

  uploadPDFAndGetSummary(file: File): Observable<PDFUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<PDFUploadResponse>(`${this.apiUrl}/monthly-expenses/upload-pdf`, formData);
  }
}
