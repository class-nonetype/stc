import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { RequestTypeService } from '../../services/request-type.service';

@Component({
  selector: 'app-request-type-item',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatIconModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSnackBarModule
  ],
  templateUrl: './request-type-item.component.html',
  styleUrl: './request-type-item.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RequestTypeItemComponent {
  private readonly dialogRef = inject(MatDialogRef<RequestTypeItemComponent>);
  private readonly formBuilder = inject(FormBuilder);
  private readonly requestTypeService = inject(RequestTypeService);
  private readonly snackBar = inject(MatSnackBar);

  readonly submitting = signal(false);
  readonly submitSuccess = signal(false);

  readonly form = this.formBuilder.nonNullable.group({
    description: ['', [Validators.required, Validators.maxLength(500)]],
  });

  onSubmit(): void {
    this.submitSuccess.set(false);

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const description = this.form.controls.description.value.trim();
    if (!description) {
      this.form.controls.description.setValue(description);
      this.form.markAllAsTouched();
      return;
    }

    const formData = new FormData();
    formData.append('description', description);

    this.submitting.set(true);
    this.requestTypeService.postRequestType(formData).subscribe({
      next: () => {
        this.submitSuccess.set(true);
        this.snackBar.open('Tipo de solicitud creado', 'Cerrar', {
          duration: 3500,
          horizontalPosition: 'center',
          verticalPosition: 'bottom',
          panelClass: ['snackbar-success'],
        });
        this.dialogRef.close(true);
      },
      error: () => {
        this.submitting.set(false);
      },
      complete: () => {
        this.submitting.set(false);
      }
    });
  }

  onCancel(): void {
    if (this.submitting()) return;
    this.onClose();
  }

  onClose(): void {
    this.dialogRef.close();
  }
}
