import { afterEach, describe, expect, it, vi } from 'vitest';

import { sendChatMessage } from './chat-api';
import { validateImageFile } from './image-file';

describe('sendChatMessage', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('posts to the configured backend and returns the AI response', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ success: true, provider: 'gemini', model: 'configured', response: 'Hello' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    vi.stubGlobal('fetch', fetchMock);

    await expect(sendChatMessage('Plan my launch', 'https://api.example.com')).resolves.toMatchObject({ response: 'Hello' });
    expect(fetchMock).toHaveBeenCalledWith(
      'https://api.example.com/api/chat',
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('returns a readable API error without leaking unknown response fields', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ error: { message: 'No AI provider is currently available' }, secret: 'hidden' }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' },
      }),
    ));

    await expect(sendChatMessage('Hello')).rejects.toThrow('No AI provider is currently available');
  });

  it('includes a validated image data URL in the chat request', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ success: true, provider: 'nvidia', model: 'vision', response: 'A product' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    vi.stubGlobal('fetch', fetchMock);

    await sendChatMessage('What is this?', '', undefined, 'data:image/png;base64,aGVsbG8=');

    const request = fetchMock.mock.calls[0][1] as RequestInit;
    expect(typeof request.body).toBe('string');
    expect(JSON.parse(request.body as string)).toEqual({
      message: 'What is this?',
      provider: 'auto',
      image_url: 'data:image/png;base64,aGVsbG8=',
    });
  });

  it('rejects unsupported or oversized image files before upload', () => {
    expect(() => validateImageFile({ type: 'image/svg+xml', size: 100 })).toThrow(/JPEG, PNG, or WebP/);
    expect(() => validateImageFile({ type: 'image/png', size: 5 * 1024 * 1024 + 1 })).toThrow(/5 MB/);
    expect(() => validateImageFile({ type: 'image/webp', size: 1024 })).not.toThrow();
  });
});
