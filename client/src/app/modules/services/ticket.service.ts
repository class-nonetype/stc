import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable, signal } from '@angular/core';
import { environment } from '@environments/environment';
import { endpoints } from '../constants/endpoints';
import type { LevelType, SupportUser, CountFinishedTickets, Ticket, TicketResponse, TicketCreateRequest, TicketAttachment } from '../interfaces/ticket.interface';
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
  private readonly refreshIntervalMs = 5000;
  private refreshIntervalId: ReturnType<typeof setInterval> | null = null;
  private refreshSubscribers = 0;

  readonly tickets = signal<Ticket[]>([]);

  readonly requestTypes = signal<LevelType[]>([]);
  readonly priorityTypes = signal<LevelType[]>([]);
  readonly statusTypes = signal<LevelType[]>([]);
  readonly supportUsers = signal<SupportUser[]>([]);

  readonly loading = signal<boolean>(false);
  readonly hasError = signal<boolean>(false);

  getAllLevelTypes(): void {

    // comprueba que el arreglo devuelto por los tipos
    // no esté vacío (un número distinto de 0 se evalúa como true
    if (
      this.requestTypes().length &&
      this.priorityTypes().length &&
      this.statusTypes().length &&
      this.supportUsers().length &&

      // comprueba que no haya errores
      !this.hasError()
    ) return;

    if (this.loading()) return;

    // cambia los estados reactivos
    this.loading.set(true);
    this.hasError.set(false);


    // esta variable se usará para marcar si alguna de las peticiones falla.
    let encounteredError = false;


    // llamada de todos los endpoints en paralelo (al mismo tiempo)
    forkJoin({
      requestTypes: this.getAllTicketTypes(endpoints.types.requestTypes).pipe(
        catchError(error => {
          console.error('Failed to load request types', error);
          encounteredError = true;

          // retorna un arreglo vacio
          return of([] as LevelType[]);
        }),
      ),
      priorityTypes: this.getAllTicketTypes(endpoints.types.priorityTypes).pipe(
        catchError(error => {
          console.error('Failed to load priority types', error);
          encounteredError = true;

          // retorna un arreglo vacio
          return of([] as LevelType[]);
        }),
      ),
      statusTypes: this.getAllTicketTypes(endpoints.types.statusTypes).pipe(
        catchError(error => {
          console.error('Failed to load status types', error);
          encounteredError = true;

          // retorna un arreglo vacio
          return of([] as LevelType[]);
        }),
      ),
      supportUsers: this.getAllSupportUsers().pipe(
        catchError(error => {
          console.error('Failed to load support users', error);
          encounteredError = true;

          // retorna un arreglo vacio
          return of([] as SupportUser[]);
        }),
      ),

    // cuando todo termine, se cargan los signals
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

  private getAllTicketTypes(endpoint: string) {
    return this.http
      .get<ApiCollectionResponse<LevelType>>(`${environment.apiUrl}/${endpoint}`)
      .pipe(map(response => (Array.isArray(response?.data) ? response.data : [])));
  }

  private getAllSupportUsers() {
    return this.http
      .get<ApiCollectionResponse<SupportUser>>(
        `${environment.apiUrl}/${endpoints.types.supportUsers}`,
      )
      .pipe(map(response => (Array.isArray(response?.data) ? response.data : [])));
  }




  getAllTickets(options?: { silent?: boolean }): void {
    const silent = options?.silent ?? false;
    const userId = this.authentication.getCurrentUserId();
    if (!userId) {
      this.hasError.set(true);
      console.warn('No requester id found for the current session.');
      return;
    }

    const endpointPath = this.getTicketsEndpointForTeam(userId);

    console.log('Cargando los tickets desde: ', endpointPath);


    if (!endpointPath) {
      this.hasError.set(true);
      console.warn('No ticket endpoint available for the current team.');
      return;
    }

    const url = `${environment.apiUrl}/${endpointPath}`;

    if (!silent) {
      this.loading.set(true);
      this.hasError.set(false);
    }

    this.http
      .get<unknown>(url)
      .subscribe({
        next: response => {
          this.tickets.set(this.normalizeTicketsResponse(response));
          this.hasError.set(false);
        },
        error: error => {
          console.error('Failed to load tickets', error);
          this.hasError.set(true);
          if (!silent) {
            this.loading.set(false);
          }
        },
        complete: () => {
          if (!silent) {
            this.loading.set(false);
          }
        },
      });
  }


  getCountTicketsByUserId(userId: string, statusType: string): Observable<number> {
    if (!userId || userId.trim() === '') {
      console.warn('Cannot load finished tickets count without a requester id.');
      return of(0);
    }

    const endpointPath = this.getCountTicketEndpointForTeam(userId);
    if (!endpointPath) {
      console.warn('Cannot load finished tickets count without a valid team context.');
      return of(0);
    }

    const url = `${environment.apiUrl}/${endpointPath}`;
    const status = statusType ? statusType.trim() : '';
    let params = new HttpParams();
    if (status) {
      params = params.set('status', status);
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

  private getTicketsEndpointForTeam(userId: string): string | null {
    const role = this.authentication.getCurrentUserTeam();

    console.log(role);


    if (role === 'Asesoría') {
      return endpoints.tickets.getAllTicketsByRequesterUserId(userId);
    }
    if (role === 'Soporte') {
      return endpoints.tickets.getAllTicketsByManagerUser;
    }
    return null;
  }

  private getCountTicketEndpointForTeam(userId: string): string | null {
    const role = this.authentication.getCurrentUserTeam();

    if (role === 'Asesoría') {
      return endpoints.tickets.getTotalTicketsByRequesterUserId(userId);
    }
    if (role === 'Soporte') {
      return endpoints.tickets.getTotalTicketsByManagerUser;
    }
    return null;
  }

  setTicketManagerByTicketId(ticketId: string, managerId: string) {
    return this.http
      .put<boolean>(
        `${environment.apiUrl}/${endpoints.tickets.setTicketManagerByTicketId(ticketId, managerId)}`,
        {}
      )
      .pipe(map(() => true));
  }

  setTicketStatusByTicketId(ticketId: string, statusId: string) {
    return this.http
      .put<boolean>(
        `${environment.apiUrl}/${endpoints.tickets.setTicketStatusByTicketId(ticketId, statusId)}`,
        {}
      )
      .pipe(map(() => true));
  }


  postTicket(payload: TicketCreateRequest | FormData): Observable<Ticket> {
    this.hasError.set(false);

    const body = payload instanceof FormData ? payload : this.toFormData(payload);

    return this.http
      .post<TicketResponse>(`${environment.apiUrl}/${endpoints.tickets.postTicket}`, body)
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
      requesterId: this.ensureString(schema.requesterId, 'Sin encargado'),
      managerId: this.toNullableString(schema.managerId),
      requester: this.toNullableString(schema.requester),
      manager: this.toNullableString(schema.manager),
      teamId: this.toNullableString(schema.teamId),
      duetAt: this.toNullableString(schema.duetAt),
      resolvedAt: this.toNullableString(schema.resolvedAt),
      closedAt: this.toNullableString(schema.closedAt),
      deletedAt: this.toNullableString(schema.deletedAt),
      createdAt: this.toNullableString(schema.createdAt),
      updatedAt: this.toNullableString(schema.updatedAt),
      isResolved: typeof schema.isResolved === 'boolean' ? schema.isResolved : null,
      isReaded: typeof schema.isResolved === 'boolean' ? schema.isResolved : null,
      attachments: this.normalizeAttachments(schema.attachments, id),
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
      managerId: null,
      requester: null,
      manager: null,
      teamId: null,
      duetAt: null,
      resolvedAt: null,
      closedAt: null,
      deletedAt: null,
      createdAt: null,
      updatedAt: null,
      isResolved: null,
      isReaded: null,
      attachments: [],
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

  private toNullableNumber(value: unknown): number | null {
    if (typeof value === 'number' && Number.isFinite(value)) {
      return value;
    }
    if (typeof value === 'string') {
      const parsed = Number(value);
      if (!Number.isNaN(parsed)) {
        return parsed;
      }
    }
    return null;
  }

  private normalizeAttachments(source: unknown, ticketId: string): TicketAttachment[] {
    const entries = this.extractArray(source);
    if (!entries) return [];

    return entries
      .map((entry, idx) => this.mapAttachment(entry, idx, ticketId))
      .filter((att): att is TicketAttachment => Boolean(att));
  }

  private mapAttachment(entry: unknown, index: number, ticketId: string): TicketAttachment | null {
    if (!entry || typeof entry !== 'object') return null;
    const raw = entry as Record<string, unknown>;

    console.log('raw', raw);


    return {
      id: this.ensureString(raw['id'], `att-${index}-${Date.now()}`),
      ticketId: this.toNullableString(raw['ticketId']) ?? ticketId,
      fileName: this.ensureString(raw['fileName'], 'Archivo adjunto'),
      fileStorageName: this.toNullableString(raw['fileStorageName']),
      filePath: this.toNullableString(raw['filePath']),
      fileSize: this.toNullableNumber(raw['fileSize']),
      mimeType: this.toNullableString(raw['mimeType']),
      createdAt: this.toNullableString(raw['createdAt']),
      url: this.toNullableString(raw['url']),
    };
  }


  enableRealtimeUpdates(): void {
    this.refreshSubscribers++;
    if (this.refreshIntervalId) {
      return;
    }
    this.getAllTickets({ silent: true });

    this.refreshIntervalId = setInterval(() => {
      this.getAllTickets({ silent: true });
    }, this.refreshIntervalMs);
  }

  disableRealtimeUpdates(): void {
    if (this.refreshSubscribers > 0) {
      this.refreshSubscribers--;
    }

    if (this.refreshSubscribers === 0 && this.refreshIntervalId) {
      clearInterval(this.refreshIntervalId);
      this.refreshIntervalId = null;
    }
  }
}

