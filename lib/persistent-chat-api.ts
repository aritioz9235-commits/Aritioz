import { getBackendBaseUrl } from './backend-url';

export interface PersistentConversation {
  id: string;
  organization_id: string;
  workspace_id: string;
  title: string;
  status: 'active' | 'archived' | 'deleted';
  created_at: string | null;
  updated_at: string | null;
}

export interface PersistentMessage {
  id: string;
  conversation_id: string;
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
  provider?: string | null;
  model?: string | null;
  created_at: string | null;
}

async function request<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getBackendBaseUrl()}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, ...Object.fromEntries(new Headers(init?.headers).entries()) },
  });
  const payload = await response.json().catch(() => ({})) as T & { detail?: string; error?: { message?: string } };
  if (!response.ok) throw new Error(payload.detail || payload.error?.message || 'Aritioz request failed.');
  return payload;
}

export function createConversation(token: string, organizationId: string, workspaceId: string, title = 'New conversation') {
  return request<PersistentConversation>('/api/conversations', token, { method: 'POST', body: JSON.stringify({ organization_id: organizationId, workspace_id: workspaceId, title }) });
}

export function listConversations(token: string, workspaceId: string) {
  return request<{ items: PersistentConversation[] }>('/api/conversations?workspace_id=' + encodeURIComponent(workspaceId), token);
}

export function listMessages(token: string, conversationId: string) {
  return request<{ items: PersistentMessage[] }>(`/api/conversations/${conversationId}/messages`, token);
}

export function sendPersistentChat(token: string, conversationId: string, message: string) {
  return request<{ success: true; provider: string; model: string; response: string }>(`/api/conversations/${conversationId}/chat`, token, { method: 'POST', body: JSON.stringify({ message }) });
}
