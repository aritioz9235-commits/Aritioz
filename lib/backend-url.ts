const LOCAL_BACKEND_HOSTS = new Set(['localhost', '127.0.0.1', '[::1]']);

/**
 * Resolve the API endpoint for both local development and same-origin deploys.
 *
 * A public build can accidentally contain the local development URL. In a
 * browser, that URL points at the visitor's computer, not the server running
 * Aritioz, so use the current origin for non-local pages instead.
 */
export function getBackendBaseUrl(configuredUrl = process.env.NEXT_PUBLIC_AI_BACKEND_URL ?? '') {
  const configured = configuredUrl.trim().replace(/\/$/, '');
  if (typeof window === 'undefined') return configured;

  const currentOrigin = window.location.origin;
  if (!configured) return currentOrigin;

  try {
    const parsed = new URL(configured, currentOrigin);
    const current = new URL(currentOrigin);
    if (LOCAL_BACKEND_HOSTS.has(parsed.hostname) && !LOCAL_BACKEND_HOSTS.has(current.hostname)) {
      return currentOrigin;
    }
    return parsed.origin;
  } catch {
    return currentOrigin;
  }
}
