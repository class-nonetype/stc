import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class FormService {
  readonly opened = signal<boolean>(false);

  open(): void {
    if (this.opened()) return;
    this.opened.set(true);
    this.toggleBodyScroll(true);
  }

  close(): void {
    if (!this.opened()) return;
    this.opened.set(false);
    this.toggleBodyScroll(false);
  }

  toggle(): void {
    this.opened() ? this.close() : this.open();
  }

  private toggleBodyScroll(disable: boolean): void {
    if (typeof document === 'undefined') return;
    document.body.classList.toggle('ticket-sidenav-open', disable);
  }
}
