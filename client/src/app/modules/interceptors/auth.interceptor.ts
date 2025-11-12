import { AuthenticationSessionService } from '../services/authentication.service';
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, take, filter, throwError, Subject } from 'rxjs';


let refreshInProgress = false;
const refreshDone$ = new Subject<string | null>();

export const authenticationInterceptor: HttpInterceptorFn = (req, next) => {
  const authentication = inject(AuthenticationSessionService);
  const accessToken = authentication.accessToken();
  const withAuthorization = accessToken ? req.clone({
    setHeaders: {
      Authorization: `Bearer ${accessToken}`
    }
  }) : req;


  return next(withAuthorization).pipe(
    catchError((err: unknown) => {
      const e = err as HttpErrorResponse;
      const isAuthCall = req.url.includes('/authentication/sign-in') || req.url.includes('/authentication/refresh-token');
      if (e.status !== 401 || isAuthCall) return throwError(() => e);

      if (!refreshInProgress) {
        refreshInProgress = true;
        authentication.refresh().subscribe({
          next: (session) => {
            refreshInProgress = false;
            const token = session?.accessToken ?? null;
            if (!token) {
              authentication.clearSession();
            }
            refreshDone$.next(token);
          },
          error: () => {
            refreshInProgress = false;
            authentication.clearSession();
            refreshDone$.next(null);
          }
        });
      }
      return refreshDone$.pipe(
        filter(v => v !== undefined), take(1),
        switchMap(tok => tok ? next(req.clone({ setHeaders: { Authorization: `Bearer ${tok}` } })) : throwError(() => e))
      );
    })
  );
};

