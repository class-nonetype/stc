import { HttpClient } from "@angular/common/http";
import { inject, Injectable, signal } from "@angular/core";
import { environment } from '@environments/environment';
import { endpoints } from "../constants/endpoints";
import { Teams } from "../interfaces/team.interface";

interface TeamsResponse {
  data: Teams[];
}

@Injectable({ providedIn: 'root' })
export class TeamService {
  private readonly http = inject(HttpClient);

  readonly allTeams = signal<Teams[]>([]);
  readonly loading = signal<boolean>(false);
  readonly hasError = signal<boolean>(false);

  // carga todos los grupos
  loadTeams(): void {
    this.loading.set(true);
    this.hasError.set(false);

    this.http
      .get<TeamsResponse>(`${environment.apiUrl}/${endpoints.userTeam.base}`)
      .subscribe({
        next: ({ data }) => {
          const teams = Array.isArray(data) ? data : [];
          this.allTeams.set(teams);
        },
        error: error => {
          console.error('Failed to load team groups', error);
          this.hasError.set(true);
          this.loading.set(false);
        },
        complete: () => this.loading.set(false),
      });

  }

  constructor() {
    this.loadTeams();
  }

}
