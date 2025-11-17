export interface SignInResponse {
  client?: string;
  accessToken?: string;
  username?: string;
  userFullName?: string | null;
  team?: string | null;
}

export interface SignUpProfilePayload {
  full_name: string;
  email: string;
  is_active: boolean;
}

export interface SignUpAccountPayload {
  username: string;
  password: string;
}

export interface SignUpTeamPayload {
  id: string;
}

export interface SignUpRequestPayload {
  UserProfile: SignUpProfilePayload;
  UserAccount: SignUpAccountPayload;
  TeamGroup: SignUpTeamPayload;
}

export interface SignUpResponse {
  status: string;
  data: unknown;
}

