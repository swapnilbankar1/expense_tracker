import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ExpenseService } from '../../services/expense.service';
import { PDFUploadResponse } from '../../models/monthly-expense.model';

@Component({
  selector: 'app-upload',
  imports: [CommonModule, RouterLink],
  templateUrl: './upload.component.html',
  styleUrl: './upload.component.scss'
})
export class UploadComponent {
  private expenseService = inject(ExpenseService);
  
  selectedFile = signal<File | null>(null);
  uploading = signal(false);
  uploadResult = signal<PDFUploadResponse | null>(null);
  errorMessage = signal<string | null>(null);
  dragOver = signal(false);

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.selectedFile.set(input.files[0]);
      this.errorMessage.set(null);
    }
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.dragOver.set(true);
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.dragOver.set(false);
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.dragOver.set(false);

    if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
      this.selectedFile.set(event.dataTransfer.files[0]);
      this.errorMessage.set(null);
    }
  }

  uploadFile(): void {
    const file = this.selectedFile();
    if (!file) {
      this.errorMessage.set('Please select a file');
      return;
    }

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      this.errorMessage.set('Only PDF files are allowed');
      return;
    }

    this.uploading.set(true);
    this.errorMessage.set(null);
    this.uploadResult.set(null);

    this.expenseService.uploadPDFAndGetSummary(file).subscribe({
      next: (response) => {
        this.uploadResult.set(response);
        this.uploading.set(false);
        this.selectedFile.set(null);
      },
      error: (error) => {
        this.errorMessage.set(error.error?.detail || 'Upload failed');
        this.uploading.set(false);
      }
    });
  }

  clearSelection(): void {
    this.selectedFile.set(null);
    this.uploadResult.set(null);
    this.errorMessage.set(null);
  }
}
