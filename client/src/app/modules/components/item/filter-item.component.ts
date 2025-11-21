import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, EventEmitter, Inject, Input, Output } from '@angular/core';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import type { TicketFilters } from '../list/ticket-list.component';

interface FilterDialogData {
  filters: TicketFilters;
  status: string[];
  request: string[];
  priority: string[];
}

@Component({
  selector: 'filter-item',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatIconModule,
  ],
  templateUrl: './filter-item.component.html',
  styleUrl: './filter-item.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FilterItemComponent {
  @Input() filters: TicketFilters = {
    text: '',
    status: [],
    request: [],
    priority: [],
    requester: '',
    unreadOnly: false,
  };
  @Input() statusOptions: string[] = [];
  @Input() requestOptions: string[] = [];
  @Input() priorityOptions: string[] = [];

  @Output() patch = new EventEmitter<{ key: keyof TicketFilters; value: TicketFilters[keyof TicketFilters] }>();
  @Output() reset = new EventEmitter<void>();

  constructor(
    private readonly dialogRef: MatDialogRef<FilterItemComponent>,
    @Inject(MAT_DIALOG_DATA) data: FilterDialogData,
  ) {
    if (data) {
      this.filters = { ...this.filters, ...data.filters };
      this.statusOptions = data.status;
      this.requestOptions = data.request;
      this.priorityOptions = data.priority;
    }
  }

  emitPatch<K extends keyof TicketFilters>(key: K, value: TicketFilters[K]): void {
    this.patch.emit({ key, value });
  }

  onReset(): void {
    this.reset.emit();
  }

  onClose(): void {
    this.dialogRef.close();
  }
}
