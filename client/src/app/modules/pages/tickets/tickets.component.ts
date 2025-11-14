import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { type Ticket } from '../../interfaces/ticket.interface';
import { TicketService } from '../../services/ticket.service';
import { TicketListComponent } from '../../components/list/ticket-list.component';
import { TicketListItemComponent } from '../../components/item/ticket-item.component';
import { AuthenticationSessionService } from '../../services/authentication.service';

@Component({
  selector: 'ticket-inbox-page',
  standalone: true,
  imports: [TicketListComponent, MatButtonModule, MatIconModule],
  templateUrl: './tickets.component.html',
  styleUrl: './tickets.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TicketInboxPageComponent implements OnInit, OnDestroy {
  private readonly userSession = inject(AuthenticationSessionService);
  readonly userIsAuthenticated = this.userSession.isAuthenticated;

  private readonly ticketService = inject(TicketService);
  private readonly dialog = inject(MatDialog);
  private readonly relativeTimeFormatter = new Intl.RelativeTimeFormat('es', { numeric: 'auto' });

  readonly openedTicketIds = signal<Set<string>>(new Set());

  readonly loading = computed(() => this.ticketService.loading());
  readonly hasError = computed(() => this.ticketService.hasError());

  readonly cards = computed<Ticket[]>(() => this.ticketService.tickets());
  readonly hasTickets = computed(() => this.cards().length > 0);

  constructor(public session: AuthenticationSessionService) {}

  ngOnInit(): void {
    this.ticketService.enableRealtimeUpdates();
    this.ticketService.getAllTickets();
  }

  ngOnDestroy(): void {
    this.ticketService.disableRealtimeUpdates();
  }

  onOpen(card: Ticket): void {
    const ticket = this.ticketService.tickets().find(item => item.id === card.id);
    if (!ticket) return;

    this.openedTicketIds.update(previous => {
      const updated = new Set(previous);
      updated.add(card.id);
      return updated;
    });

    this.dialog.open(TicketListItemComponent, {
      data: ticket,
      panelClass: 'ticket-detail-dialog-panel',
      maxWidth: '720px',
    });
  }

  onRetry(): void {
    this.ticketService.getAllTickets();
  }

}
