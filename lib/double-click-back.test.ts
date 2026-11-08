import { describe, expect, it, vi } from 'vitest';

import { handleDoubleClickBack, navigateWorkspaceBack } from './double-click-back';

function doubleClick(targetSelector: string | null, detail = 2) {
  return {
    detail,
    button: 0,
    target: { closest: vi.fn((selector: string) => targetSelector && selector.split(',').map((part) => part.trim()).includes(targetSelector) ? {} : null) },
  };
}

describe('double-click back', () => {
  it('does nothing for a single click', () => {
    const back = vi.fn();
    handleDoubleClickBack(doubleClick(null, 1), back);
    expect(back).not.toHaveBeenCalled();
  });

  it('goes back on a background double-click', () => {
    const back = vi.fn();
    handleDoubleClickBack(doubleClick(null), back);
    expect(back).toHaveBeenCalledOnce();
  });

  it.each(['input', 'textarea', 'button', 'a', 'select', 'nav', 'aside', '[role="menuitem"]', '[role="switch"]', '[contenteditable]', '[data-no-double-back]', 'article', '[class*="card"]'])('ignores a double-click inside %s', (selector) => {
    const back = vi.fn();
    handleDoubleClickBack(doubleClick(selector), back);
    expect(back).not.toHaveBeenCalled();
  });

  it('goes back on the page even when a previous text selection remains', () => {
    const back = vi.fn();
    handleDoubleClickBack(doubleClick(null), back, 'selected text');
    expect(back).toHaveBeenCalledOnce();
  });

  it('goes back when double-clicking the workspace heading', () => {
    const back = vi.fn();
    handleDoubleClickBack(doubleClick('h2'), back, 'selected heading');
    expect(back).toHaveBeenCalledOnce();
  });

  it('keeps text selection inside paragraph content', () => {
    const back = vi.fn();
    handleDoubleClickBack(doubleClick('p'), back, 'selected paragraph');
    expect(back).not.toHaveBeenCalled();
  });

  it('uses browser back for the workspace history entry', () => {
    const back = vi.fn();
    const fallback = vi.fn();
    navigateWorkspaceBack({ length: 2, state: { aritiozWorkspace: 'entry' }, back }, 'entry', fallback);
    expect(back).toHaveBeenCalledOnce();
    expect(fallback).not.toHaveBeenCalled();
  });

  it('falls back home when application history is unavailable', () => {
    const back = vi.fn();
    const fallback = vi.fn();
    navigateWorkspaceBack({ length: 1, state: null, back }, 'entry', fallback);
    expect(back).not.toHaveBeenCalled();
    expect(fallback).toHaveBeenCalledWith('/');
  });

  it('stays in Aritioz when browser history belongs to another site', () => {
    const back = vi.fn();
    const fallback = vi.fn();
    navigateWorkspaceBack({ length: 3, state: null, back }, 'entry', fallback);
    expect(back).not.toHaveBeenCalled();
    expect(fallback).toHaveBeenCalledWith('/');
  });
});
