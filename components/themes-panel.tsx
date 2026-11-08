import { ArrowLeft, Check } from 'lucide-react';
import type { WorkspaceTheme } from '@/lib/workspace-theme';

type ThemesPanelProps = {
  theme: WorkspaceTheme;
  onSelect: (theme: WorkspaceTheme) => void;
  onBack: () => void;
};

export function ThemesPanel({ theme, onSelect, onBack }: ThemesPanelProps) {
  return (
    <section className="themes-panel" aria-label="Themes">
      <button className="themes-panel-back" type="button" onClick={onBack}><ArrowLeft size={16} /> Back to chat</button>
      <header className="themes-panel-heading">
        <span className="workbench-kicker">APPEARANCE</span>
        <h2>Themes</h2>
        <p>Choose how your Aritioz workspace looks.</p>
      </header>
      <div className="themes-panel-choices">
        <button type="button" className="themes-panel-choice" aria-pressed={theme === 'light'} onClick={() => onSelect('light')}>
          <span className="themes-panel-preview themes-panel-preview-light" aria-hidden="true"><i /><i /><i /></span>
          <span className="themes-panel-choice-label"><strong>Light</strong><small>Bright and clear</small></span>
          {theme === 'light' && <Check size={18} aria-hidden="true" />}
        </button>
        <button type="button" className="themes-panel-choice" aria-pressed={theme === 'dark'} onClick={() => onSelect('dark')}>
          <span className="themes-panel-preview themes-panel-preview-dark" aria-hidden="true"><i /><i /><i /></span>
          <span className="themes-panel-choice-label"><strong>Dark</strong><small>Comfortable in low light</small></span>
          {theme === 'dark' && <Check size={18} aria-hidden="true" />}
        </button>
        <button type="button" className="themes-panel-choice" aria-pressed={theme === 'cosmic'} onClick={() => onSelect('cosmic')}>
          <span className="themes-panel-preview themes-panel-preview-cosmic" aria-hidden="true"><i /><i /><i /></span>
          <span className="themes-panel-choice-label"><strong>Cosmic</strong><small>Bright space, inspired by your image</small></span>
          {theme === 'cosmic' && <Check size={18} aria-hidden="true" />}
        </button>
      </div>
    </section>
  );
}
