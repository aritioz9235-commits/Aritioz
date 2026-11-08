import { describe, expect, it } from 'vitest';

import { parseWorkspaceTheme } from './workspace-theme';

describe('parseWorkspaceTheme', () => {
  it('restores each selectable theme', () => {
    expect(parseWorkspaceTheme('light')).toBe('light');
    expect(parseWorkspaceTheme('dark')).toBe('dark');
    expect(parseWorkspaceTheme('cosmic')).toBe('cosmic');
  });

  it('defaults to dark for missing or unrecognized values', () => {
    expect(parseWorkspaceTheme(null)).toBe('dark');
    expect(parseWorkspaceTheme('other')).toBe('dark');
  });
});
