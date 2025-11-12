import { ChangeDetectionStrategy, Component, effect, inject, signal, ViewChild } from '@angular/core';
import { AbstractControl, FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatStepperModule } from '@angular/material/stepper';

import { FormService } from '../../services/form.service';
import { MatIcon } from "@angular/material/icon";
import { MatStep, MatStepper } from "@angular/material/stepper";
import { MatError, MatFormField, MatHint, MatLabel } from "@angular/material/form-field";
import { MatOption, MatSelect } from "@angular/material/select";
import { AuthenticationSessionService } from "../../services/authentication.service";
import { TicketService } from "../../services/ticket.service";
import { TeamService } from "../../services/team.service";
import { LevelType, SupportUser } from "../../interfaces/ticket.interface";
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';



@Component({
  selector: 'app-ticket-creation-form',
  templateUrl: './ticket-creation-form.component.html',
  styleUrl: './ticket-creation-form.component.css',
  imports: [
    MatIcon,
    MatStepper,
    MatStep,
    MatFormField,
    MatLabel,
    MatSelect,
    MatOption,
    MatHint,
    MatError,
    ReactiveFormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule,
    MatStepperModule,
    MatSelectModule,
    MatSnackBarModule
  ]
})
export class AppTicketCreationFormComponent {

  @ViewChild('ticketStepper') private stepper?: MatStepper;

  readonly sidenavState = inject(FormService);

  private readonly formBuilder = inject(FormBuilder);
  private readonly authentication = inject(AuthenticationSessionService);
  private readonly ticketService = inject(TicketService);
  private readonly teamService = inject(TeamService);

  private readonly snackBar = inject(MatSnackBar);

  readonly requestTypes = this.ticketService.requestTypes;
  readonly priorityTypes = this.ticketService.priorityTypes;
  readonly statusTypes = this.ticketService.statusTypes;
  readonly supportUsers = this.ticketService.supportUsers;
  readonly referencesLoading = this.ticketService.loading;
  readonly referencesHasError = this.ticketService.hasError;


  readonly attachments = signal<File[]>([]);
  readonly dropzoneActive = signal<boolean>(false);
  readonly submitting = signal<boolean>(false);
  readonly submitSuccess = signal<boolean>(false);
  readonly formErrorMessage = signal<string | null>(null);


  readonly generalForm = this.formBuilder.nonNullable.group({
    code: [`TCKT-${this.getNumericCode()}`, [Validators.maxLength(32)]],
    request_type_id: ['', Validators.required],
    priority_type_id: ['', Validators.required],
    note: ['', [Validators.maxLength(1000)]],
  });

  readonly assignmentForm = this.formBuilder.nonNullable.group({
    assignee_id: ['', Validators.required],
  });

  readonly ticketForm = this.formBuilder.group({
    general: this.generalForm,
    assignment: this.assignmentForm,
  });


  constructor() {
    this.ticketService.loadLevelTypes();
    this.teamService.loadTeams();

    effect(() => {
      const opened = this.sidenavState.opened();
      if (!opened) {
        this.submitSuccess.set(false);
        return;
      }
      this.assignNewCode();
    });

    effect(() => {
      const disable = this.referencesLoading() && !this.requestTypes().length;
      this.toggleControlDisabled(this.generalForm.get('request_type_id'), disable);
    });

    effect(() => {
      const disable = this.referencesLoading() && !this.priorityTypes().length;
      this.toggleControlDisabled(this.generalForm.get('priority_type_id'), disable);
    });

    effect(() => {
      const disable = this.referencesLoading() && !this.supportUsers().length;
      this.toggleControlDisabled(this.assignmentForm.get('assignee_id'), disable);
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

  close(): void {
    this.resetForm();
    this.sidenavState.close();
  }

  onSubmit(): void {
    this.formErrorMessage.set(null);
    this.submitSuccess.set(false);

    if (this.ticketForm.invalid) {
      this.ticketForm.markAllAsTouched();
      return;
    }

    const general = this.generalForm.getRawValue();
    const assignment = this.assignmentForm.getRawValue();

    const requesterId = this.getCurrentRequesterId();
    if (!requesterId) {
      this.setFormError('No pudimos identificar al solicitante. Inicia sesión nuevamente.');
      return;
    }

    const statusId = this.getDefaultStatusId();
    if (!statusId) {
      this.setFormError('No pudimos asignar el estado "En espera". Actualiza los catálogos.');
      return;
    }

    const teamId = this.getSupportTeamId();
    if (!teamId) {
      this.setFormError('No pudimos ubicar el equipo Soporte. Revisa los catálogos.');
      return;
    }

    const assigneeId = assignment.assignee_id?.trim();

    const formData = new FormData();
    formData.append('code', general.code.trim());
    formData.append('note', (general.note ?? '').trim());
    formData.append('request_type_id', general.request_type_id.trim());
    formData.append('priority_type_id', general.priority_type_id.trim());
    formData.append('status_type_id', statusId);
    formData.append('requester_id', requesterId);
    formData.append('team_id', teamId);
    this.appendIfValue(formData, 'assignee_id', assigneeId);

    this.attachments().forEach(file => formData.append('attachments', file));

    this.submitting.set(true);
    this.ticketService.createTicket(formData).subscribe({
      next: () => {
        this.ticketService.loadTickets();
        this.submitting.set(false);
        this.submitSuccess.set(true);
        this.resetForm(true);
        this.sidenavState.close();
      },
      error: () => {
        this.submitting.set(false);
        this.setFormError('No pudimos crear el ticket. Intenta de nuevo.');
      },

      complete: () => {
        this.resetForm();
        this.snackBar.open('Ticket enviado', 'Cerrar', {
          duration: 3500,
          horizontalPosition: 'center',
          verticalPosition: 'bottom',
          panelClass: ['snackbar-success'],
        });
      }
    });
  }

  onAttachmentsSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files?.length) {
      this.appendAttachments(input.files);
      input.value = '';
    }
  }

  onDropzoneDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    if (!this.dropzoneActive()) {
      this.dropzoneActive.set(true);
    }
  }

  onDropzoneDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    if (event.currentTarget === event.target) {
      this.dropzoneActive.set(false);
    }
  }

  onDropzoneDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.dropzoneActive.set(false);
    const files = event.dataTransfer?.files;
    if (files?.length) {
      this.appendAttachments(files);
    }
  }

  removeAttachment(index: number): void {
    this.attachments.update(previous => {
      return previous.filter((_, idx) => idx !== index);
    });
  }

  attachmentSize(file: File): string {
    const bytes = file.size;
    if (!Number.isFinite(bytes) || bytes <= 0) {
      return '';
    }
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
  }

  typeOptionLabel(option?: LevelType | null): string {
    if (!option) {
      return 'Tipo sin descripción';
    }

    const label = option.description?.trim();
    if (label && label.length > 0) {
      return label;
    }

    const numeric = option.value;
    if (numeric !== null && numeric !== undefined) {
      return `Tipo ${numeric}`;
    }
    return 'Tipo sin descripción';
  }

  priorityIndicatorClass(option: LevelType): string {
    return `priority-indicator--${this.resolvePriorityLevel(option)}`;
  }

  userOptionLabel(option: SupportUser): string {
    const profileName = option.user_profile_relationship?.full_name?.trim();
    if (profileName && profileName.length > 0) {
      return profileName;
    }
    const rootFullName = option.full_name?.trim();
    if (rootFullName && rootFullName.length > 0) {
      return rootFullName;
    }
    const username = option.username?.trim();
    if (username && username.length > 0) {
      return username;
    }
    const email = option.user_profile_relationship?.email?.trim();
    if (email && email.length > 0) {
      return email;
    }
    return 'Usuario sin nombre';
  }

  private resetForm(preserveSelections = false): void {
    const baseCode = `TCKT-${this.getNumericCode()}`;
    this.generalForm.reset({
      code: baseCode,
      request_type_id: preserveSelections ? this.generalForm.get('request_type_id')?.value ?? '' : '',
      priority_type_id: preserveSelections ? this.generalForm.get('priority_type_id')?.value ?? '' : '',
      note: '',
    });
    this.assignmentForm.reset({
      assignee_id: preserveSelections ? this.assignmentForm.get('assignee_id')?.value ?? '' : '',
    });
    this.attachments.set([]);
    this.dropzoneActive.set(false);
    this.stepper?.reset();
  }

  private assignNewCode(): void {
    this.generalForm.patchValue({
      code: `TCKT-${this.getNumericCode()}`,
    });
  }

  private toggleControlDisabled(control: AbstractControl | null | undefined, disabled: boolean): void {
    if (!control) {
      return;
    }
    if (disabled && control.enabled) {
      control.disable({ emitEvent: false });
    } else if (!disabled && control.disabled) {
      control.enable({ emitEvent: false });
    }
  }

  private appendAttachments(collection: FileList | File[]): void {
    const incoming = Array.from(collection ?? []).filter(file => file instanceof File);
    if (!incoming.length) {
      return;
    }
    this.attachments.update(previous => [...previous, ...incoming]);
  }

  private appendIfValue(formData: FormData, key: string, value?: string | null): void {
    if (!value) {
      return;
    }
    formData.append(key, value);
  }

  private setFormError(message: string): void {
    this.formErrorMessage.set(message);
  }

  private getNumericCode(length = 6): string {
    if (typeof crypto !== 'undefined' && 'getRandomValues' in crypto) {
      const bytes = new Uint8Array(length);
      crypto.getRandomValues(bytes);
      let out = '';
      for (let i = 0; i < length; i++) out += (bytes[i] % 10).toString();
      return out;
    }
    return Array.from({ length }, () => Math.floor(Math.random() * 10)).join('');
  }

  private getCurrentRequesterId(): string | null {
    return this.authentication.getCurrentUserId();
  }

  private getDefaultStatusId(): string | null {
    const statuses = this.statusTypes();
    const target = this.normalizeLabel('en espera');
    const status = statuses.find(item => this.normalizeLabel(item.description) === target);
    return status?.id ?? null;
  }

  private getSupportTeamId(): string | null {
    const teams = this.teamService.allTeams();
    const target = this.normalizeLabel('soporte');
    const match = teams.find(team => this.normalizeLabel(team.description) === target);
    return match?.id ?? null;
  }

  private normalizeLabel(value: string | null | undefined): string {
    if (!value) {
      return '';
    }
    return value
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLocaleLowerCase('es')
      .trim();
  }

  private resolvePriorityLevel(option?: LevelType | null): 'low' | 'medium' | 'high' | 'urgent' | 'default' {
    if (!option) {
      return 'default';
    }

    const numeric = option.value ?? null;
    if (typeof numeric === 'number' && Number.isFinite(numeric)) {
      if (numeric <= 1) return 'low';
      if (numeric === 2) return 'medium';
      if (numeric === 3) return 'high';
      if (numeric >= 4) return 'urgent';
    }

    const label = this.normalizeLabel(option.description);
    if (label.includes('baja') || label.includes('low')) return 'low';
    if (label.includes('media') || label.includes('medio') || label.includes('medium')) return 'medium';
    if (label.includes('alta') || label.includes('high')) return 'high';
    if (label.includes('critica') || label.includes('urgente') || label.includes('urgent')) return 'urgent';
    return 'default';
  }



}
