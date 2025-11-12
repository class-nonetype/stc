import { Component } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { SidenavOptions } from './options/sidenav-options';

@Component({
  selector: 'app-sidenav',
  standalone: true,
  imports: [
    SidenavOptions,
    MatIconModule,
  ],
  templateUrl: './sidenav.html',
  styleUrl: './sidenav.css',
})
export class AppSidenav {}
