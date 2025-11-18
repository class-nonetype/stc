import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, ParamMap } from '@angular/router';
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
  private readonly route = inject(ActivatedRoute);
  private readonly relativeTimeFormatter = new Intl.RelativeTimeFormat('es', { numeric: 'auto' });

  readonly openedTicketIds = signal<Set<string>>(new Set());
  readonly initialFilters = signal<Partial<{
    text: string;
    status: string[];
    request: string[];
    priority: string[];
    requester: string;
    unreadOnly: boolean;
  }> | null>(null);

  readonly loading = computed(() => this.ticketService.loading());
  readonly hasError = computed(() => this.ticketService.hasError());

  readonly cards = computed<Ticket[]>(() => this.ticketService.tickets());
  readonly hasTickets = computed(() => this.cards().length > 0);

  constructor(public session: AuthenticationSessionService) {}

  ngOnInit(): void {
    this.syncFiltersFromQuery();
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

  private syncFiltersFromQuery(): void {
    this.route.queryParamMap.subscribe(params => {
      const status = this.readArrayParam(params, 'status');
      const text = params.get('text') ?? undefined;
      const requester = params.get('requester') ?? undefined;

      if (!status.length && !text && !requester) {
        this.initialFilters.set(null);
        return;
      }

      this.initialFilters.set({
        status,
        text,
        requester,
      });
    });
  }

  private readArrayParam(params: ParamMap, key: string): string[] {
    const values = params.getAll(key);
    if (values.length > 0) return values.filter(Boolean);

    const single = params.get(key);
    if (!single) return [];
    return single.split(',').map(v => v.trim()).filter(Boolean);
  }

}
