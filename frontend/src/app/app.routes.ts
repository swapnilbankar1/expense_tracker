import { Routes } from '@angular/router';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { UploadComponent } from './components/upload/upload.component';
import { TransactionsComponent } from './components/transactions/transactions.component';
import { MonthlyExpensesComponent } from './components/monthly-expenses/monthly-expenses.component';

export const routes: Routes = [
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'upload', component: UploadComponent },
  { path: 'transactions', component: TransactionsComponent },
  { path: 'monthly-expenses', component: MonthlyExpensesComponent }
];
