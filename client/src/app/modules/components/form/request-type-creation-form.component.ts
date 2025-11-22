import { Component, inject, signal, effect } from "@angular/core";
import { MatFormFieldModule } from "@angular/material/form-field";
import { MatInputModule } from "@angular/material/input";
import { MatIcon, MatIconModule } from "@angular/material/icon";
import { MatButtonModule } from "@angular/material/button";
import { FormBuilder, ReactiveFormsModule, Validators } from "@angular/forms";
import { MatSnackBar, MatSnackBarModule } from "@angular/material/snack-bar";
import { FormService } from "../../services/form.service";
import { RequestTypeService } from "../../services/request-type.service";


@Component({
  selector: 'app-request-type-creation-form',
  standalone: true,
  templateUrl: './request-type-creation-form.component.html',
  styleUrls: ['./request-type-creation-form.component.css'],
  imports: [
    MatIcon,
    ReactiveFormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule,
    MatSnackBarModule
  ]
})
export class RequestTypeCreationFormComponent {
  readonly sidenavState = inject(FormService);

  private readonly formBuilder = inject(FormBuilder);


  private readonly requestTypeService = inject(RequestTypeService);

  readonly submitSuccess = signal<boolean>(false);
  readonly submitting = signal<boolean>(false);
  private readonly snackBar = inject(MatSnackBar);


  readonly generalForm = this.formBuilder.nonNullable.group({
    description: ['', [Validators.required, Validators.maxLength(500)]],
  });

  readonly requestTypeForm = this.formBuilder.group({
    general: this.generalForm,
  });

  constructor() {

    effect(() => {
      const opened = this.sidenavState.isOpen('request-type');
      if (!opened) {
        this.submitSuccess.set(false);
        return;
      }
    });
  }
  onBackdropClick(): void {
    if (this.submitting()) return;
    this.close();
  }

  onCancel(): void {
    if (this.submitting()) return;
    this.close();
  }


  onSubmit(): void {
    this.submitSuccess.set(false);

    if (this.requestTypeForm.invalid) {
      this.requestTypeForm.markAllAsTouched();
      return;
    }

    const general = this.generalForm.getRawValue();
    const description = general.description.trim();
    if (!description) {
      this.generalForm.get('description')?.setValue(description);
      this.generalForm.markAllAsTouched();
      return;
    }


    const formData = new FormData();
    formData.append('description', description);

    this.submitting.set(true);
    this.requestTypeService.postRequestType(formData).subscribe({
      next: () => {
        this.submitting.set(false);
        this.submitSuccess.set(true);
        this.resetForm();
        this.sidenavState.close('request-type');
      },
      error: () => {
        this.submitting.set(false);
      },

      complete: () => {
        this.resetForm();
        this.snackBar.open('Tipo de solicitud creado', 'Cerrar', {
          duration: 3500,
          horizontalPosition: 'center',
          verticalPosition: 'bottom',
          panelClass: ['snackbar-success'],
        });
      }
    });
  }

  close(): void {
    this.resetForm();
    this.sidenavState.close('request-type');
  }

  private resetForm(): void {
    this.generalForm.reset({
      description: '',
    });
  }

}   
