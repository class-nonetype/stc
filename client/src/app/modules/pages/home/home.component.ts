
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
    'Cerrado': 'closed',
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
  ];

  private readonly advisorBaseOptions: HomeOption[] = [
    {
      icon: 'person',
      iconBadge: 'speaker_notes',
      label: 'Enviar un ticket',
      subtitle: 'Describa su problema rellenando el formulario de ticket de soporte',
      click: () => this.openForm()
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
    const statsOptions: HomeOption[] = [
      {
        icon: 'schedule',
        label: 'Tickets en espera',
        subtitle: '',
        value: this.ticketCount.onHold,
        click: () => console.log('Tickets en espera clicked')
      },
      {
        icon: 'pending',
        label: 'Tickets en proceso',
        subtitle: '',
        value: this.ticketCount.inProgress,
        click: () => console.log('Tickets en proceso clicked')
      },
      {
        icon: 'visibility',
        label: 'Tickets abiertos',
        subtitle: '',
        value: this.ticketCount.opened,
        click: () => console.log('Tickets abiertos clicked')
      },
      {
        icon: 'cancel',
        label: 'Tickets cerrados',
        subtitle: '',
        value: this.ticketCount.closed,
        click: () => console.log('Tickets cerrados clicked')
      },
      {
        icon: 'error',
        label: 'Tickets cancelados',
        subtitle: '',
        value: this.ticketCount.cancelled,
        click: () => console.log('Tickets cancelados clicked')
      },
      {
        icon: 'task_alt',
        label: 'Tickets finalizados',
        subtitle: '',
        value: this.ticketCount.finished,
        click: () => console.log('Tickets finalizados clicked')
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



  openForm(event?: Event) {
    event?.preventDefault();
    event?.stopPropagation();
    this.form.open();
  }
}
