import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  effect,
  input,
  output,
  signal,
} from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import type { Ticket } from '../../interfaces/ticket.interface';


@Component({
  selector: 'ticket-list',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatPaginatorModule],
  templateUrl: './ticket-list.component.html',
  styleUrl: './ticket-list.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TicketListComponent {
  readonly tickets = input<Ticket[]>([]);
  readonly loading = input<boolean>(false);
  readonly hasError = input<boolean>(false);

  readonly open = output<Ticket>();
  readonly retry = output<void>();


  readonly pageIndex = signal(0);
  readonly pageSize = signal(6);
  readonly pageSizeOptions = [6, 12, 24];

  private readonly relativeTimeFormatter = new Intl.RelativeTimeFormat('es', { numeric: 'auto' });

  readonly visibleTickets = computed(() => {
    const allTickets = this.tickets();
    if (!allTickets.length) return allTickets;

    const index = this.pageIndex();
    const size = this.pageSize();
    const start = index * size;
    return allTickets.slice(start, start + size);
  });

  constructor() {
    effect(() => {
      const totalTickets = this.tickets().length;
      const currentSize = this.pageSize();
      const maxPage = Math.max(Math.ceil(totalTickets / currentSize) - 1, 0);
      const currentPage = this.pageIndex();

      if (currentPage > maxPage) {
        this.pageIndex.set(maxPage);
      }
    });
  }

  onOpen(ticket: Ticket): void {
    this.open.emit(ticket);
  }

  onRetry(): void {
    this.retry.emit();
  }

  onPageChange(event: PageEvent): void {
    this.pageIndex.set(event.pageIndex);
    this.pageSize.set(event.pageSize);
  }

  statusKey(ticket: Ticket): string {
    const base = ticket.status?.trim().toLowerCase().replace(/\s+/g, '_');
    if (base && base.length) {
      return base;
    }
    if (ticket.isResolved === true) return 'resolved';
    return 'open';
  }

  statusLabel(ticket: Ticket): string {
    return ticket.status ?? (ticket.isResolved ? 'Resuelto' : 'En proceso');
  }

  isUnread(ticket: Ticket): boolean {
    return ticket.isResolved === false;
  }

  requesterLabel(ticket: Ticket): string {
    return ticket.requester?.trim() || ticket.requesterId || 'Sin solicitante';
  }

  titleLabel(ticket: Ticket): string {
    return ticket.request?.trim() || ticket.note?.trim() || ticket.code;
  }

  updatedAgo(ticket: Ticket): string {
    return this.formatRelativeTime(ticket.updatedAt ?? ticket.createdAt);
  }

  private formatRelativeTime(iso?: string | null): string {
    if (!iso) {
      return 'Sin fecha';
    }
    const timestamp = Date.parse(iso);
    if (Number.isNaN(timestamp)) {
      return 'Sin fecha';
    }

    const divisions: Array<{ amount: number; unit: Intl.RelativeTimeFormatUnit }> = [
      { amount: 60, unit: 'second' },
      { amount: 60, unit: 'minute' },
      { amount: 24, unit: 'hour' },
      { amount: 7, unit: 'day' },
      { amount: 4.34524, unit: 'week' },
      { amount: 12, unit: 'month' },
      { amount: Infinity, unit: 'year' },
    ];

    let duration = (timestamp - Date.now()) / 1000;
    for (const division of divisions) {
      if (Math.abs(duration) < division.amount) {
        return this.relativeTimeFormatter.format(Math.round(duration), division.unit);
      }
      duration /= division.amount;
    }
    return this.relativeTimeFormatter.format(0, 'second');
  }
}
