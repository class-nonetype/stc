import { Routes } from '@angular/router';

import { authenticationGuard } from './modules/guards/authentication.guard';

export const routes: Routes = [
  {
    path: 'sign-in',
    loadComponent: () => import('./modules/pages/sign-in/sign-in.component').then(m => m.default),
  },

  {
    path: 'sign-up',
    loadComponent: () => import('./modules/pages/sign-up/sign-up.component').then(m => m.default),
  },

  {
    path: '',
    canActivate: [authenticationGuard],
    canActivateChild: [authenticationGuard],
    loadComponent: () => import('./modules/layout/shell/shell').then(m => m.ShellComponent),
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./modules/pages/home/home.component').then(m => m.HomePage),
      },
      {
        path: 'tickets',
        loadComponent: () =>
          import('./modules/pages/tickets/tickets.component').then(m => m.TicketInboxPageComponent),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
