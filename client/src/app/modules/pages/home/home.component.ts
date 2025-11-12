
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

  private countFinishedTickets = 0;

  readonly options = [
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
    {
      icon: 'group',
      label: 'Clientes',
      value: '1 280',
      trend: '+5%' ,
      click: () => console.log('Clientes clicked')
    },
    {
      icon: 'task_alt',
      label: 'Tickets finalizados',
      value: this.countFinishedTickets ?? 0,
      trend: 'En progreso',
      click: () => console.log('Tickets finalizados clicked')
    },
  ];

  private readonly finishedTicketsOption = this.options.find(option => option.label === 'Tickets finalizados');

  constructor() {
    this.loadFinishedTicketsCount();
  }

  private loadFinishedTicketsCount(): void {
    const requesterId = this.userSession.getCurrentUserId();
    if (!requesterId) {
      return;
    }

    this.ticketService.getCountFinishedTicketsByRequesterId(requesterId).subscribe({
      next: count => {
        this.countFinishedTickets = count;

        console.log(this.countFinishedTickets);


        if (this.finishedTicketsOption) {
          this.finishedTicketsOption.value = this.countFinishedTickets;
        }
      },
      error: error => console.error('Failed to load finished tickets count', error),
    });
  }


  openForm(event?: Event) {
    event?.preventDefault();
    event?.stopPropagation();
    this.form.open();
  }
}
