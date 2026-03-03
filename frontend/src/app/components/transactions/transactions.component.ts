import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { BaseChartDirective } from 'ng2-charts';
import { ChartData, ChartOptions } from 'chart.js';
import { ExpenseService } from '../../services/expense.service';
import { Transaction } from '../../models/transaction.model';

interface MonthOption {
  value: string;
  label: string;
  year: number;
  month: number;
  transactionCount: number;
}

@Component({
  selector: 'app-transactions',
  imports: [CommonModule, FormsModule, RouterLink, BaseChartDirective],
  templateUrl: './transactions.component.html',
  styleUrl: './transactions.component.scss'
})
export class TransactionsComponent implements OnInit {
  private expenseService = inject(ExpenseService);
  
  transactions = signal<Transaction[]>([]);
  filteredTransactions = signal<Transaction[]>([]);
  loading = signal(true);
  
  // Filters
  categoryFilter = signal('');
  merchantFilter = signal('');
  monthFilter = signal('');
  startDate = signal('');
  endDate = signal('');
  
  // Pagination
  currentPage = signal(1);
  itemsPerPage = 50;
  
  // Unique categories and months for filter dropdown
  categories = signal<string[]>([]);
  availableMonths = signal<MonthOption[]>([]);
  
  // Statistics
  monthWithMostTransactions = computed(() => {
    if (this.availableMonths().length === 0) return null;
    return this.availableMonths().reduce((max, month) => 
      month.transactionCount > max.transactionCount ? month : max
    );
  });
  
  selectedMonthLabel = computed(() => {
    if (!this.monthFilter()) return '';
    const month = this.availableMonths().find(m => m.value === this.monthFilter());
    return month ? month.label : '';
  });
  
  // Merchant pie chart
  merchantChartData: ChartData<'pie'> = {
    labels: [],
    datasets: [{
      data: [],
      backgroundColor: [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
        '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'
      ]
    }]
  };
  
  merchantChartOptions: ChartOptions<'pie'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
        labels: {
          boxWidth: 12,
          padding: 10,
          font: { size: 11 }
        }
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const label = context.label || '';
            const value = context.parsed;
            const total = (context.dataset.data as number[]).reduce((a, b) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            return `${label}: ₹${value.toLocaleString()} (${percentage}%)`;
          }
        }
      }
    }
  };
  
  ngOnInit(): void {
    this.loadTransactions();
  }
  
  loadTransactions(): void {
    this.loading.set(true);
    this.expenseService.getTransactions({ limit: 500 }).subscribe({
      next: (data) => {
        this.transactions.set(data);
        this.filteredTransactions.set(data);
        this.extractCategories(data);
        this.extractMonths(data);
        this.updateMerchantChart(data);
        this.loading.set(false);
      },
      error: (error) => {
        console.error('Error loading transactions:', error);
        this.loading.set(false);
      }
    });
  }
  
  extractCategories(transactions: Transaction[]): void {
    const uniqueCategories = new Set<string>();
    transactions.forEach(t => {
      if (t.category) uniqueCategories.add(t.category);
    });
    this.categories.set(Array.from(uniqueCategories).sort());
  }
  
  extractMonths(transactions: Transaction[]): void {
    const monthMap = new Map<string, MonthOption>();
    
    transactions.forEach(t => {
      const date = new Date(t.date);
      const year = date.getFullYear();
      const month = date.getMonth() + 1;
      const key = `${year}-${month.toString().padStart(2, '0')}`;
      
      if (monthMap.has(key)) {
        monthMap.get(key)!.transactionCount++;
      } else {
        const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        monthMap.set(key, {
          value: key,
          label: `${monthNames[month - 1]} ${year}`,
          year,
          month,
          transactionCount: 1
        });
      }
    });
    
    const months = Array.from(monthMap.values()).sort((a, b) => {
      if (a.year !== b.year) return b.year - a.year;
      return b.month - a.month;
    });
    
    this.availableMonths.set(months);
  }
  
  updateMerchantChart(transactions: Transaction[]): void {
    const merchantTotals = new Map<string, number>();
    
    transactions.forEach(t => {
      const merchant = t.merchant_clean || t.merchant_raw;
      merchantTotals.set(merchant, (merchantTotals.get(merchant) || 0) + t.amount);
    });
    
    const sortedMerchants = Array.from(merchantTotals.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);
    
    this.merchantChartData = {
      labels: sortedMerchants.map(m => m[0]),
      datasets: [{
        data: sortedMerchants.map(m => m[1]),
        backgroundColor: [
          '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
          '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'
        ]
      }]
    };
  }
  
  applyFilters(): void {
    let filtered = [...this.transactions()];
    
    // Month filter
    if (this.monthFilter()) {
      const [year, month] = this.monthFilter().split('-').map(Number);
      filtered = filtered.filter(t => {
        const date = new Date(t.date);
        return date.getFullYear() === year && (date.getMonth() + 1) === month;
      });
    }
    
    // Category filter
    if (this.categoryFilter()) {
      filtered = filtered.filter(t => t.category === this.categoryFilter());
    }
    
    // Merchant filter
    if (this.merchantFilter()) {
      const searchTerm = this.merchantFilter().toLowerCase();
      filtered = filtered.filter(t => 
        t.merchant_clean.toLowerCase().includes(searchTerm) ||
        t.merchant_raw.toLowerCase().includes(searchTerm)
      );
    }
    
    // Date filters
    if (this.startDate()) {
      filtered = filtered.filter(t => t.date >= this.startDate());
    }
    if (this.endDate()) {
      filtered = filtered.filter(t => t.date <= this.endDate());
    }
    
    this.filteredTransactions.set(filtered);
    this.updateMerchantChart(filtered);
    this.currentPage.set(1);
  }
  
  clearFilters(): void {
    this.categoryFilter.set('');
    this.merchantFilter.set('');
    this.monthFilter.set('');
    this.startDate.set('');
    this.endDate.set('');
    this.filteredTransactions.set(this.transactions());
    this.updateMerchantChart(this.transactions());
    this.currentPage.set(1);
  }
  
  get paginatedTransactions(): Transaction[] {
    const start = (this.currentPage() - 1) * this.itemsPerPage;
    const end = start + this.itemsPerPage;
    return this.filteredTransactions().slice(start, end);
  }
  
  get totalPages(): number {
    return Math.ceil(this.filteredTransactions().length / this.itemsPerPage);
  }
  
  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage.set(page);
    }
  }
  
  getTotalAmount(): number {
    return this.filteredTransactions().reduce((sum, t) => sum + t.amount, 0);
  }
}
