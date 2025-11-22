
// src/app/features/home/home.page.ts
import { ChangeDetectorRef, Component, OnDestroy, OnInit, effect, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatIcon, MatIconModule } from '@angular/material/icon';
import { MatBadgeModule } from '@angular/material/badge';

import { FormService } from '../../services/form.service';
import { Router } from '@angular/router';
import { AuthenticationSessionService } from '../../services/authentication.service';
import { TicketService } from '../../services/ticket.service';
import { MatDialog } from '@angular/material/dialog';
import { RequestTypeItemComponent } from '../../components/item/request-type-item.component';

import { forkJoin, map } from 'rxjs';


type TicketCounts = {
  opened: number;
  inProgress: number;
  onHold: number;
  closed: number;
  cancelled: number;
  finished: number;
};

type ClickHandler = () => void | Promise<boolean>;

interface HomeOption {
  icon: string;
  label: string;
  subtitle: string;
  click: ClickHandler;
  iconBadge?: string;
  value?: number;
  trend?: string;
  disabled?: boolean;
}

const EMPTY_STATS: HomeOption[] = [];


@Component({
  standalone: true,
  selector: 'home-page',
  imports: [
    MatIcon,
    MatIconModule,
    MatButtonModule,
    MatCardModule,
    MatGridListModule,
    MatBadgeModule
  ],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomePage implements OnInit, OnDestroy {
  private readonly userSession = inject(AuthenticationSessionService);
  private readonly ticketService = inject(TicketService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly dialog = inject(MatDialog);

  readonly userIsAuthenticated = this.userSession.isAuthenticated;
  readonly userFullName = this.userSession.getCurrentUserFullName();
  readonly userTeam = this.userSession.getCurrentUserTeam();

  private readonly form = inject(FormService);
  private readonly router = inject(Router);

  //private readonly ticketCount = {
  //  opened: 0,
  //  inProgress: 0,
  //  onHold: 0,
  //  closed: 0,
  //  cancelled: 0,
  //  finished: 0,
  //};

  private readonly statusMap: Record<string, keyof TicketCounts> = {
    'Abierto': 'opened',
    'En proceso': 'inProgress',
    'En espera': 'onHold',
    //'Cerrado': 'closed',
    'Cancelado': 'cancelled',
    'Resuelto': 'finished',
  };

  ticketCount: TicketCounts = { opened: 0, inProgress: 0, onHold: 0, closed: 0, cancelled: 0, finished: 0 };

  private readonly supportBaseOptions: HomeOption[] = [
    {
      icon: 'confirmation_number',
      label: 'Tickets solicitados',
      subtitle: 'Visualice las solicitudes que han sido emitidas.',
      click: () => this.router.navigate(['/tickets'])
    },

    {
      icon: 'library_add_check',
      label: 'Crear tipo de solicitud',
      subtitle: 'Añade un nuevo tipo de solicitud para que pueda ser emitido por los usuarios.',
      click: () => this.openRequestTypeDialog()
    }
  ];

  private readonly advisorBaseOptions: HomeOption[] = [
    {
      icon: 'person',
      iconBadge: 'speaker_notes',
      label: 'Enviar un ticket',
      subtitle: 'Describa su problema rellenando el formulario de ticket de soporte',
      click: () => this.openForm('ticket')
    },
    {
      icon: 'confirmation_number',
      label: 'Tickets solicitados',
      subtitle: 'Visualice las solicitudes que han sido emitidas.',
      click: () => this.router.navigate(['/tickets'])
    },
  ];

  supportUserOptions: HomeOption[] = [...this.supportBaseOptions];
  advisorUserOptions: HomeOption[] = [...this.advisorBaseOptions];
  statusDashboardOptions: HomeOption[] = EMPTY_STATS;



  private readonly syncTicketCounts = effect(() => {
    const authenticated = this.userIsAuthenticated();
    const ticketsSnapshot = this.ticketService.tickets();
    if (!authenticated) {
      return;
    }
    // Trigger whenever the ticket collection is refreshed.
    void ticketsSnapshot;
    this.loadTicketCount();
  });

  ngOnInit(): void {
    this.resetBaseOptions();
    this.ticketService.enableRealtimeUpdates();
    this.loadTicketCount();
  }

  ngOnDestroy(): void {
    this.ticketService.disableRealtimeUpdates();
  }


  private loadTicketCount(): void {
    const userId = this.userSession.getCurrentUserId();
    if (!userId) return;

    const statusTypes = Object.keys(this.statusMap);

    const requests = statusTypes.map(st =>
      this.ticketService.getCountTicketsByUserId(userId, st)
        .pipe(map(count => ({ st, count })))
    );

    forkJoin(requests).subscribe({
      next: results => {
        for (const { st, count } of results) {
          const key = this.statusMap[st];
          this.ticketCount[key] = count;
        }
        this.updateOptions();
        console.log('ticketCount listo:', this.ticketCount);
      },
      error: err => console.error('No se pudieron cargar los conteos', err),
    });
  }

  private updateOptions() {
    const navToTickets = (status: string) =>
      this.router.navigate(['/tickets'], { queryParams: { status } });

    const statsOptions: HomeOption[] = [
      {
        icon: 'schedule',
        label: 'Tickets en espera',
        subtitle: '',
        value: this.ticketCount.onHold,
        disabled: this.ticketCount.onHold === 0,
        click: () => navToTickets('En espera')
      },
      {
        icon: 'pending',
        label: 'Tickets en proceso',
        subtitle: '',
        value: this.ticketCount.inProgress,
        disabled: this.ticketCount.inProgress === 0,
        click: () => navToTickets('En proceso')
      },
      {
        icon: 'visibility',
        label: 'Tickets abiertos',
        subtitle: '',
        value: this.ticketCount.opened,
        disabled: this.ticketCount.opened === 0,
        click: () => navToTickets('Abierto')
      },
      //{
      //  icon: 'cancel',
      //  label: 'Tickets cerrados',
      //  subtitle: '',
      //  value: this.ticketCount.closed,
      //  disabled: this.ticketCount.closed === 0,
      //  click: () => navToTickets('Cerrado')
      //},

      {
        icon: 'error',
        label: 'Tickets cancelados',
        subtitle: '',
        value: this.ticketCount.cancelled,
        disabled: this.ticketCount.cancelled === 0,
        click: () => navToTickets('Cancelado')
      },

      {
        icon: 'task_alt',
        label: 'Tickets finalizados',
        subtitle: '',
        value: this.ticketCount.finished,
        disabled: this.ticketCount.finished === 0,
        click: () => navToTickets('Resuelto')
      },
    ];

    this.statusDashboardOptions = statsOptions;
    this.supportUserOptions = [...this.supportBaseOptions];
    this.advisorUserOptions = [...this.advisorBaseOptions];
    this.cdr.markForCheck();
  }

  private resetBaseOptions(): void {
    this.supportUserOptions = [...this.supportBaseOptions];
    this.advisorUserOptions = [...this.advisorBaseOptions];
  }

  private isSupportUser(): boolean {
    const team = this.userSession.getCurrentUserTeam();
    return (team ?? '').toLowerCase() === 'soporte';
  }



  openForm(context: string, event?: Event) {
    event?.preventDefault();
    event?.stopPropagation();
    this.form.open(context);
  }

  openRequestTypeDialog(event?: Event) {
    event?.preventDefault();
    event?.stopPropagation();

    this.dialog.open(RequestTypeItemComponent, {
      maxWidth: '720px',
      width: 'min(720px, 96vw)',
      panelClass: 'ticket-detail-dialog-panel',
    });
  }
}
