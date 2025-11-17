import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Output,
  inject,
  signal,
} from '@angular/core';
import {
  AbstractControl,
  NonNullableFormBuilder,
  ReactiveFormsModule,
  ValidatorFn,
  Validators,
} from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatStepperModule } from '@angular/material/stepper';
import { MatCardModule } from '@angular/material/card';
import { HttpErrorResponse } from '@angular/common/http';

import { AuthenticationSessionService } from '../../services/authentication.service';

import { SignUpRequestPayload, SignUpResponse } from '../../interfaces/sign-up.interface';

import { SelectListComponent } from '../../components/select/select-list.component';

@Component({
  selector: 'sign-up-page',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatStepperModule,
    MatFormFieldModule,
    MatInputModule,
    MatCheckboxModule,
    MatIconModule,
    MatButtonModule,
    MatCardModule,
    SelectListComponent
],
  templateUrl: './sign-up.component.html',
  styleUrl: './sign-up.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,

})
export default class SignUpPage {

  private readonly formBuilder = inject(NonNullableFormBuilder);
  private readonly authenticationService = inject(AuthenticationSessionService);

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal<string | null>(null);

  readonly profileGroup = this.formBuilder.group({
    fullName: this.formBuilder.control('', { validators: [Validators.required, Validators.minLength(3)] }),
    email: this.formBuilder.control('', { validators: [Validators.required, Validators.email] }),
    isActive: this.formBuilder.control(true),
  });

  private readonly passwordsMatchValidator: ValidatorFn = (group: AbstractControl) => {
    const password = group.get('password')?.value as string | undefined;
    const confirmPassword = group.get('confirmPassword')?.value as string | undefined;
    if (!password || !confirmPassword) return null;
    return password === confirmPassword ? null : { passwordMismatch: true };
  };

  readonly accountGroup = this.formBuilder.group(
    {
      username: this.formBuilder.control('', { validators: [Validators.required, Validators.minLength(3)] }),
      password: this.formBuilder.control('', { validators: [Validators.required, Validators.minLength(8)] }),
      confirmPassword: this.formBuilder.control('', { validators: [Validators.required] }),
    },
    { validators: this.passwordsMatchValidator },
  );

  readonly teamGroup = this.formBuilder.group({
    teamGroupId: this.formBuilder.control('', { validators: [Validators.required] }),
  });

  readonly profileControls = this.profileGroup.controls;
  readonly accountControls = this.accountGroup.controls;
  readonly teamGroupControls = this.teamGroup.controls;

  submit(): void {
    if (this.loading()) return;

    this.markAllAsTouched();

    if (this.profileGroup.invalid || this.accountGroup.invalid || this.teamGroup.invalid) {
      return;
    }

    this.loading.set(true);
    this.error.set(null);
    this.success.set(null);

    const payload = this.buildPayload();

    this.authenticationService.signUp(payload).subscribe({
      next: (response: SignUpResponse) => {
        this.success.set('Cuenta creada correctamente.');
        this.resetForms();
        this.submitEventEmitter.emit(response);
      },
      error: (error: HttpErrorResponse) => {
        this.error.set(this.resolveErrorMessage(error));
        this.loading.set(false);
      },
      complete: () => this.loading.set(false),
    });
  }

  private buildPayload(): SignUpRequestPayload {
    const profileValue = this.profileGroup.getRawValue();
    const accountValue = this.accountGroup.getRawValue();
    const teamGroupValue = this.teamGroup.getRawValue();

    const fullName = profileValue.fullName.trim();
    const email = profileValue.email.trim().toLowerCase();
    const username = accountValue.username.trim();
    const password = accountValue.password;
    const teamGroupId = teamGroupValue.teamGroupId.trim();

    return {
      UserProfile: {
        full_name: fullName,
        email,
        is_active: profileValue.isActive ?? true,
      },
      UserAccount: {
        username,
        password,
      },
      TeamGroup: {
        id: teamGroupId,
      },
    };
  }

  private markAllAsTouched(): void {
    this.profileGroup.markAllAsTouched();
    this.accountGroup.markAllAsTouched();
    this.teamGroup.markAllAsTouched();
  }

  private resetForms(): void {
    this.profileGroup.reset({
      fullName: '',
      email: '',
      isActive: true,
    });
    this.accountGroup.reset({
      username: '',
      password: '',
      confirmPassword: '',
    });
    this.teamGroup.reset({
      teamGroupId: '',
    });
  }

  private resolveErrorMessage(error: HttpErrorResponse): string {
    if (error.status === 400) {
      return 'El nombre de usuario ya existe. Intenta con otro.';
    }
    if (error.status === 0) {
      return 'No se pudo contactar con el servidor. Revisa tu conexion.';
    }
    return 'No fue posible completar el registro. Intentalo mas tarde.';
  }

  @Output() submitEventEmitter = new EventEmitter<SignUpResponse>();
}
