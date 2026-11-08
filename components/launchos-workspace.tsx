'use client';

import { useRef, useState, useSyncExternalStore } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import {
  ArrowUp,
  Library,
  BookOpen,
  Puzzle,
  LayoutGrid,
  Clock3,
  Blend,
  PanelsTopLeft,
  ChevronDown,
  FolderClosed,
  Lightbulb,
  Menu,
  Mic,
  MoreHorizontal,
  SquarePen,
  Plus,
  Search,
  ChevronRight,
  SlidersHorizontal,
  UserCircle,
  Settings,
  LifeBuoy,
  LogOut,
  Moon,
  X,
} from 'lucide-react';
import { sendChatMessage } from '@/lib/chat-api';
import { readImageFile } from '@/lib/image-file';
import { useVoiceInput } from '@/hooks/use-voice-input';
import type { VoiceLanguage } from '@/lib/voice-input';
import { LocalProjects } from '@/components/local-projects';
import { ThemesPanel } from '@/components/themes-panel';
import { parseWorkspaceTheme, type WorkspaceTheme } from '@/lib/workspace-theme';

let workspaceTheme: WorkspaceTheme = 'dark';
function readWorkspaceTheme(): WorkspaceTheme {
  try { return parseWorkspaceTheme(localStorage.getItem('aritioz-workspace-theme')); }
  catch { return workspaceTheme; }
}
function subscribeWorkspaceTheme(onChange: () => void) {
  window.addEventListener('storage', onChange);
  window.addEventListener('aritioz-theme-change', onChange);
  return () => {
    window.removeEventListener('storage', onChange);
    window.removeEventListener('aritioz-theme-change', onChange);
  };
}

export function projectsViewForClick(clickCount: number): 'conversation' | 'projects' {
  return clickCount >= 2 ? 'conversation' : 'projects';
}

export function AssistantResponse({ answer, error, loading }: { answer: string; error: string; loading: boolean }) {
  return <div className="response-card">
    <p>{loading ? 'Creating your response.' : error || answer}</p>
  </div>;
}

export function LaunchOSWorkspace() {
  const [mode, setMode] = useState<'chat' | 'work'>('chat');
  const [view, setView] = useState<'conversation' | 'projects' | 'themes'>('conversation');
  const [prompt, setPrompt] = useState('');
  const voice = useVoiceInput(setPrompt);
  const [submitted, setSubmitted] = useState('');
  const [answer, setAnswer] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [imageLoading, setImageLoading] = useState(false);
  const [image, setImage] = useState<{ name: string; dataUrl: string } | null>(null);
  const [attachmentError, setAttachmentError] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [accountNotice, setAccountNotice] = useState('');
  const theme = useSyncExternalStore<WorkspaceTheme>(subscribeWorkspaceTheme, readWorkspaceTheme, () => 'dark');
  const darkMode = theme === 'dark';

  function setTheme(nextTheme: WorkspaceTheme) {
    workspaceTheme = nextTheme;
    try {
      localStorage.setItem('aritioz-workspace-theme', nextTheme);
    } catch { /* Theme switching still works without persistent storage. */ }
    window.dispatchEvent(new Event('aritioz-theme-change'));
  }
  function toggleDarkMode() { setTheme(darkMode ? 'light' : 'dark'); }
  const imageInputRef = useRef<HTMLInputElement>(null);
  const accountMenuRef = useRef<HTMLDetailsElement>(null);

  async function submitPrompt(event: React.SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = prompt.trim();
    if (!value || loading) return;
    voice.cancel();
    setSubmitted(value);
    setAnswer('');
    setError('');
    setLoading(true);
    setPrompt('');
    try {
      const reply = await sendChatMessage(value, undefined, undefined, image?.dataUrl, mode);
      setAnswer(reply.response);
      setImage(null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Aritioz could not complete that request.');
    } finally {
      setLoading(false);
    }
  }

  function startNewProject() {
    voice.cancel();
    setSubmitted('');
    setAnswer('');
    setError('');
    setAttachmentError('');
    setImage(null);
    setPrompt('');
    setMode('chat');
    setView('conversation');
  }

  async function selectImage(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    setAttachmentError('');
    setImageLoading(true);
    try {
      const dataUrl = await readImageFile(file);
      setImage({ name: file.name, dataUrl });
    } catch (selectionError) {
      setImage(null);
      setAttachmentError(selectionError instanceof Error ? selectionError.message : 'The image could not be attached.');
    } finally {
      setImageLoading(false);
    }
  }

  return (
    <section className={`aritioz-chat${darkMode ? ' workspace-dark' : ''}${theme === 'cosmic' ? ' workspace-cosmic' : ''}`} aria-label="Aritioz project workspace">
      <aside className={`chat-sidebar${sidebarOpen ? ' mobile-open' : ''}`}>
        <div className="chat-sidebar-brand">
          <span className="workspace-brand-symbol"><Image src="/aritioz-earth-emblem.png" width={18} height={18} alt="" unoptimized /></span>
          <Image className="workspace-brand-logo" src="/aritioz-wordmark.png" width={387} height={90} alt="Aritioz" unoptimized />
        </div>
        <div className="chat-sidebar-tools" aria-label="Workspace tools">
          <button aria-label="Search projects"><Search size={18} /></button>
          <button aria-label="Toggle sidebar" aria-expanded={sidebarOpen} onClick={() => setSidebarOpen((open) => !open)}><Menu size={18} /></button>
        </div>

        <button className="new-project-button" onClick={startNewProject}>
          <span className="sidebar-icon-tile"><SquarePen size={18} /></span><span>New chat</span><ChevronRight className="sidebar-row-arrow" size={16} aria-hidden="true" />
        </button>
        <nav className="chat-navigation" aria-label="Workspace navigation">
          <button className="sidebar-library"><span className="sidebar-icon-tile">{darkMode ? <BookOpen size={18} /> : <Library size={18} />}</span><span>Library</span><ChevronRight className="sidebar-row-arrow" size={16} aria-hidden="true" /></button>
          <button className="sidebar-projects" type="button" aria-current={view === 'projects' ? 'page' : undefined} onClick={(event) => { setView(projectsViewForClick(event.detail)); setSidebarOpen(false); }}><span className="sidebar-icon-tile"><FolderClosed size={18} /></span><span>Projects</span><ChevronRight className="sidebar-row-arrow" size={16} aria-hidden="true" /></button>
          <button className="sidebar-scheduled"><span className="sidebar-icon-tile"><Clock3 size={18} /></span><span>Scheduled</span><ChevronRight className="sidebar-row-arrow" size={16} aria-hidden="true" /></button>
          <button className="sidebar-plugins"><span className="sidebar-icon-tile">{darkMode ? <Puzzle size={18} /> : <Blend size={18} />}</span><span>Plugins</span><ChevronRight className="sidebar-row-arrow" size={16} aria-hidden="true" /></button>
          <button className="sidebar-sites"><span className="sidebar-icon-tile">{darkMode ? <LayoutGrid size={18} /> : <PanelsTopLeft size={18} />}</span><span>Sites</span><span className="chat-nav-new">NEW</span><ChevronRight className="sidebar-row-arrow" size={16} aria-hidden="true" /></button>
          <button className="sidebar-more"><span className="sidebar-icon-tile"><MoreHorizontal size={18} /></span><span>More</span><ChevronRight className="sidebar-row-arrow" size={16} aria-hidden="true" /></button>
        </nav>

        <div className="chat-profile-row">
        <Link className="chat-profile" href="/" title="Go to homepage">
          <span className="chat-profile-logo"><Image src="/blue-water-swirl.svg" width={36} height={36} alt="Blue water swirl logo" unoptimized /></span>
          <div><strong>Anshuman Bharti</strong><small>Creator plan</small></div>
        </Link>
        <details ref={accountMenuRef} className="account-menu" onToggle={() => setAccountNotice('')}>
          <summary aria-label="Account menu" title="Account menu"><Image src="/video-editing-water.webp" width={34} height={34} alt="" unoptimized /></summary>
          <section className="account-panel" aria-label="Account">
            <header className="account-panel-header">
              <span className="account-avatar">AB</span>
              <div><strong>Anshuman Bharti</strong><small>Plus</small></div>
            </header>
            <div className="account-panel-items">
              <button type="button" role="switch" aria-checked={darkMode} aria-label="Dark Mode" onClick={toggleDarkMode}><Moon /><span>Dark Mode</span><span className="theme-switch-track" aria-hidden="true"><span /></span></button>
              <button type="button" className="account-personalization" aria-current={view === 'themes' ? 'page' : undefined} onClick={() => { setView('themes'); setSidebarOpen(false); if (accountMenuRef.current) accountMenuRef.current.open = false; }}><SlidersHorizontal /><span>Themes</span></button>
              <button type="button" onClick={() => setAccountNotice('Profile management is not available yet.')}><UserCircle /><span>Profile</span></button>
              <button type="button" onClick={() => setAccountNotice('Account settings are not available yet.')}><Settings /><span>Settings</span></button>
            </div>
            <div className="account-panel-items account-panel-footer">
              <button type="button" onClick={() => setAccountNotice('Type your question in the chat to get help using Aritioz.')}><LifeBuoy /><span>Help</span><ChevronRight className="account-chevron" /></button>
              <button type="button" onClick={() => setAccountNotice('No account sign-in is connected, so there is no session to log out of.')}><LogOut /><span>Log out</span></button>
            </div>
            {accountNotice && <output className="account-notice">{accountNotice}</output>}
          </section>
        </details>
        </div>
      </aside>

      <div className="chat-main">
        <div className="workspace-space-scene" aria-hidden="true"><span className="workspace-moon" /></div>
        <span className="workspace-build-label" aria-hidden="true">Build with AI <i /></span>
        <div className="chat-mobile-bar">
          <span className="workspace-brand-symbol"><Image src="/aritioz-earth-emblem.png" width={18} height={18} alt="" unoptimized /></span>
          <Image className="workspace-brand-logo" src="/aritioz-wordmark.png" width={387} height={90} alt="Aritioz" unoptimized />
          <button aria-label="Open menu" aria-expanded={sidebarOpen} onClick={() => setSidebarOpen(true)}><Menu size={19} /></button>
        </div>
        {view === 'conversation' && <fieldset className="chat-mode-switch" aria-label="Workspace mode">
          <button type="button" aria-pressed={mode === 'chat'} className={mode === 'chat' ? 'active' : ''} disabled={loading} onClick={() => setMode('chat')}>Chat</button>
          <button type="button" aria-pressed={mode === 'work'} className={mode === 'work' ? 'active' : ''} disabled={loading} onClick={() => setMode('work')}>Work</button>
        </fieldset>}

        {view === 'projects' ? <LocalProjects /> : view === 'themes' ? <ThemesPanel theme={theme} onSelect={setTheme} onBack={() => setView('conversation')} /> : <div className="chat-canvas">
          {submitted ? (
            <div className="chat-response" aria-live="polite">
              <div className="response-prompt">{submitted}</div>
              <AssistantResponse answer={answer} error={error} loading={loading} />
            </div>
          ) : (
            <h2>{mode === 'chat' ? <>What would you like to <span className="chat-heading-accent">create</span>?</> : 'What are you working on today?'}</h2>
          )}

          {(image || imageLoading || attachmentError) && (
            <div className="chat-attachment-status" aria-live="polite">
              {imageLoading && <span>Preparing image…</span>}
              {image && <span>{image.name}<button type="button" aria-label="Remove attached image" onClick={() => setImage(null)}><X size={14} /></button></span>}
              {attachmentError && <span className="attachment-error">{attachmentError}</span>}
            </div>
          )}

          <form className="chat-composer" onSubmit={submitPrompt}>
            <input ref={imageInputRef} type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={selectImage} />
            <button type="button" className="composer-add" aria-label="Add a JPEG, PNG, or WebP image" disabled={loading || imageLoading} onClick={() => imageInputRef.current?.click()}><Plus size={22} /></button>
            <input value={prompt} onChange={(event) => { voice.cancel(); setPrompt(event.target.value); }} placeholder={mode === 'work' ? 'Describe a project task' : 'Ask Aritioz'} aria-label={mode === 'work' ? 'Describe a project task' : 'Ask Aritioz'} disabled={loading} />
            <button type="button" className="composer-mode">{mode === 'work' ? 'Work task' : 'Creative'} <ChevronDown size={15} /></button>
            <button
              type="button"
              className={`composer-mic${voice.active ? ' is-listening' : ''}`}
              aria-label={voice.active ? 'Stop voice input' : 'Use voice input'}
              aria-pressed={voice.active}
              aria-describedby={voice.used ? 'voice-input-status' : undefined}
              title={voice.active ? 'Stop listening' : `Start voice input (${voice.language})`}
              disabled={loading}
              onClick={() => voice.toggle(prompt)}
            ><Mic size={20} /></button>
            <button type="submit" className="composer-send" aria-label="Send prompt" disabled={loading || imageLoading || !prompt.trim()}><ArrowUp size={19} /></button>
          </form>

          {voice.used && (
            <div className="voice-input-feedback">
              <output id="voice-input-status" aria-live="polite" className={voice.error ? 'voice-input-error' : ''}>
                {voice.error || ({
                  idle: 'Microphone off. Edit your text or send when ready.',
                  requesting: 'Allow microphone access in your browser… Click the mic again to cancel.',
                  starting: 'Starting microphone…',
                  listening: 'Listening… Speak now. Click the mic to stop.',
                  stopping: 'Stopping microphone…',
                }[voice.status])}
              </output>
              <label className="voice-language">
                <span>Voice language</span>
                <select value={voice.language} disabled={voice.active} onChange={(event) => voice.setLanguage(event.target.value as VoiceLanguage)}>
                  <option value="hi-IN">हिन्दी (India)</option>
                  <option value="en-IN">English (India)</option>
                  <option value="en-US">English (US)</option>
                </select>
              </label>
            </div>
          )}

          {!submitted && (
            <button className="chat-suggestion" onClick={() => { voice.cancel(); setPrompt(mode === 'work' ? 'Review my project task and propose the concrete code changes and verification steps.' : 'Help me plan the launch for Aria Essentials'); }}>
              <Lightbulb size={24} /> <span>{mode === 'work' ? 'Review a project task and propose the changes' : 'Help me plan the launch for Aria Essentials'}</span><ChevronRight className="suggestion-arrow" size={16} />
            </button>
          )}
        </div>}
        <div className="workspace-signature" aria-hidden="true"><span>Bigger ideas.<br />Brighter possibilities.</span><span>Aritioz · The AI workspace <i /></span></div>
      </div>
    </section>
  );
}
