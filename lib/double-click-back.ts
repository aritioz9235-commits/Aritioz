const interactiveSelector = [
  'input', 'textarea', 'button', 'a', 'select', 'option', 'label', 'form',
  'nav', 'aside', 'article', 'details', 'summary',
  '[role="button"]', '[role="link"]', '[role="menu"]', '[role="menuitem"]',
  '[role="switch"]', '[role="tab"]', '[role="listbox"]', '[role="option"]',
  '[contenteditable]', '[data-no-double-back]', '[tabindex]:not(.project-dialog)',
  '[class*="card"]', '[role="dialog"]:not(.project-dialog)',
].join(', ');

type DoubleClickEvent = {
  detail: number;
  button: number;
  target: unknown;
};

export function handleDoubleClickBack(event: DoubleClickEvent, back: () => void, selection = ''): void {
  if (event.detail !== 2 || event.button !== 0) return;
  const target = event.target as { closest?: (selector: string) => unknown } | null;
  if (!target || typeof target.closest !== 'function') return;
  if (target.closest(interactiveSelector)) return;
  if (selection && target.closest('p, pre, code, blockquote')) return;
  back();
}

export function navigateWorkspaceBack(
  history: { length: number; state: unknown; back: () => void },
  entry: string,
  fallback: (route: string) => void,
): void {
  const state = history.state as { aritiozWorkspace?: string } | null;
  if (history.length > 1 && state?.aritiozWorkspace === entry) {
    history.back();
  } else {
    fallback('/');
  }
}
