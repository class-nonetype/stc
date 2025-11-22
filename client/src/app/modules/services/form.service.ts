import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class FormService {
  readonly opened = signal<boolean>(false);
  readonly context = signal<string | null>(null);

  private bodyClass: string | null = null;

  open(context: string): void {
    const previousContext = this.context();
    if (previousContext && previousContext !== context) {
      this.updateBodyClass(false, previousContext);
    }

    this.context.set(context);
    this.opened.set(true);
    this.updateBodyClass(true, context);
  }

  close(context?: string): void {
    if (!this.opened()) return;

    const activeContext = context ?? this.context();
    this.opened.set(false);
    this.context.set(null);

    if (activeContext) {
      this.updateBodyClass(false, activeContext);
    }
  }

  toggle(context: string): void {
    this.isOpen(context) ? this.close(context) : this.open(context);
  }

  isOpen(context: string): boolean {
    return this.opened() && this.context() === context;
  }

  private updateBodyClass(enable: boolean, context: string): void {
    if (typeof document === 'undefined') return;

    const className = `${context}-sidenav-open`;

    if (enable) {
      if (this.bodyClass && this.bodyClass !== className) {
        document.body.classList.remove(this.bodyClass);
      }
      document.body.classList.add(className);
      this.bodyClass = className;
      return;
    }

    document.body.classList.remove(className);
    if (this.bodyClass === className) {
      this.bodyClass = null;
    }
  }
}
