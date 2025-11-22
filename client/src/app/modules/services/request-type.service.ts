import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable, signal } from '@angular/core';
import { environment } from '@environments/environment';
import { endpoints } from '../constants/endpoints';
import type { LevelType, SupportUser, CountFinishedTickets, Ticket, TicketResponse, TicketCreateRequest, TicketAttachment } from '../interfaces/ticket.interface';
import { forkJoin, of } from 'rxjs';
import { Observable, catchError, map, tap, throwError } from 'rxjs';

import { AuthenticationSessionService } from './authentication.service';
import { RequestTypeCreateRequest, RequestTypeResponse } from '../interfaces/request-type.interface';

interface ApiCollectionResponse<T> {
    data?: T[] | T | null;
}


@Injectable({ providedIn: 'root' })
export class RequestTypeService {
    private readonly http = inject(HttpClient);

    readonly tickets = signal<Ticket[]>([]);

    readonly requestTypes = signal<RequestTypeResponse[]>([]);
    readonly priorityTypes = signal<LevelType[]>([]);
    readonly statusTypes = signal<LevelType[]>([]);
    readonly supportUsers = signal<SupportUser[]>([]);

    readonly loading = signal<boolean>(false);
    readonly hasError = signal<boolean>(false);


    postRequestType(payload: RequestTypeCreateRequest | FormData): Observable<RequestTypeResponse> {
        this.hasError.set(false);

        const body = payload;

        return this.http
            .post<RequestTypeResponse>(`${environment.apiUrl}/${endpoints.types.postRequestType}`, body)
            .pipe(
                tap(response => {
                    this.requestTypes.update(previous => [response, ...previous]);
                }),
                catchError(error => {
                    console.error('Failed to create ticket', error);
                    this.hasError.set(true);
                    return throwError(() => error);
                }),
            );
    }

}

