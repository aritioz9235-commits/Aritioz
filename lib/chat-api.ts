import { getBackendBaseUrl } from './backend-url';

export interface ChatReply {
  success: true;
  provider: string;
  model: string;
  response: string;
}

interface ErrorEnvelope {
  error?: { message?: string };
}

export async function sendChatMessage(
  message: string,
  backendBaseUrl = process.env.NEXT_PUBLIC_AI_BACKEND_URL ?? '',
  signal?: AbortSignal,
  imageUrl?: string,
  mode: 'chat' | 'work' = 'chat',
): Promise<ChatReply> {
  const baseUrl = getBackendBaseUrl(backendBaseUrl);
  let response: Response;
  try {
    response = await fetch(`${baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        provider: 'auto',
        ...(mode === 'work' ? { max_tokens: 8192 } : {}),
        ...(mode === 'work' ? {
          system_prompt: 'You are Aritioz Work, a software engineering assistant working with the connected local project. Analyze the supplied active file and task. For a code edit confined to that file, first explain the intended change briefly, then output the entire replacement file in this exact format: a line `<<<FILE:<exact supplied path>>>`, the complete new file contents, and a final line `<<<END_FILE>>>`. Do not use this format for diffs or partial snippets. Never invent a path or claim that you inspected files, changed files, ran commands, or tests unless their results are explicitly included in the conversation. If the task needs other files, ask the user to open them. Include useful verification commands. Flag destructive or irreversible actions and ask before proceeding.',
        } : {}),
        ...(imageUrl ? { image_url: imageUrl } : {}),
      }),
      signal,
    });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error('Aritioz backend is unreachable. Start the API server or check the deployment /api proxy.');
    }
    throw error;
  }
  const payload = (await response.json().catch(() => ({}))) as ChatReply | ErrorEnvelope;
  if (!response.ok) {
    const errorPayload = payload as ErrorEnvelope;
    throw new Error(errorPayload.error?.message || 'Aritioz could not complete that request.');
  }
  return payload as ChatReply;
}

export function extractWorkFileDraft(response: string, path: string): string | null {
  const start = `<<<FILE:${path}>>>`;
  const startIndex = response.indexOf(start);
  if (startIndex < 0) return null;
  const contentStart = response.indexOf('\n', startIndex + start.length);
  if (contentStart < 0) return null;
  const endIndex = response.indexOf('<<<END_FILE>>>', contentStart + 1);
  if (endIndex < 0) return null;
  const draft = response.slice(contentStart + 1, endIndex).replace(/\n+$/, '');
  return draft || null;
}
