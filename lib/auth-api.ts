import { getBackendBaseUrl } from '@/lib/backend-url';

export type AuthSession = {
  access_token: string;
  token_type: 'bearer';
  user: { id: string; email: string; display_name: string | null };
};

type AuthPayload = { email: string; password: string };

async function authRequest(path: string, body: AuthPayload & { name?: string }): Promise<AuthSession> {
  const response = await fetch(`${getBackendBaseUrl()}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await response.json().catch(() => null) as AuthSession | { detail?: string; error?: { message?: string } } | null;
  if (!response.ok) {
    throw new Error((data && 'detail' in data && data.detail) || (data && 'error' in data && data.error?.message) || 'Unable to authenticate. Please try again.');
  }
  return data as AuthSession;
}

export const login = (payload: AuthPayload) => authRequest('/api/auth/login', payload);
export const signup = (payload: AuthPayload & { name: string }) => authRequest('/api/auth/register', payload);

export function saveSession(session: AuthSession, persistent: boolean): void {
  const storage = persistent ? window.localStorage : window.sessionStorage;
  window.localStorage.removeItem('aritioz_auth');
  window.sessionStorage.removeItem('aritioz_auth');
  storage.setItem('aritioz_auth', JSON.stringify(session));
}
