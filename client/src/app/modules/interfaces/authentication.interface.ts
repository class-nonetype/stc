export interface SignInResponse {
  client?: string;
  access_token?: string;
  accessToken?: string;
  token?: string;
  username?: string | null;
  userFullName?: string | null;
  team?: string | null;
  expiresAt?: number;
}

export interface SignInRequest {
  username: string;
  password: string;
}

export interface RefreshResponse {
  access_token: string;
}

export interface SignOutRequest {
  authorization: string;
}

export interface Session {
  client?: string;
  accessToken: string;
  username?: string | null;
  userFullName?: string | null;
  team?: string | null;
  expiresAt?: number;
}
