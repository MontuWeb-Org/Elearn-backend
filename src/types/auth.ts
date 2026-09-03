import type { RoleName } from '../models/index.js';

export type RoutingTarget = 'instructor' | 'assistant' | 'parent' | 'student';

export interface AuthContext {
  userId: string;
  sessionId: string;
  roles: RoleName[];
}

export interface AccessTokenPayload {
  sub: string;
  sid: string;
  roles: RoleName[];
  typ: 'access';
}

export interface CurrentUserDto {
  id: string;
  email: string;
  full_name: string;
  avatar_url: string | null;
  roles: RoleName[];
  routing_target: RoutingTarget;
}

export interface AuthSessionDto {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user: CurrentUserDto;
}

export interface RequestMeta {
  userAgent?: string;
  ipAddress?: string;
}

export interface SessionDto {
  user_session_id: string;
  user_agent: string | null;
  ip_address: string | null;
  is_revoked: boolean;
  remember_me: boolean;
  is_current: boolean;
  expires_at: string;
  created_at: string;
}
