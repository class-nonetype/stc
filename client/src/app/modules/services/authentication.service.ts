import { Injectable, computed, signal, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { finalize, map, tap } from 'rxjs/operators';
import { Session, SignInRequest, SignInResponse, SignOutRequest } from '../interfaces/authentication.interface';
import { environment } from '@environments/environment';
import { endpoints } from '../constants/endpoints';

@Injectable({ providedIn: 'root' })
export class AuthenticationSessionService {
  private readonly http = inject(HttpClient);
  private readonly sessionSignal = signal<Session | null>(null);
  private readonly storageKey = '__stc_auth_session__';
  private hydratedFromStorage = false;

  readonly session = computed(() => this.sessionSignal());
  readonly accessToken = computed(() => this.sessionSignal()?.accessToken ?? null);
  readonly isAuthenticated = computed(() => !!this.accessToken());

  constructor() {
    this.hydrateFromStorage(); // Rehydrate whatever was cached so a reload keeps the session alive.

  }

  signIn(payload: SignInRequest): Observable<SignInResponse> {
    return this.http
      .post<SignInResponse>(
        `${environment.apiUrl}/${endpoints.authentication.signIn}`,
        payload
      )
      .pipe(
        tap(response => {
          console.log(response);
          console.log(this.decodeJwtPayload(response.accessToken ?? ''));
        })
      );
  }

  establishSession(payload: SignInResponse | Session | null | undefined): Session | null {
    const session = this.normalizeSession(payload);
    if (!session) {
      this.clearSession();
      return null;
    }

    this.sessionSignal.set(session);
    this.persistSession(session); // Cache the backend response so it can be restored later.
    return session;
  }

  setAccessToken(token: string | null): void {
    if (!token) {
      this.clearSession();
      return;
    }

    const current = this.sessionSignal();
    if (!current) {
      const next: Session = { accessToken: token };
      this.sessionSignal.set(next);
      this.persistSession(next);
      return;
    }

    const updated = { ...current, accessToken: token };
    this.sessionSignal.set(updated);
    this.persistSession(updated);
  }

  refresh(): Observable<Session | null> {
    return this.http.post<SignInResponse>(
      `${environment.apiUrl}/${endpoints.authentication.refreshToken}`,
      {},
      { withCredentials: true }
    ).pipe(map(payload => this.establishSession(payload)));
  }

  signOut(token: string | null) {
    const payload: SignOutRequest = {
      authorization: token ?? '',
    };

    return this.http.post<void>(
      `${environment.apiUrl}/${endpoints.authentication.signOut}`,
      payload
    );
  }



  hasValidSession(): boolean {
    return !!this.accessToken();
  }

  clearSession(): void {
    this.sessionSignal.set(null);
    this.persistSession(null);
  }

  async restoreSessionFromServer(): Promise<void> {
    this.hydrateFromStorage(); // Only need to rehydrate the cached snapshot on bootstrap.
  }


  getCurrentUserClient(): string | null {
    const current = this.sessionSignal();
    if (current?.client) {
      return current.client;
    }

    const token = this.accessToken();
    if (!token) {
      return null;
    }

    const payload = this.decodeJwtPayload(token);
    if (!payload) {
      return null;
    }

    const fromPayload = payload['client'];
    return typeof fromPayload === 'string' && fromPayload.trim().length > 0 ? fromPayload.trim() : null;
  }

  getCurrentUsername(): string | null {
    const current = this.sessionSignal();
    if (current?.username) {
      return current.username;
    }

    const token = this.accessToken();
    if (!token) {
      return null;
    }

    const payload = this.decodeJwtPayload(token);
    if (!payload) {
      return null;
    }

    const fromPayload = payload['username'];
    return typeof fromPayload === 'string' && fromPayload.trim().length > 0 ? fromPayload.trim() : null;
  }

  getCurrentUserId(): string | null {
    const token = this.accessToken();
    if (!token) {
      return null;
    }

    const payload = this.decodeJwtPayload(token);
    if (!payload) {
      return null;
    }
    console.log(payload);

    return payload['userAccountId']
  }


  getCurrentUserFullName(): string | null {
    const current = this.sessionSignal();
    if (current?.userFullName) {
      return current.userFullName;
    }

    const token = this.accessToken();
    if (!token) {
      return null;
    }

    const payload = this.decodeJwtPayload(token);
    if (!payload) {
      return null;
    }

    const fromPayload = payload['userFullName'];
    return typeof fromPayload === 'string' && fromPayload.trim().length > 0 ? fromPayload.trim() : null;
  }

  private normalizeSession(payload: SignInResponse | Session | null | undefined): Session | null {
    const accessToken = this.extractAccessToken(payload);
    if (!accessToken) {
      return null;
    }

    const current = this.sessionSignal();
    return {
      client: payload?.client ?? current?.client,
      accessToken,
      username: payload?.username ?? current?.username ?? null,
      userFullName: payload?.userFullName ?? current?.userFullName ?? null,
      team: payload?.team ?? current?.team ?? null,
      expiresAt: payload?.expiresAt ?? current?.expiresAt,
    };
  }

  private extractAccessToken(payload: SignInResponse | Session | null | undefined): string | null {
    if (!payload) {
      return null;
    }
    if ('accessToken' in payload && payload.accessToken) {
      return payload.accessToken;
    }
    if ('access_token' in payload && payload.access_token) {
      return payload.access_token;
    }
    if ('token' in payload && payload.token) {
      return payload.token;
    }
    return null;
  }

  private hydrateFromStorage(): void {
    if (this.hydratedFromStorage) {
      return;
    }
    this.hydratedFromStorage = true;
    const cached = this.readPersistedSession();
    if (cached?.accessToken) {
      this.sessionSignal.set(cached);
    }
  }

  private persistSession(session: Session | null): void {
    const storage = this.resolveSessionStorage();
    if (!storage) {
      return;
    }
    try {
      if (!session) {
        storage.removeItem(this.storageKey);
        return;
      }
      storage.setItem(this.storageKey, JSON.stringify(session));
    } catch {
      // If storage is blocked we keep the in-memory session only.
    }
  }

  private readPersistedSession(): Session | null {
    const storage = this.resolveSessionStorage();
    if (!storage) {
      return null;
    }
    try {
      const raw = storage.getItem(this.storageKey);
      return raw ? JSON.parse(raw) as Session : null;
    } catch {
      return null;
    }
  }

  private resolveSessionStorage(): Storage | null {
    if (typeof window === 'undefined' || !window.sessionStorage) {
      return null;
    }
    return window.sessionStorage;
  }

  private decodeJwtPayload(token: string): Record<string, any> | null {
    const segments = token.split('.');
    if (segments.length < 2) {
      return null;
    }
    try {
      const base64 = segments[1].replace(/-/g, '+').replace(/_/g, '/');
      const decoded = decodeURIComponent(
        atob(base64)
          .split('')
          .map(char => `%${('00' + char.charCodeAt(0).toString(16)).slice(-2)}`)
          .join(''),
      );
      return JSON.parse(decoded) as Record<string, any>;
    } catch (error) {
      console.error('No se pudo decodificar el token de acceso', error);
      return null;
    }
  }
}
