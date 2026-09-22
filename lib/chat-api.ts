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
): Promise<ChatReply> {
  const baseUrl = backendBaseUrl.replace(/\/$/, '');
  const response = await fetch(`${baseUrl}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      provider: 'auto',
      ...(imageUrl ? { image_url: imageUrl } : {}),
    }),
    signal,
  });
  const payload = (await response.json().catch(() => ({}))) as ChatReply | ErrorEnvelope;
  if (!response.ok) {
    const errorPayload = payload as ErrorEnvelope;
    throw new Error(errorPayload.error?.message || 'Aritioz could not complete that request.');
  }
  return payload as ChatReply;
}
