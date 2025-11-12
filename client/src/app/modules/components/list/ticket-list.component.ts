import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  effect,
  input,
  output,
  signal,
} from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import type { Ticket } from '../../interfaces/ticket.interface';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';



type NullableDate = string | null;

interface TicketFilters {
  text: string;                 // busca en code, requester, request, note
  status: string[];             // múltiples estados
  request: string[];            // tipos (request)
  priority: string[];           // prioridades
  requester: string;            // solicitante
  unreadOnly: boolean;          // solo no resueltos
  //dateFrom: NullableDate;       // ISO (createdAt/updatedAt)
  //dateTo: NullableDate;         // ISO
}




@Component({
  selector: 'ticket-list',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    MatPaginatorModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule
  ],
  templateUrl: './ticket-list.component.html',
  styleUrl: './ticket-list.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TicketListComponent {
  readonly tickets = input<Ticket[]>([]);
  readonly loading = input<boolean>(false);
  readonly hasError = input<boolean>(false);

  readonly open = output<Ticket>();
  readonly retry = output<void>();


  readonly pageIndex = signal(0);
  readonly pageSize = signal(6);
  readonly pageSizeOptions = [6, 12, 24];

  readonly filters = signal<TicketFilters>({
    text: '',
    status: [],
    request: [],
    priority: [],
    requester: '',
    unreadOnly: false,
    //dateFrom: null,
    //dateTo: null,
  });


  readonly statusOptions = computed(() => Array.from(new Set(
    this.tickets().map(t => (t.status ?? (t.isResolved ? 'Resuelto' : 'En proceso')))
  )).filter(Boolean));

  readonly requestOptions = computed(() => Array.from(new Set(
    this.tickets().map(t => t.request).filter(Boolean) as string[]
  )));

  readonly priorityOptions = computed(() => Array.from(new Set(
    this.tickets().map(t => t.priority).filter(Boolean) as string[]
  )));

  private readonly relativeTimeFormatter = new Intl.RelativeTimeFormat('es', { numeric: 'auto' });


  // 1) filtra
  readonly filteredTickets = computed(() => {
    const f = this.filters();
    const list = this.tickets();

    const norm = (v?: string | null) => (v ?? '').toLowerCase().trim();

    //const fromTs = f.dateFrom ? Date.parse(f.dateFrom) : null;
    //const toTs   = f.dateTo   ? Date.parse(f.dateTo)   : null;

    return list.filter(t => {
      // text
      const haystack = [
        t.code,
        t.request,
        t.priority,
        t.requester,
        t.note
      ].map(norm).join(' ');

      const textOk = !f.text || haystack.includes(norm(f.text));

      // status
      const statusKey = t.status ?? (t.isResolved ? 'Resuelto' : 'En proceso');
      const statusOk = f.status.length === 0 || f.status.includes(statusKey);

      // request (tipo)
      const requestOk = f.request.length === 0 || (t.request ? f.request.includes(t.request) : false);

      // priority
      const priorityOk = f.priority.length === 0 || (t.priority ? f.priority.includes(t.priority) : false);

      // requester
      const requesterOk = !f.requester || norm(t.requester)?.includes(norm(f.requester)) || norm(t.requesterId)?.includes(norm(f.requester));

      // unreadOnly
      const unreadOk = !f.unreadOnly || t.isResolved === false;

      // rangos de fecha (usa updatedAt || createdAt)
      //const baseIso = t.updatedAt ?? t.createdAt ?? null;
      //let dateOk = true;
      //if (fromTs || toTs) {
      //  if (!baseIso) dateOk = false;
      //  else {
      //    const ts = Date.parse(baseIso);
      //    if (Number.isNaN(ts)) dateOk = false;
      //    if (dateOk && fromTs && ts < fromTs) dateOk = false;
      //    if (dateOk && toTs && ts > toTs) dateOk = false;
      //  }
      //}

      return textOk && statusOk && requestOk && priorityOk && requesterOk && unreadOk // && dateOk;
    });
  });



  readonly visibleTickets = computed(() => {
    const all = this.filteredTickets();   // <-- antes: this.tickets()
    if (!all.length) return all;

    const start = this.pageIndex() * this.pageSize();
    return all.slice(start, start + this.pageSize());
  });

  constructor() {
    effect(() => {
      // si cambia el tamaño de página o la lista, clamp del pageIndex
      const total = this.filteredTickets().length;
      const size = this.pageSize();
      const maxPage = Math.max(Math.ceil(total / size) - 1, 0);
      if (this.pageIndex() > maxPage) this.pageIndex.set(maxPage);
      console.log('filtered len', this.filteredTickets().length, 'of', this.tickets().length, 'filters', this.filters());

    });
  }

  patchFilters<K extends keyof TicketFilters>(key: K, value: TicketFilters[K]): void {
    this.filters.update(f => ({ ...f, [key]: value }));
    this.pageIndex.set(0); // resetea a la primera página al cambiar filtros
    //console.log('filter change', key, value);

  }

  resetFilters(): void {
    this.filters.set({
      text: '',
      status: [],
      request: [],
      priority: [],
      requester: '',
      unreadOnly: false,
      //dateFrom: null,
      //dateTo: null,
    });
    this.pageIndex.set(0);
  }


  onOpen(ticket: Ticket): void {
    this.open.emit(ticket);
  }

  onRetry(): void {
    this.retry.emit();
  }

  onPageChange(event: PageEvent): void {
    this.pageIndex.set(event.pageIndex);
    this.pageSize.set(event.pageSize);
  }

  statusKey(ticket: Ticket): string {
    const base = ticket.status?.trim().toLowerCase().replace(/\s+/g, '_');
    if (base && base.length) {
      return base;
    }
    if (ticket.isResolved === true) return 'resolved';
    return 'open';
  }

  statusLabel(ticket: Ticket): string {
    return ticket.status ?? (ticket.isResolved ? 'Resuelto' : 'En proceso');
  }

  isUnread(ticket: Ticket): boolean {
    return ticket.isResolved === false;
  }

  requesterLabel(ticket: Ticket): string {
    return ticket.requester?.trim() || ticket.requesterId || 'Sin solicitante';
  }

  titleLabel(ticket: Ticket): string {
    return ticket.request?.trim() || ticket.note?.trim() || ticket.code;
  }

  updatedAgo(ticket: Ticket): string {
    return this.formatRelativeTime(ticket.updatedAt ?? ticket.createdAt);
  }

  // dd/MM/yyyy HH:mm[:ss]   o   dd/MM/yyyy hh:mm[:ss] AM/PM
  private parseDMYFlexible(input: string): number | null {
    const s = input.trim().replace(/\s+/g, ' ');

    // day/month/year hour:minute[:second] [AM|PM]
    const re = /^(\d{1,2})\/(\d{1,2})\/(\d{2,4})\s+(\d{1,2}):([0-5]\d)(?::([0-5]\d))?\s*([AaPp][Mm])?$/;
    const m = re.exec(s);
    if (!m) return null;

    const day = Number(m[1]);
    const month = Number(m[2]);
    const ystr = m[3];
    let year = ystr.length === 2 ? 2000 + Number(ystr) : Number(ystr);

    let hour = Number(m[4]);
    const minute = Number(m[5]);
    const second = m[6] ? Number(m[6]) : 0;
    const ampm = m[7] ? m[7].toUpperCase() : null; // 'AM' | 'PM' | null

    // validaciones básicas
    if (month < 1 || month > 12) return null;
    if (day < 1 || day > 31) return null;
    if (hour > 23 || minute > 59 || second > 59) return null;

    // Normalización 12h/24h:
    if (ampm && hour <= 12) {
      // 12h con AM/PM
      hour = hour % 12;           // 12 → 0
      if (ampm === 'PM') hour += 12;
    }
    // Si hora > 12 y hay AM/PM, lo ignoramos (ya es 24h válido)

    const d = new Date(year, month - 1, day, hour, minute, second);

    // Evita "overflow" silencioso (p. ej. 31/11 → 01/12)
    if (
      d.getFullYear() !== year ||
      d.getMonth() !== month - 1 ||
      d.getDate() !== day ||
      d.getHours() !== hour ||
      d.getMinutes() !== minute ||
      d.getSeconds() !== second
    ) return null;

    return d.getTime();
  }



  private formatRelativeTime(iso?: string | null): string {
    if (!iso) return 'Sin fecha';

    const ts = this.parseDMYFlexible(iso) ?? Date.parse(iso);
    if (ts == null || Number.isNaN(ts)) return 'Sin fecha';

    const divisions: Array<{ amount: number; unit: Intl.RelativeTimeFormatUnit }> = [
      { amount: 60, unit: 'second' },
      { amount: 60, unit: 'minute' },
      { amount: 24, unit: 'hour' },
      { amount: 7, unit: 'day' },
      { amount: 4.34524, unit: 'week' },
      { amount: 12, unit: 'month' },
      { amount: Infinity, unit: 'year' },
    ];

    let duration = (ts - Date.now()) / 1000;
    for (const div of divisions) {
      if (Math.abs(duration) < div.amount) {
        return this.relativeTimeFormatter.format(Math.round(duration), div.unit);
      }
      duration /= div.amount;
    }
    return this.relativeTimeFormatter.format(0, 'second');
  }


}
