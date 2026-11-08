import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { ThemesPanel } from './themes-panel';

describe('ThemesPanel', () => {
  it('shows Light, Dark and Cosmic choices', () => {
    const markup = renderToStaticMarkup(createElement(ThemesPanel, {
      theme: 'light',
      onSelect: () => {},
      onBack: () => {},
    }));

    expect(markup).toContain('>Themes</h2>');
    expect(markup).toContain('>Light</strong>');
    expect(markup).toContain('>Dark</strong>');
    expect(markup).toContain('>Cosmic</strong>');
    expect(markup).toContain('Back to chat');
  });

  it('marks the current theme as selected', () => {
    const markup = renderToStaticMarkup(createElement(ThemesPanel, {
      theme: 'cosmic',
      onSelect: () => {},
      onBack: () => {},
    }));

    expect(markup).toMatch(/aria-pressed="true"[^>]*>[\s\S]*?<strong>Cosmic<\/strong>/);
    expect(markup).toMatch(/aria-pressed="false"[^>]*>[\s\S]*?<strong>Dark<\/strong>/);
    expect(markup).toMatch(/aria-pressed="false"[^>]*>[\s\S]*?<strong>Light<\/strong>/);
  });
});
