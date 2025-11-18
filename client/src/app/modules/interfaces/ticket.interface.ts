import type { Teams } from './team.interface';

export interface LevelType {
  id: string;
  value?: number | null;
  description?: string | null;
}

export interface TicketUserProfile {
  id: string;
  full_name: string;
  email: string;
  is_active: boolean;
}

export interface SupportUser {
  id: string;
  user_profile_id: string;
  team_id: string;
  username: string;
  full_name?: string | null;
  last_login_date?: string | null;
  created_at?: string;
  updated_at?: string;
  user_profile_relationship?: TicketUserProfile | null;
  team_relationship?: Teams | null;
}

export interface CountFinishedTickets {
  count: number;
}


export interface TicketAttachment {
  id: string;
  ticketId?: string | null;
  fileName: string;
  fileStorageName?: string | null;
  filePath?: string | null;
  fileSize?: number | null;
  mimeType?: string | null;
  createdAt?: string | null;
  url?: string | null;
}

export interface LegacyTicketUser {
  id?: string;
  displayName?: string;
  email?: string | null;
  avatarUrl?: string | null;
}

export type TicketStatusKey =
  | 'open'
  | 'in_progress'
  | 'on_hold'
  | 'resolved'
  | 'closed'
  | 'cancelled'
  | 'unknown';

export const TICKET_STATUS_KEY_BY_VALUE: Record<number, TicketStatusKey> = {
  1: 'open',
  2: 'in_progress',
  3: 'on_hold',
  4: 'resolved',
  5: 'closed',
  6: 'cancelled',
};

export const PENDING_STATUS_KEYS: readonly TicketStatusKey[] = ['open', 'in_progress', 'on_hold'];

export const STATUS_LABEL_BY_KEY: Record<TicketStatusKey, string> = {
  open: 'Abierto',
  in_progress: 'En proceso',
  on_hold: 'En espera',
  resolved: 'Resuelto',
  closed: 'Cerrado',
  cancelled: 'Cancelado',
  unknown: 'Sin estado',
};

const STATUS_KEY_BY_STRING: Record<string, TicketStatusKey> = {
  open: 'open',
  'in_progress': 'in_progress',
  'in-progress': 'in_progress',
  'in progress': 'in_progress',
  'on_hold': 'on_hold',
  'on-hold': 'on_hold',
  'on hold': 'on_hold',
  resolved: 'resolved',
  closed: 'closed',
  cancelled: 'cancelled',
  canceled: 'cancelled',
};

export const normalizeTicketStatusKey = (value: string | null | undefined): TicketStatusKey | null => {
  if (!value) return null;

  const normalized = value.trim().toLowerCase();
  const direct = STATUS_KEY_BY_STRING[normalized];

  if (direct) return direct;

  const slug = normalized.replace(/\s+/g, '_');
  return STATUS_KEY_BY_STRING[slug] ?? null;
};

export interface Ticket {
  id: string;
  code: string;
  note: string;
  requestTypeId: string | null;
  request: string | null;
  priorityTypeId: string | null;
  priority: string | null;
  statusTypeId: string | null;
  status: string | null;
  requesterId: string;
  //assigneeId: string | null;
  requester: string | null;
  //assignee: string | null;

  managerId: string | null;
  manager: string | null;

  teamId: string | null;
  duetAt: string | null;
  resolvedAt: string | null;
  closedAt: string | null;
  deletedAt: string | null;
  createdAt: string | null;
  updatedAt: string | null;
  isResolved: boolean | null;

  attachments?: TicketAttachment[];
}

export interface TicketCard {
  id: string;
  code: string;
  title: string;
  requester: string;
  statusKey: TicketStatusKey;
  statusLabel: string;
  updatedAgo: string;
  unread: boolean;
}

export interface TicketsResponse {
  data: Ticket[];
  total?: number;
}

export interface TicketCreateRequest {
  code: string;
  note: string;
  request_type_id: string;
  priority_type_id: string;
  status_type_id: string;
  requester_id: string;
  team_id?: string | null;
  assignee_id?: string | null;
  due_at?: string | null;
  resolved_at?: string | null;
  closed_at?: string | null;
  description?: string;
  title?: string;
}


export type TicketResponse = {
  id?: string;
  code?: string;
  note?: string | null;
  requestTypeId?: string | null;
  request?: string | null;
  priorityTypeId?: string | null;
  priority?: string | null;
  statusTypeId?: string | null;
  status?: string | null;
  requesterId?: string;
  managerId?: string | null;
  requester?: string | null;
  manager?: string | null;
  teamId?: string | null;
  duetAt?: string | null;
  resolvedAt?: string | null;
  closedAt?: string | null;
  deletedAt?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
  isResolved?: boolean | null;
  attachments?: TicketAttachment[] | unknown;

};

export interface TicketUpdateRequest extends Partial<TicketCreateRequest> {
  id: string;
}

export interface TicketDeleteRequest {
  id: string;
}

