'use client';

import { useRef, useState } from 'react';
import {
  ArrowUp,
  BookOpen,
  BriefcaseBusiness,
  ChevronDown,
  CircleHelp,
  FolderKanban,
  Lightbulb,
  Menu,
  MessageCircle,
  Mic,
  MoreHorizontal,
  PenLine,
  Plus,
  Search,
  Sparkles,
  X,
} from 'lucide-react';
import { sendChatMessage } from '@/lib/chat-api';
import { readImageFile } from '@/lib/image-file';

const savedProjects = [
  'Aria Essentials launch',
  'Brand identity direction',
  'Product listing refresh',
  'Diwali campaign ideas',
  'Store homepage copy',
];

const recentProjects = ['New skincare collection', 'Customer reply templates'];

export function LaunchOSWorkspace() {
  const [mode, setMode] = useState<'chat' | 'work'>('chat');
  const [prompt, setPrompt] = useState('');
  const [submitted, setSubmitted] = useState('');
  const [answer, setAnswer] = useState('');
  const [answerMeta, setAnswerMeta] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [imageLoading, setImageLoading] = useState(false);
  const [image, setImage] = useState<{ name: string; dataUrl: string } | null>(null);
  const [attachmentError, setAttachmentError] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const imageInputRef = useRef<HTMLInputElement>(null);

  async function submitPrompt(event: React.SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = prompt.trim();
    if (!value || loading) return;
    setSubmitted(value);
    setAnswer('');
    setAnswerMeta('');
    setError('');
    setLoading(true);
    setPrompt('');
    try {
      const reply = await sendChatMessage(value, undefined, undefined, image?.dataUrl);
      setAnswer(reply.response);
      setAnswerMeta(`${reply.provider} · ${reply.model}`);
      setImage(null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Aritioz could not complete that request.');
    } finally {
      setLoading(false);
    }
  }

  function startNewProject() {
    setSubmitted('');
    setAnswer('');
    setAnswerMeta('');
    setError('');
    setAttachmentError('');
    setImage(null);
    setPrompt('');
    setMode('chat');
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
    <section className="aritioz-chat" aria-label="Aritioz project workspace">
      <aside className={`chat-sidebar${sidebarOpen ? ' mobile-open' : ''}`}>
        <div className="chat-sidebar-brand">
          <Sparkles size={18} strokeWidth={1.9} />
          <span>Aritioz</span>
        </div>
        <div className="chat-sidebar-tools" aria-label="Workspace tools">
          <button aria-label="Search projects"><Search size={18} /></button>
          <button aria-label="Toggle sidebar" aria-expanded={sidebarOpen} onClick={() => setSidebarOpen((open) => !open)}><Menu size={18} /></button>
        </div>

        <button className="new-project-button" onClick={startNewProject}>
          <PenLine size={18} /> New project
        </button>
        <nav className="chat-navigation" aria-label="Project navigation">
          <button><BookOpen size={18} /> Library</button>
          <button><FolderKanban size={18} /> Projects</button>
          <button><BriefcaseBusiness size={18} /> Workspace</button>
          <button><CircleHelp size={18} /> Help</button>
          <button><MoreHorizontal size={18} /> More</button>
        </nav>

        <div className="chat-history">
          <p>Pinned</p>
          {savedProjects.map((project) => (
            <button key={project} onClick={() => setSubmitted(project)}>
              <MessageCircle size={17} /> {project}
            </button>
          ))}
        </div>
        <div className="chat-history chat-recents">
          <p>Recents</p>
          {recentProjects.map((project) => <button key={project} onClick={() => setSubmitted(project)}>{project}</button>)}
        </div>
        <button className="chat-profile" aria-label="Open Anshuman Bharti profile">
          <span>AB</span><div><strong>Anshuman Bharti</strong><small>Creator plan</small></div>
        </button>
      </aside>

      <div className="chat-main">
        <div className="chat-mobile-bar">
          <Sparkles size={17} /><strong>Aritioz</strong>
          <button aria-label="Open menu" aria-expanded={sidebarOpen} onClick={() => setSidebarOpen(true)}><Menu size={19} /></button>
        </div>
        <div className="chat-mode-switch" role="tablist" aria-label="Workspace mode">
          <button role="tab" aria-selected={mode === 'chat'} className={mode === 'chat' ? 'active' : ''} onClick={() => setMode('chat')}>Chat</button>
          <button role="tab" aria-selected={mode === 'work'} className={mode === 'work' ? 'active' : ''} onClick={() => setMode('work')}>Work</button>
        </div>

        <div className="chat-canvas">
          {submitted ? (
            <div className="chat-response" aria-live="polite">
              <div className="response-prompt">{submitted}</div>
              <div className="response-card"><Sparkles size={20} /><div>
                <strong>{loading ? 'Thinking…' : error ? 'Something went wrong' : 'Aritioz'}</strong>
                <p>{loading ? 'Creating your response.' : error || answer}</p>
                {answerMeta && <small>{answerMeta}</small>}
              </div></div>
            </div>
          ) : (
            <h2>{mode === 'chat' ? 'What would you like to create?' : 'What are you working on today?'}</h2>
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
            <input value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="Ask Aritioz" aria-label="Ask Aritioz" disabled={loading} />
            <button type="button" className="composer-mode">Creative <ChevronDown size={15} /></button>
            <button type="button" className="composer-mic" aria-label="Use voice input"><Mic size={20} /></button>
            <button type="submit" className="composer-send" aria-label="Send prompt" disabled={loading || imageLoading || !prompt.trim()}><ArrowUp size={19} /></button>
          </form>

          {!submitted && (
            <button className="chat-suggestion" onClick={() => setPrompt('Help me plan the launch for Aria Essentials')}>
              <Lightbulb size={24} /> <span>Help me plan the launch for Aria Essentials</span>
            </button>
          )}
        </div>
      </div>
    </section>
  );
}
