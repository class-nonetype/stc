import { ChangeDetectionStrategy, Component, Input, inject } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { TeamService } from '../../services/team.service';

@Component({
  selector: 'select-list',
  standalone: true,
  templateUrl: 'select-list.component.html',
  styleUrls: ['select-list.component.css'],
  imports: [MatFormFieldModule, MatSelectModule, ReactiveFormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SelectListComponent {
  @Input({ required: true }) control!: FormControl<string>;
  @Input() label = 'Grupo de trabajo';

  private readonly teamService = inject(TeamService);

  readonly teams = this.teamService.allTeams;
  readonly loading = this.teamService.loading;
  readonly hasError = this.teamService.hasError;

  constructor() {
    if (!this.teams().length && !this.loading()) {
      this.teamService.loadTeams();
    }
  }
}
