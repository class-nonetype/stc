import { Output, EventEmitter, Component, inject, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatCard, MatCardActions, MatCardHeader, MatCardSubtitle, MatCardTitle } from '@angular/material/card';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { MatDivider } from '@angular/material/divider';
import { MatButtonModule } from "@angular/material/button";
import { AuthenticationSessionService } from '../../services/authentication.service';
import { finalize } from 'rxjs/operators';
import { Session, SignInRequest, SignInResponse } from '../../interfaces/authentication.interface';
import { HttpErrorResponse } from '@angular/common/http';




@Component({
  selector: 'sign-in-page',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule,
    MatDivider,
    MatCard,
    MatCardHeader,
    //MatCardTitle,
    //MatCardSubtitle,
    //MatCardActions,
    MatButtonModule
],
  templateUrl: './sign-in.component.html',
  styleUrl: './sign-in.component.css',
})
export default class SignInPage {
  private readonly router = inject(Router);
  private readonly authentication = inject(AuthenticationSessionService);

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  readonly form = new FormGroup({
    username: new FormControl<string>('', { nonNullable: true, validators: [Validators.required] }),
    password: new FormControl<string>('', { nonNullable: true, validators: [Validators.required] }),
  });

  readonly controls = this.form.controls;

  readonly showPassword = signal(false);


  submit(): void {
    if (this.form.invalid || this.loading()) {
      return;
    }

    this.error.set(null);
    this.loading.set(true);

    const credentials: SignInRequest = this.form.getRawValue();

    this.authentication.signIn(credentials)
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: (payload: SignInResponse) => {
          const session = this.authentication.establishSession(payload);
          if (!session) {
            this.error.set('No se pudo establecer la sesión. Inténtalo nuevamente.');
            return;
          }
          void this.router.navigate(['/dashboard']);
          this.submitEventEmitter.emit(session);
        },
        error: (error: HttpErrorResponse) => {
          this.error.set(this.resolveErrorMessage(error));
        },
      });
  }

  private resolveErrorMessage(error: HttpErrorResponse): string {
    if (error.status === 401 || error.status === 403) {
      return 'Credenciales inválidas. Verifica tu usuario y contraseña.';
    }
    if (error.status === 0) {
      return 'No se pudo contactar con el servidor. Revisa tu conexión.';
    }
    return 'No fue posible iniciar sesión. Inténtalo nuevamente más tarde.';
  }

  changePasswordVisibility(): void {
    this.showPassword.update((visible) => !visible);
  }

  @Output() submitEventEmitter = new EventEmitter<Session>();

}
