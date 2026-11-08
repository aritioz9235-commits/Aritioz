import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { AssistantResponse, LaunchOSWorkspace, projectsViewForClick } from './launchos-workspace';

describe('LaunchOSWorkspace sidebar', () => {
  it('does not render saved or recent project lists', () => {
    const workspace = renderToStaticMarkup(createElement(LaunchOSWorkspace));

    expect(workspace).not.toContain('Pinned');
    expect(workspace).not.toContain('Recents');
    expect(workspace).not.toContain('Aria Essentials launch');
    expect(workspace).not.toContain('New skincare collection');
  });
});

describe('Projects sidebar item', () => {
  it('opens Local projects on a single click', () => {
    expect(projectsViewForClick(1)).toBe('projects');
  });

  it('closes Local projects on a double click', () => {
    expect(projectsViewForClick(2)).toBe('conversation');
  });

  it('stays closed through extra clicks in the same sequence', () => {
    expect(projectsViewForClick(3)).toBe('conversation');
  });
});

describe('AssistantResponse', () => {
  it('renders the assistant text without exposing provider or model metadata', () => {
    const markup = renderToStaticMarkup(createElement(AssistantResponse, {
      answer: 'Hello! How can I help you today?',
      error: '',
      loading: false,
    }));

    expect(markup).toContain('Hello! How can I help you today?');
    expect(markup).not.toContain('Aritioz');
    expect(markup).not.toContain('ollama');
    expect(markup).not.toContain('gemma4:31b-cloud');
  });
});
