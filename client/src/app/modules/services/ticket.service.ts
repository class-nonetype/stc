import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable, signal } from '@angular/core';
import { environment } from '@environments/environment';
import { endpoints } from '../constants/endpoints';
import type { LevelType, SupportUser, CountFinishedTickets, Ticket, TicketResponse, TicketCreateRequest } from '../interfaces/ticket.interface';
import { forkJoin, of } from 'rxjs';
import { Observable, catchError, map, tap, throwError } from 'rxjs';

import { AuthenticationSessionService } from './authentication.service';

interface ApiCollectionResponse<T> {
  data?: T[] | T | null;
}


@Injectable({ providedIn: 'root' })
export class TicketService {
  private readonly http = inject(HttpClient);
  private readonly authentication = inject(AuthenticationSessionService);

  readonly tickets = signal<Ticket[]>([]);

  readonly requestTypes = signal<LevelType[]>([]);
  readonly priorityTypes = signal<LevelType[]>([]);
  readonly statusTypes = signal<LevelType[]>([]);
  readonly supportUsers = signal<SupportUser[]>([]);

  readonly loading = signal<boolean>(false);
  readonly hasError = signal<boolean>(false);

  loadLevelTypes(): void {
    if (
      this.requestTypes().length &&
      this.priorityTypes().length &&
      this.statusTypes().length &&
      this.supportUsers().length &&
      !this.hasError()
    ) {
      return;
    }

    if (this.loading()) {
      return;
    }

    this.loading.set(true);
    this.hasError.set(false);

    let encounteredError = false;

    forkJoin({
      requestTypes: this.fetchTicketTypes(endpoints.types.requestTypes).pipe(
        catchError(error => {
          console.error('Failed to load request types', error);
          encounteredError = true;
          return of([] as LevelType[]);
        }),
      ),
      priorityTypes: this.fetchTicketTypes(endpoints.types.priorityTypes).pipe(
        catchError(error => {
          console.error('Failed to load priority types', error);
          encounteredError = true;
          return of([] as LevelType[]);
        }),
      ),
      statusTypes: this.fetchTicketTypes(endpoints.types.statusTypes).pipe(
        catchError(error => {
          console.error('Failed to load status types', error);
          encounteredError = true;
          return of([] as LevelType[]);
        }),
      ),
      supportUsers: this.fetchSupportUsers().pipe(
        catchError(error => {
          console.error('Failed to load support users', error);
          encounteredError = true;
          return of([] as SupportUser[]);
        }),
      ),
    }).subscribe({
      next: ({ requestTypes, priorityTypes, statusTypes, supportUsers }) => {
        this.requestTypes.set(requestTypes);
        this.priorityTypes.set(priorityTypes);
        this.statusTypes.set(statusTypes);
        this.supportUsers.set(supportUsers);

        this.hasError.set(encounteredError);
      },
      error: error => {
        console.error(error);

        this.hasError.set(true);
        this.loading.set(false);
      },

      complete: () => {
        this.loading.set(false);
      },
    });
  }

  private fetchTicketTypes(endpoint: string) {
    return this.http
      .get<ApiCollectionResponse<LevelType>>(`${environment.apiUrl}/${endpoint}`)
      .pipe(map(response => (Array.isArray(response?.data) ? response.data : [])));
  }

  private fetchSupportUsers() {
    return this.http
      .get<ApiCollectionResponse<SupportUser>>(
        `${environment.apiUrl}/${endpoints.types.supportUsers}`,
      )
      .pipe(map(response => (Array.isArray(response?.data) ? response.data : [])));
  }




  loadTickets(): void {
    const requesterId = this.authentication.getCurrentUserId();
    if (!requesterId) {
      this.hasError.set(true);
      console.warn('No requester id found for the current session.');
      return;
    }

    const url = `${environment.apiUrl}/${endpoints.tickets.byRequester(requesterId)}`;

    this.loading.set(true);
    this.hasError.set(false);

    this.http
      .get<unknown>(url)
      .subscribe({
        next: response => {
          this.tickets.set(this.normalizeTicketsResponse(response));
        },
        error: error => {
          console.error('Failed to load tickets', error);
          this.hasError.set(true);
          this.loading.set(false);
        },
        complete: () => this.loading.set(false),
      });
  }

  getCountTicketsByRequesterId(requesterId: string, statusType: string): Observable<number> {
    if (!requesterId || requesterId === '') {
      console.warn('Cannot load finished tickets count without a requester id.');
      return of(0);
    }

    const url = `${environment.apiUrl}/${endpoints.tickets.countByRequester(requesterId)}`;

    let params = new HttpParams();
    if (statusType && statusType.trim() !== '') {
      params = params.set('status', statusType);
    }


    return this.http.get<ApiCollectionResponse<CountFinishedTickets>>(url, { params }).pipe(
      map(response => {
        const data = (response.data ?? { count: 0 }) as CountFinishedTickets;
        return data.count;
      }),
      catchError(error => {
        console.error('Failed to load finished tickets count', error);
        return of(0);
      }),
    );
  }


  createTicket(payload: TicketCreateRequest | FormData): Observable<Ticket> {
    this.hasError.set(false);

    const body = payload instanceof FormData ? payload : this.toFormData(payload);

    return this.http
      .post<TicketResponse>(`${environment.apiUrl}/${endpoints.tickets.create}`, body)
      .pipe(
        map(schema => this.mapToTicket(schema, this.tickets().length)),
        tap(ticket => {
          this.tickets.update(previous => [ticket, ...previous]);
        }),
        catchError(error => {
          console.error('Failed to create ticket', error);
          this.hasError.set(true);
          return throwError(() => error);
        }),
      );
  }

  private toFormData(payload: TicketCreateRequest): FormData {
    const formData = new FormData();
    Object.entries(payload).forEach(([key, value]) => {
      if (value === undefined || value === null) {
        return;
      }
      formData.append(key, value);
    });
    return formData;
  }

  private normalizeTicketsResponse(payload: unknown): Ticket[] {
    const arrayCandidate = this.extractArray(payload);
    if (arrayCandidate) {
      return arrayCandidate
        .map((entry, index) => this.mapToTicket(entry, index))
        .filter((ticket): ticket is Ticket => Boolean(ticket));
    }
    if (payload === null || payload === undefined) {
      return [];
    }
    return [this.mapToTicket(payload, 0)];
  }

  private extractArray(source: unknown): unknown[] | null {
    if (Array.isArray(source)) {
      return source;
    }

    if (source && typeof source === 'object') {
      const container = source as Record<string, unknown>;
      const candidateKeys = ['items', 'data', 'tickets', 'results', 'result'];
      for (const key of candidateKeys) {
        if (!(key in container)) {
          continue;
        }
        const value = container[key];
        if (value === source) {
          continue;
        }
        const extracted = this.extractArray(value);
        if (extracted) {
          return extracted;
        }
      }
    }

    return null;
  }

  private mapToTicket(entry: unknown, index: number): Ticket {
    if (!entry || typeof entry !== 'object') {
      return this.createFallbackTicket(index);
    }

    const schema = entry as TicketResponse;
    const id = this.ensureString(schema.id, `schema-${index}-${Date.now()}`);
    const code = this.ensureString(schema.code, `#${id.slice(0, 6).toUpperCase()}`);

    return {
      id,
      code,
      note: this.ensureString(schema.note, ''),
      requestTypeId: this.toNullableString(schema.requestTypeId),
      request: this.toNullableString(schema.request),
      priorityTypeId: this.toNullableString(schema.priorityTypeId),
      priority: this.toNullableString(schema.priority),
      statusTypeId: this.toNullableString(schema.statusTypeId),
      status: this.toNullableString(schema.status),
      requesterId: this.ensureString(schema.requesterId, 'Sin solicitante'),
      assigneeId: this.toNullableString(schema.assigneeId),
      requester: this.toNullableString(schema.requester),
      assignee: this.toNullableString(schema.assignee),
      teamId: this.toNullableString(schema.teamId),
      duetAt: this.toNullableString(schema.duetAt),
      resolvedAt: this.toNullableString(schema.resolvedAt),
      closedAt: this.toNullableString(schema.closedAt),
      deletedAt: this.toNullableString(schema.deletedAt),
      createdAt: this.toNullableString(schema.createdAt),
      updatedAt: this.toNullableString(schema.updatedAt),
      isResolved: typeof schema.isResolved === 'boolean' ? schema.isResolved : null,
    };
  }

  private createFallbackTicket(index: number): Ticket {
    return {
      id: `raw-${index}-${Date.now()}`,
      code: 'Sin código',
      note: '',
      requestTypeId: null,
      request: null,
      priorityTypeId: null,
      priority: null,
      statusTypeId: null,
      status: null,
      requesterId: 'unknown',
      assigneeId: null,
      requester: null,
      assignee: null,
      teamId: null,
      duetAt: null,
      resolvedAt: null,
      closedAt: null,
      deletedAt: null,
      createdAt: null,
      updatedAt: null,
      isResolved: null,
    };
  }

  private ensureString(value: unknown, fallback = ''): string {
    const normalized = this.toNullableString(value);
    return normalized ?? fallback;
  }

  private toNullableString(value: unknown): string | null {
    if (typeof value === 'string') {
      const trimmed = value.trim();
      return trimmed.length ? trimmed : null;
    }
    if (typeof value === 'number' && Number.isFinite(value)) {
      return String(value);
    }
    return null;
  }
}
