export type WorkspaceTheme = 'light' | 'dark' | 'cosmic';

export function parseWorkspaceTheme(value: string | null): WorkspaceTheme {
  return value === 'light' || value === 'cosmic' ? value : 'dark';
}
