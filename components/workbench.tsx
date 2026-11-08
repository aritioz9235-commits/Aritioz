'use client';

import { useEffect, useState } from 'react';
import { ArrowLeft, ChevronRight, FileCode2, Folder, Play, RefreshCw, Save } from 'lucide-react';
import {
  getWorkspaceStatus,
  listWorkspaceFiles,
  readWorkspaceFile,
  runWorkspaceCommand,
  saveWorkspaceFile,
  type WorkspaceFile,
} from '@/lib/workspace-api';

type ActiveFileContext = { path: string; content: string } | null;
export type WorkFileDraft = { path: string; content: string } | null;

export function Workbench({
  onActiveFileContext,
  aiDraft,
  onApplyDraft,
}: {
  onActiveFileContext: (context: ActiveFileContext) => void;
  aiDraft: WorkFileDraft;
  onApplyDraft: () => void;
}) {
  const [enabled, setEnabled] = useState(false);
  const [rootName, setRootName] = useState('');
  const [folder, setFolder] = useState('');
  const [files, setFiles] = useState<WorkspaceFile[]>([]);
  const [activePath, setActivePath] = useState('');
  const [content, setContent] = useState('');
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [commandOutput, setCommandOutput] = useState('');
  const [refreshIndex, setRefreshIndex] = useState(0);

  useEffect(() => () => onActiveFileContext(null), [onActiveFileContext]);

  useEffect(() => {
    let current = true;
    async function refresh() {
      setNotice('Connecting to the local project…');
      try {
        const status = await getWorkspaceStatus();
        if (!current) return;
        setEnabled(status.enabled);
        setRootName(status.root_name || '');
        if (!status.enabled) {
          setFiles([]);
          setNotice('Connect a local project to use its files and run checks.');
          return;
        }
        const result = await listWorkspaceFiles(folder);
        if (!current) return;
        if (result.error) throw new Error(result.error);
        setFiles(result.files);
        setNotice('');
      } catch (error) {
        if (current) setNotice(error instanceof Error ? error.message : 'Could not connect to the local project.');
      }
    }
    void refresh();
    return () => { current = false; };
  }, [folder, refreshIndex]);

  async function openFile(path: string) {
    setBusy(true);
    setNotice('Opening file…');
    try {
      const file = await readWorkspaceFile(path);
      setActivePath(file.path);
      setContent(file.content);
      onActiveFileContext({ path: file.path, content: file.content });
      setNotice('');
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Could not open this file.');
    } finally {
      setBusy(false);
    }
  }

  async function saveFile() {
    if (!activePath || busy) return;
    setBusy(true);
    setNotice('Saving file…');
    try {
      await saveWorkspaceFile(activePath, content);
      onActiveFileContext({ path: activePath, content });
      setNotice('Saved. The project file now contains these edits.');
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Could not save this file.');
    } finally {
      setBusy(false);
    }
  }

  async function runCommand(command: 'test' | 'lint' | 'typecheck' | 'build') {
    setBusy(true);
    setCommandOutput(`Running ${command}…`);
    try {
      const result = await runWorkspaceCommand(command);
      setCommandOutput(`${result.command} · ${result.return_code === 0 ? 'passed' : `exit ${result.return_code}`}\n\n${result.output}`);
    } catch (error) {
      setCommandOutput(error instanceof Error ? error.message : 'Could not run the project check.');
    } finally {
      setBusy(false);
    }
  }

  const parentFolder = folder.includes('/') ? folder.slice(0, folder.lastIndexOf('/')) : '';

  return (
    <section className="workbench" aria-label="Project workbench">
      <div className="workbench-topline">
        <div><span className="workbench-kicker">PROJECT WORKSPACE</span><strong>{rootName || 'Local project'}</strong></div>
        <span className={`workbench-connection${enabled ? ' connected' : ''}`}><i />{enabled ? 'Connected' : 'Not connected'}</span>
      </div>

      {!enabled ? (
        <div className="workbench-empty">
          <Folder size={24} />
          <strong>Connect a local project</strong>
          <p>Set <code>APP_ENV=development</code> and <code>WORKSPACE_ROOT</code> in the backend environment, then restart it. Work mode will be limited to that project directory.</p>
          {notice && <output aria-live="polite">{notice}</output>}
        </div>
      ) : (
        <div className="workbench-grid">
          <section className="workbench-files" aria-label="Project files">
            <div className="workbench-section-title">
              {folder && <button type="button" aria-label="Parent folder" onClick={() => setFolder(parentFolder)}><ArrowLeft size={15} /></button>}
              <span>{folder || 'Project files'}</span>
              <button type="button" aria-label="Refresh files" onClick={() => setRefreshIndex((value) => value + 1)}><RefreshCw size={14} /></button>
            </div>
            <div className="workbench-file-list">
              {files.map((file) => (
                <button type="button" key={file.path} className={activePath === file.path ? 'selected' : ''} disabled={busy} onClick={() => file.kind === 'directory' ? setFolder(file.path) : void openFile(file.path)}>
                  {file.kind === 'directory' ? <Folder size={15} /> : <FileCode2 size={15} />}
                  <span>{file.path.slice(file.path.lastIndexOf('/') + 1)}</span>
                  {file.kind === 'directory' && <ChevronRight size={13} />}
                </button>
              ))}
              {!files.length && <small>No visible project files in this folder.</small>}
            </div>
            {notice && <output className="workbench-notice" aria-live="polite">{notice}</output>}
          </section>

          <section className="workbench-editor" aria-label="File editor">
            <div className="workbench-section-title"><span>{activePath || 'Choose a project file'}</span>
              <div className="workbench-editor-actions">
                {aiDraft?.path === activePath && <button type="button" title="Load this AI draft into the editor; it will not be saved until you press Save file." onClick={() => { setContent(aiDraft.content); onActiveFileContext(aiDraft); onApplyDraft(); }}>Apply AI draft</button>}
                <button type="button" className="workbench-save" disabled={!activePath || busy} onClick={() => void saveFile()}><Save size={14} /> Save file</button>
              </div>
            </div>
            {activePath ? (
              <textarea aria-label={`Edit ${activePath}`} spellCheck={false} value={content} disabled={busy} onChange={(event) => { setContent(event.target.value); onActiveFileContext({ path: activePath, content: event.target.value }); }} />
            ) : (
              <div className="workbench-editor-empty"><FileCode2 size={22} /><span>Select a text file to inspect or edit it.</span></div>
            )}
          </section>

          <section className="workbench-checks" aria-label="Project checks">
            <div className="workbench-section-title"><span>Run project checks</span></div>
            <div className="workbench-command-list">
              {(['test', 'lint', 'typecheck', 'build'] as const).map((command) => (
                <button type="button" key={command} disabled={busy} onClick={() => void runCommand(command)}><Play size={13} />{command === 'typecheck' ? 'TypeScript' : command}</button>
              ))}
            </div>
            {commandOutput && <pre aria-live="polite">{commandOutput}</pre>}
            <small>Only the listed commands can run, from the connected project root.</small>
          </section>
        </div>
      )}
    </section>
  );
}
