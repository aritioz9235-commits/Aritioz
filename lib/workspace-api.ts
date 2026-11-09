import { getBackendBaseUrl } from './backend-url';

export interface WorkspaceFile {
  path: string;
  kind: 'file' | 'directory';
}

async function requestWorkspace<T>(path: string, init?: RequestInit): Promise<T> {
  const workspaceToken = process.env.NEXT_PUBLIC_WORKSPACE_ACCESS_TOKEN;
  if (!workspaceToken) throw new Error('Workspace access is not configured.');
  const headers = new Headers(init?.headers);
  headers.set('X-Workspace-Token', workspaceToken);
  const response = await fetch(`${getBackendBaseUrl()}/api/workspace${path}`, { ...init, headers });
  const payload = await response.json().catch(() => ({})) as T & { error?: string };
  if (!response.ok || payload.error) throw new Error(payload.error || 'Workspace request failed.');
  return payload;
}

export function getWorkspaceStatus() {
  return requestWorkspace<{ enabled: boolean; root_name: string | null }>('/status');
}

export function listWorkspaceFiles(path = '') {
  return requestWorkspace<{ enabled: boolean; files: WorkspaceFile[]; error?: string }>(`/files?path=${encodeURIComponent(path)}`);
}

export function readWorkspaceFile(path: string) {
  return requestWorkspace<{ path: string; content: string }>(`/file?path=${encodeURIComponent(path)}`);
}

export function saveWorkspaceFile(path: string, content: string) {
  return requestWorkspace<{ saved: boolean; path: string }>('/file', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path, content }),
  });
}

export function runWorkspaceCommand(command: 'test' | 'lint' | 'typecheck' | 'build') {
  return requestWorkspace<{ command: string; return_code: number; output: string }>('/command', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ command }),
  });
}
