import { APP_INITIALIZER, ApplicationConfig, provideBrowserGlobalErrorListeners, provideZoneChangeDetection, inject } from '@angular/core';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';


import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { authenticationInterceptor } from './modules/interceptors/auth.interceptor';
import { AuthenticationSessionService } from './modules/services/authentication.service';

const restoreSessionFactory = () => {
  const authentication = inject(AuthenticationSessionService);
  return () => authentication.restoreSessionFromServer();
};


export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(withInterceptors([authenticationInterceptor])),
    {
      provide: APP_INITIALIZER,
      multi: true,
      useFactory: restoreSessionFactory,
    },
  ]
};
