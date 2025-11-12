import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { Ticket } from '../../interfaces/ticket.interface';

@Component({
  selector: 'ticket-list-item',
  standalone: true,
  imports: [CommonModule, MatDialogModule, MatIconModule],
  templateUrl: './ticket-item.component.html',
  styleUrl: './ticket-item.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TicketListItemComponent {
  readonly ticket: Ticket = inject<Ticket>(MAT_DIALOG_DATA);
  private readonly dialogRef = inject(MatDialogRef<TicketListItemComponent>);

  get requesterDisplayName(): string {
    return this.ticket.requester?.trim() || this.ticket.requesterId || 'Sin solicitante';
  }

  get displayTitle(): string {
    //return this.ticket.note?.trim() || this.ticket.code;

    return this.ticket.request ?? this.ticket.code;
  }

  get statusLabel(): string {
    return this.ticket.status ?? (this.ticket.isResolved ? 'Resuelto' : 'En proceso');
  }

  get statusAccentClass(): string {
    return `ticket-pill--status-${this.statusKey}`;
  }

  get requestLabel(): string {
    return this.ticket.request ?? 'Sin tipo';
  }

  get priorityLabel(): string {
    return this.ticket.priority ?? 'Sin prioridad';
  }

  get lastUpdated(): string {
    return this.ticket.updatedAt ?? this.ticket.createdAt ?? 'Sin fecha';
  }

  get noteText(): string {
    return this.ticket.note?.trim() || 'Sin descripción disponible.';
  }

  get statusKey(): string {
    const base = this.ticket.status?.trim().toLowerCase().replace(/\s+/g, '_');
    if (base && base.length) {
      return base;
    }
    return this.ticket.isResolved ? 'resolved' : 'open';
  }

  onClose(): void {
    this.dialogRef.close();
  }
}
