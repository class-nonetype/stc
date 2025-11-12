import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthenticationSessionService } from '../services/authentication.service';


export const authenticationGuard: CanActivateFn = () => {
  const sessionService = inject(AuthenticationSessionService);
  const router = inject(Router);

  if (sessionService.hasValidSession()) {
    return true;
  }

  return router.createUrlTree(['/sign-in']);
};
