import { prisma } from '../../config/database.js';
import { RoleName, type User } from '../../models/index.js';
import type {
  AuthSessionDto,
  CurrentUserDto,
  RequestMeta,
  RoutingTarget,
} from '../../types/auth.js';
import { ACCESS_TOKEN_TTL_SECONDS, HttpError } from '../../utils/index.js';
import { dummyPasswordCheck, verifyPassword } from './password.service.js';
import { createSession, rotateSession } from './session.service.js';
import { signAccessToken } from './token.service.js';

const userWithRoles = {
  roles: { include: { role: true } },
} as const;

type UserWithRoles = User & {
  roles: { role: { name: RoleName } }[];
};

const ROUTING_PRIORITY: ReadonlyArray<{ role: RoleName; target: RoutingTarget }> = [
  { role: RoleName.TEACHER, target: 'instructor' },
  { role: RoleName.ASSISTANT, target: 'assistant' },
  { role: RoleName.PARENT, target: 'parent' },
  { role: RoleName.STUDENT, target: 'student' },
];

export const resolveRoutingTarget = (roles: RoleName[]): RoutingTarget | null => {
  for (const entry of ROUTING_PRIORITY) {
    if (roles.includes(entry.role)) {
      return entry.target;
    }
  }
  return null;
};

const roleNames = (user: UserWithRoles): RoleName[] =>
  user.roles.map((assignment) => assignment.role.name);

const toCurrentUser = (user: UserWithRoles): CurrentUserDto => {
  const roles = roleNames(user);
  const routingTarget = resolveRoutingTarget(roles);
  if (routingTarget === null) {
    throw HttpError.forbidden('No routable role', 'INSUFFICIENT_SCOPE');
  }

  return {
    id: user.id,
    email: user.email,
    full_name: user.fullName,
    avatar_url: user.avatarUrl,
    roles,
    routing_target: routingTarget,
  };
};

const issueAuthSession = async (
  user: UserWithRoles,
  rememberMe: boolean,
  meta: RequestMeta,
): Promise<AuthSessionDto> => {
  const currentUser = toCurrentUser(user);
  const { sessionId, refreshToken } = await createSession(user.id, rememberMe, meta);
  const accessToken = signAccessToken({
    sub: user.id,
    sid: sessionId,
    roles: currentUser.roles,
    typ: 'access',
  });

  return {
    access_token: accessToken,
    refresh_token: refreshToken,
    expires_in: ACCESS_TOKEN_TTL_SECONDS,
    user: currentUser,
  };
};

const loadUserWithRoles = async (userId: string): Promise<UserWithRoles | null> =>
  prisma.user.findUnique({
    where: { id: userId },
    include: userWithRoles,
  });

export const login = async (
  email: string,
  password: string,
  rememberMe: boolean,
  meta: RequestMeta,
): Promise<AuthSessionDto> => {
  const user = await prisma.user.findUnique({
    where: { email: email.toLowerCase() },
    include: userWithRoles,
  });

  if (user === null) {
    await dummyPasswordCheck(password);
    throw HttpError.unauthorized('Invalid credentials', 'INVALID_CREDENTIALS');
  }

  const passwordOk = await verifyPassword(password, user.passwordHash);
  if (!passwordOk) {
    throw HttpError.unauthorized('Invalid credentials', 'INVALID_CREDENTIALS');
  }

  if (!user.isActive) {
    throw HttpError.forbidden('Account disabled', 'ACCOUNT_DISABLED');
  }

  await prisma.user.update({
    where: { id: user.id },
    data: { lastLoginAt: new Date() },
  });

  return issueAuthSession(user, rememberMe, meta);
};

export const refresh = async (refreshToken: string): Promise<AuthSessionDto> => {
  const rotated = await rotateSession(refreshToken);
  if (rotated === null) {
    throw HttpError.unauthorized('Invalid credentials', 'INVALID_CREDENTIALS');
  }

  const user = await loadUserWithRoles(rotated.userId);
  if (user === null || !user.isActive) {
    throw HttpError.unauthorized('Invalid credentials', 'INVALID_CREDENTIALS');
  }

  const currentUser = toCurrentUser(user);
  const accessToken = signAccessToken({
    sub: user.id,
    sid: rotated.sessionId,
    roles: currentUser.roles,
    typ: 'access',
  });

  return {
    access_token: accessToken,
    refresh_token: rotated.refreshToken,
    expires_in: ACCESS_TOKEN_TTL_SECONDS,
    user: currentUser,
  };
};

export const getCurrentUser = async (userId: string): Promise<CurrentUserDto> => {
  const user = await loadUserWithRoles(userId);
  if (user === null || !user.isActive) {
    throw HttpError.forbidden('Account disabled', 'ACCOUNT_DISABLED');
  }
  return toCurrentUser(user);
};
