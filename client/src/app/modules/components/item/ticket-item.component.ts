import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, ChangeDetectorRef, inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { Ticket } from '../../interfaces/ticket.interface';
import { AuthenticationSessionService } from '../../services/authentication.service';
import { MatButton, MatButtonModule } from '@angular/material/button';
import { TicketService } from '../../services/ticket.service';
import { MatChipsModule } from '@angular/material/chips';
import type { LevelType } from '../../interfaces/ticket.interface';

@Component({
  selector: 'ticket-list-item',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatIconModule,
    MatButtonModule,
    MatButton,
    MatChipsModule],
  templateUrl: './ticket-item.component.html',
  styleUrl: './ticket-item.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TicketListItemComponent {

  private readonly authenticationService = inject(AuthenticationSessionService);
  private readonly ticketService = inject(TicketService);
  private readonly cdr = inject(ChangeDetectorRef);

  readonly userIsAuthenticated: boolean = this.authenticationService.isAuthenticated();
  readonly userTeam = this.authenticationService.getCurrentUserTeam();


  readonly ticket: Ticket = inject<Ticket>(MAT_DIALOG_DATA);
  private readonly dialogRef = inject(MatDialogRef<TicketListItemComponent>);

  get requesterDisplayName(): string {
    return this.ticket.requester?.trim() || this.ticket.requesterId || 'Sin solicitante';
  }

  get managerDisplayName(): string {
    return this.ticket.manager?.trim() || this.ticket.managerId || 'Sin solicitante';
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

  get statusTypes(): LevelType[] {
    return this.ticketService.statusTypes();
  }

  statusChipClass(statusType: LevelType): string {
    const key = this.mapStatusKey(statusType.description);
    return `ticket-chip--${key}`;
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

  onTakeTicket(): void {
    const managerId = this.authenticationService.getCurrentUserId();
    if (!managerId || !this.ticket.id) {
      return;
    }
    this.ticketService.setTicketManagerByTicketId(this.ticket.id, managerId).subscribe({
      next: () => {
        this.dialogRef.close(true);
      },
      error: err => {
        console.error('No se pudo asignar el ticket', err);
      }
    });
  }

  onStatusSelected(statusId: string, selected: boolean): void {
    if (!selected || !this.ticket.id) {
      return;
    }
    this.ticketService.setTicketStatusByTicketId(this.ticket.id, statusId).subscribe({
      next: success => {
        if (success) {
          const found = this.statusTypes.find(st => st.id === statusId);
          this.ticket.statusTypeId = statusId;
          this.ticket.status = found?.description ?? this.ticket.status;
          this.ticket.updatedAt = new Date().toISOString();
          this.ticketService.getAllTickets({ silent: true });
          this.cdr.markForCheck();
        }
      },
      error: err => {
        console.error('No se pudo actualizar el estado', err);
      }
    });
  }

  onClose(): void {
    this.dialogRef.close();
  }

  private mapStatusKey(description?: string | null): string {
    const normalized = (description ?? '').trim().toLowerCase();
    if (!normalized) return 'unknown';

    if (normalized.includes('abierto')) return 'open';
    if (normalized.includes('proceso')) return 'in_progress';
    if (normalized.includes('espera')) return 'on_hold';
    if (normalized.includes('resuelto') || normalized.includes('finalizado')) return 'resolved';
    if (normalized.includes('cerrado')) return 'closed';
    if (normalized.includes('cancel')) return 'cancelled';

    return 'unknown';
  }
}
