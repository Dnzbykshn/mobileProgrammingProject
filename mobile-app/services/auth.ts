/**
 * Auth Service — Register, Login, Logout, Profile.
 */

import { api, setAuthTokens, removeToken, getRefreshToken } from './api';

// --- Types ---
export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_premium: boolean;
}

export interface AuthSession {
  device_id: string;
  created_at: string;
  expires_at: string;
  is_current_device: boolean;
}

export interface LogoutAllResponse {
  detail: string;
  revoked_sessions: number;
}

interface TokenResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
}

// --- API Calls ---

/** Register a new account and store JWT */
export async function register(email: string, password: string, fullName?: string): Promise<User> {
  const data = await api.post<TokenResponse>('/auth/register', {
    email,
    password,
    full_name: fullName,
  });
  await setAuthTokens(data.access_token, data.refresh_token);
  return getProfile();
}

/** Login and store JWT */
export async function login(email: string, password: string): Promise<User> {
  const data = await api.post<TokenResponse>('/auth/login', {
    email,
    password,
  });
  await setAuthTokens(data.access_token, data.refresh_token);
  return getProfile();
}

/** Get current user profile */
export async function getProfile(): Promise<User> {
  return api.get<User>('/auth/me');
}

/** List active sessions for current user */
export async function getSessions(): Promise<AuthSession[]> {
  return api.get<AuthSession[]>('/auth/sessions');
}

/** Logout — clear token */
export async function logout(): Promise<void> {
  try {
    const refreshToken = await getRefreshToken();
    await api.post<{ detail: string }>('/auth/logout', {
      refresh_token: refreshToken ?? undefined,
    });
  } catch {
    // Ignore network/backend failures and still clear local auth state.
  } finally {
    await removeToken();
  }
}

/** Logout from all devices/sessions and clear local tokens */
export async function logoutAll(): Promise<LogoutAllResponse> {
  try {
    return await api.post<LogoutAllResponse>('/auth/logout-all');
  } finally {
    await removeToken();
  }
}
