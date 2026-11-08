import { describe, expect, it, vi } from 'vitest';
import { getBackendBaseUrl } from './backend-url';

describe('getBackendBaseUrl', () => {
  it('uses the configured backend during local development', () => {
    vi.stubGlobal('window', { location: { origin: 'http://localhost:3000' } });
    expect(getBackendBaseUrl('http://127.0.0.1:8000/')).toBe('http://127.0.0.1:8000');
  });

  it('falls back to the public page origin when a production build has a local URL', () => {
    vi.stubGlobal('window', { location: { origin: 'https://www.aritioz.com' } });
    expect(getBackendBaseUrl('http://127.0.0.1:8000')).toBe('https://www.aritioz.com');
  });

  it('uses same-origin when no URL is configured', () => {
    vi.stubGlobal('window', { location: { origin: 'https://www.aritioz.com' } });
    expect(getBackendBaseUrl('')).toBe('https://www.aritioz.com');
  });
});
