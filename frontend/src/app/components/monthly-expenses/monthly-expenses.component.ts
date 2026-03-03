import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ExpenseService } from '../../services/expense.service';
import { MonthlyExpenseSummary } from '../../models/monthly-expense.model';
import { Transaction } from '../../models/transaction.model';

@Component({
  selector: 'app-monthly-expenses',
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './monthly-expenses.component.html',
  styleUrl: './monthly-expenses.component.scss'
})
export class MonthlyExpensesComponent implements OnInit {
  private expenseService = inject(ExpenseService);
  
  monthlySummary = signal<MonthlyExpenseSummary[]>([]);
  filteredSummary = signal<MonthlyExpenseSummary[]>([]);
  loading = signal(true);
  
  selectedYear = signal<number>(new Date().getFullYear());
  selectedMonth = signal<number | null>(null);
  
  // Available years for filter
  availableYears = signal<number[]>([]);
  
  // Expanded months and their transactions
  expandedMonths = signal<Set<string>>(new Set());
  monthTransactions = signal<Map<string, Transaction[]>>(new Map());
  loadingTransactions = signal<Set<string>>(new Set());

  ngOnInit(): void {
    this.loadMonthlyExpenses();
  }

  loadMonthlyExpenses(): void {
    this.loading.set(true);
    this.expenseService.getMonthlyExpenseSummary().subscribe({
      next: (data) => {
        this.monthlySummary.set(data);
        this.filteredSummary.set(data);
        this.extractYears(data);
        this.loading.set(false);
      },
      error: (error) => {
        console.error('Error loading monthly expenses:', error);
        this.loading.set(false);
      }
    });
  }

  extractYears(data: MonthlyExpenseSummary[]): void {
    const years = new Set(data.map(m => m.year));
    this.availableYears.set(Array.from(years).sort((a, b) => b - a));
  }

  applyFilters(): void {
    let filtered = [...this.monthlySummary()];

    if (this.selectedYear()) {
      filtered = filtered.filter(m => m.year === this.selectedYear());
    }

    if (this.selectedMonth()) {
      filtered = filtered.filter(m => m.month === this.selectedMonth());
    }

    // Sort by year and month (most recent first)
    filtered.sort((a, b) => {
      if (a.year !== b.year) return b.year - a.year;
      return b.month - a.month;
    });

    this.filteredSummary.set(filtered);
  }

  clearFilters(): void {
    this.selectedYear.set(new Date().getFullYear());
    this.selectedMonth.set(null);
    this.filteredSummary.set(this.monthlySummary());
  }

  getTotalExpenses(): number {
    return this.filteredSummary().reduce((sum, m) => sum + m.total_amount, 0);
  }

  getTotalTransactions(): number {
    return this.filteredSummary().reduce((sum, m) => sum + m.transaction_count, 0);
  }

  getAverageMonthly(): number {
    const total = this.getTotalExpenses();
    const count = this.filteredSummary().length;
    return count > 0 ? total / count : 0;
  }
  
  getMonthKey(year: number, month: number): string {
    return `${year}-${month}`;
  }
  
  isExpanded(year: number, month: number): boolean {
    return this.expandedMonths().has(this.getMonthKey(year, month));
  }
  
  isLoadingTransactions(year: number, month: number): boolean {
    return this.loadingTransactions().has(this.getMonthKey(year, month));
  }
  
  toggleMonth(year: number, month: number): void {
    const key = this.getMonthKey(year, month);
    const expanded = new Set(this.expandedMonths());
    
    if (expanded.has(key)) {
      expanded.delete(key);
      this.expandedMonths.set(expanded);
    } else {
      expanded.add(key);
      this.expandedMonths.set(expanded);
      
      // Load transactions if not already loaded
      if (!this.monthTransactions().has(key)) {
        this.loadTransactionsForMonth(year, month);
      }
    }
  }
  
  loadTransactionsForMonth(year: number, month: number): void {
    const key = this.getMonthKey(year, month);
    const loading = new Set(this.loadingTransactions());
    loading.add(key);
    this.loadingTransactions.set(loading);
    
    // Calculate date range for the month
    const startDate = `${year}-${String(month).padStart(2, '0')}-01`;
    const lastDay = new Date(year, month, 0).getDate();
    const endDate = `${year}-${String(month).padStart(2, '0')}-${lastDay}`;
    
    this.expenseService.getTransactions({
      start_date: startDate,
      end_date: endDate,
      limit: 500
    }).subscribe({
      next: (transactions) => {
        const map = new Map(this.monthTransactions());
        map.set(key, transactions);
        this.monthTransactions.set(map);
        
        const loading = new Set(this.loadingTransactions());
        loading.delete(key);
        this.loadingTransactions.set(loading);
      },
      error: (error) => {
        console.error('Error loading transactions:', error);
        const loading = new Set(this.loadingTransactions());
        loading.delete(key);
        this.loadingTransactions.set(loading);
      }
    });
  }
  
  getMonthTransactions(year: number, month: number): Transaction[] {
    const key = this.getMonthKey(year, month);
    return this.monthTransactions().get(key) || [];
  }
}
