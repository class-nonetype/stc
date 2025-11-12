import { Component, inject } from '@angular/core';
import { MatListModule } from '@angular/material/list';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { MatIcon } from '@angular/material/icon';
import { Router } from '@angular/router';
import { AuthenticationSessionService } from 'src/app/modules/services/authentication.service';





@Component({
  selector: 'app-sidenav-options',
  standalone: true,
  imports: [
    RouterLink,
    RouterLinkActive,
    MatListModule,
    MatIcon,
  ],
  templateUrl: './sidenav-options.html',
  styleUrl: './sidenav-options.css',
})
export class SidenavOptions {

  private readonly router = inject(Router);

  private readonly authentication = inject(AuthenticationSessionService)

  readonly modules: SidenavOption[] = [
    {
      name: 'Inicio',
      route: '/dashboard',
      icon: 'dashboard',
      onClick: () => {
        this.router.navigate(['/dashboard']);
      },
    },

    {
      name: 'Tickets',
      route: '/tickets',
      icon: 'inbox',
      onClick: () => {
        this.router.navigate(['/tickets']);
      },
    },
    {
      name: 'Cerrar sesión',
      icon: 'logout',
      onClick: () => {
        const token = this.authentication.accessToken();
        this.authentication.signOut(token).subscribe({
          next: () => {
            this.authentication.clearSession();
            this.router.navigate(['/sign-in']);
          },
          error: () => {
            this.authentication.clearSession();
            this.router.navigate(['/sign-in']);
          },
        });
      },
    },
  ];

  handleClick(m: SidenavOption, event: MouseEvent) {
    if (m.onClick) {
      m.onClick(event);
      return;
    }
    if (m.route) {
      this.router.navigateByUrl(m.route);
    }
  }

}
