
// src/app/features/home/home.page.ts
import { Component, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatIcon, MatIconModule } from '@angular/material/icon';

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



@Component({
  standalone: true,
  selector: 'home-page',
  imports: [
    MatIcon,
    MatIconModule,
    MatButtonModule,
    MatCardModule,
    MatGridListModule
  ],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomePage {
  private readonly userSession = inject(AuthenticationSessionService);
  private readonly ticketService = inject(TicketService);

  readonly userIsAuthenticated = this.userSession.isAuthenticated;
  readonly userFullName = this.userSession.getCurrentUserFullName() ?? 'Usuario';

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

  options: HomeOption[] = [
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

  x = [];


  constructor() { this.loadTicketCount();}


  private loadTicketCount(): void {
    const requesterId = this.userSession.getCurrentUserId();
    if (!requesterId) return;

    const statusTypes = Object.keys(this.statusMap);

    const requests = statusTypes.map(st =>
      this.ticketService.getCountTicketsByRequesterId(requesterId, st)
        .pipe(map(count => ({ st, count })))
    );

    forkJoin(requests).subscribe({
      next: results => {
        for (const { st, count } of results) {
          const key = this.statusMap[st];
          this.ticketCount[key] = count;
        }
        this.updateOptions(); // ahora sí, ya tienes los números
        console.log('ticketCount listo:', this.ticketCount);
      },
      error: err => console.error('No se pudieron cargar los conteos', err),
    });
  }

  private updateOptions() {
    this.options.push(
      {
        icon: 'schedule',
        label: 'Tickets en espera',
        subtitle: '',
        value: this.ticketCount.onHold,
        click: () => console.log('Tickets finalizados clicked')
      },

      {
        icon: 'pending',
        label: 'Tickets en proceso',
        subtitle: '',
        value: this.ticketCount.inProgress,
        click: () => console.log('Tickets finalizados clicked')
      },

      {
        icon: 'visibility',
        label: 'Tickets abiertos',
        subtitle: '',
        value: this.ticketCount.opened,
        click: () => console.log('Tickets finalizados clicked')
      },

      {
        icon: 'cancel',
        label: 'Tickets cerrados',
        subtitle: '',
        value: this.ticketCount.closed,
        click: () => console.log('Tickets finalizados clicked')
      },

      {
        icon: 'error',
        label: 'Tickets cancelados',
        subtitle: '',
        value: this.ticketCount.cancelled,
        click: () => console.log('Tickets finalizados clicked')
      },

      {
        icon: 'task_alt',
        label: 'Tickets finalizados',
        subtitle: '',
        value: this.ticketCount.finished,
        click: () => console.log('Tickets finalizados clicked')
      },
    );
  }


  openForm(event?: Event) {
    event?.preventDefault();
    event?.stopPropagation();
    this.form.open();
  }
}
