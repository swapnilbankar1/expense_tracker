import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration } from 'chart.js';
import { ExpenseService } from '../../services/expense.service';
import { MonthlyExpenseSummary, CategoryExpense } from '../../models/monthly-expense.model';
import { TransactionsByMerchant } from '../../models/transaction.model';

@Component({
  selector: 'app-dashboard',
  imports: [CommonModule, BaseChartDirective, RouterLink],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit {
  private expenseService = inject(ExpenseService);
  
  monthlySummary = signal<MonthlyExpenseSummary[]>([]);
  topMerchants = signal<TransactionsByMerchant[]>([]);
  loading = signal(true);
  
  totalExpenses = signal(0);
  thisMonthExpenses = signal(0);
  totalTransactions = signal(0);
  topCategory = signal('');

  // Monthly Trend Chart
  monthlyChartData: ChartConfiguration['data'] = {
    datasets: [
      {
        data: [],
        label: 'Monthly Expenses',
        backgroundColor: 'rgba(66, 153, 225, 0.2)',
        borderColor: 'rgba(66, 153, 225, 1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4
      }
    ],
    labels: []
  };

  monthlyChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top'
      }
    },
    scales: {
      y: {
        beginAtZero: true
      }
    }
  };

  // Category Pie Chart
  categoryChartData: ChartConfiguration<'pie'>['data'] = {
    labels: [],
    datasets: [{
      data: [],
      backgroundColor: [
        '#4299e1', '#48bb78', '#ed8936', '#9f7aea',
        '#f56565', '#38b2ac', '#ed64a6', '#ecc94b'
      ]
    }]
  };

  categoryChartOptions: ChartConfiguration<'pie'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right'
      }
    }
  };

  // Top Merchants Bar Chart
  merchantChartData: ChartConfiguration<'bar'>['data'] = {
    labels: [],
    datasets: [{
      data: [],
      label: 'Total Amount',
      backgroundColor: 'rgba(72, 187, 120, 0.6)',
      borderColor: 'rgba(72, 187, 120, 1)',
      borderWidth: 1
    }]
  };

  merchantChartOptions: ChartConfiguration<'bar'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y',
    plugins: {
      legend: {
        display: false
      }
    },
    scales: {
      x: {
        beginAtZero: true
      }
    }
  };

  ngOnInit(): void {
    this.loadDashboardData();
  }

  loadDashboardData(): void {
    this.loading.set(true);

    // Load monthly summary
    this.expenseService.getMonthlyExpenseSummary().subscribe({
      next: (data) => {
        this.monthlySummary.set(data);
        this.updateMonthlyChart(data);
        this.updateCategoryChart(data);
        this.calculateStats(data);
        this.loading.set(false);
      },
      error: (error) => {
        console.error('Error loading monthly summary:', error);
        this.loading.set(false);
      }
    });

    // Load top merchants
    this.expenseService.getTransactionsByMerchant({ sort_by: 'amount' }).subscribe({
      next: (data) => {
        const top10 = data.slice(0, 10);
        this.topMerchants.set(top10);
        this.updateMerchantChart(top10);
      },
      error: (error) => {
        console.error('Error loading merchants:', error);
      }
    });
  }

  updateMonthlyChart(data: MonthlyExpenseSummary[]): void {
    const sortedData = [...data].sort((a, b) => {
      if (a.year !== b.year) return a.year - b.year;
      return a.month - b.month;
    });

    this.monthlyChartData = {
      ...this.monthlyChartData,
      labels: sortedData.map(d => `${d.month_name} ${d.year}`),
      datasets: [{
        ...this.monthlyChartData.datasets[0],
        data: sortedData.map(d => d.total_amount)
      }]
    };
  }

  updateCategoryChart(data: MonthlyExpenseSummary[]): void {
    const categoryMap = new Map<string, number>();

    data.forEach(month => {
      month.categories.forEach(cat => {
        const category = cat.category || 'Uncategorized';
        categoryMap.set(category, (categoryMap.get(category) || 0) + cat.amount);
      });
    });

    const sortedCategories = Array.from(categoryMap.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8);

    this.categoryChartData = {
      ...this.categoryChartData,
      labels: sortedCategories.map(c => c[0]),
      datasets: [{
        ...this.categoryChartData.datasets[0],
        data: sortedCategories.map(c => c[1])
      }]
    };
  }

  updateMerchantChart(merchants: TransactionsByMerchant[]): void {
    this.merchantChartData = {
      ...this.merchantChartData,
      labels: merchants.map(m => m.merchant),
      datasets: [{
        ...this.merchantChartData.datasets[0],
        data: merchants.map(m => m.total_amount)
      }]
    };
  }

  calculateStats(data: MonthlyExpenseSummary[]): void {
    const total = data.reduce((sum, month) => sum + month.total_amount, 0);
    this.totalExpenses.set(total);

    const totalTxns = data.reduce((sum, month) => sum + month.transaction_count, 0);
    this.totalTransactions.set(totalTxns);

    const now = new Date();
    const currentMonth = data.find(m => m.year === now.getFullYear() && m.month === now.getMonth() + 1);
    if (currentMonth) {
      this.thisMonthExpenses.set(currentMonth.total_amount);
    }

    // Find top category
    const categoryMap = new Map<string, number>();
    data.forEach(month => {
      month.categories.forEach(cat => {
        const category = cat.category || 'Uncategorized';
        categoryMap.set(category, (categoryMap.get(category) || 0) + cat.amount);
      });
    });

    if (categoryMap.size > 0) {
      const topCat = Array.from(categoryMap.entries()).sort((a, b) => b[1] - a[1])[0];
      this.topCategory.set(topCat[0]);
    }
  }
}
