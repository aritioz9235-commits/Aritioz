'use client';

import { useRef, useState } from 'react';
import { FileCode2, FolderClosed, FolderOpen } from 'lucide-react';

type ProjectFile = { path: string; file: File };

export function LocalProjects() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [projectName, setProjectName] = useState('');
  const [files, setFiles] = useState<ProjectFile[]>([]);
  const [activePath, setActivePath] = useState('');
  const [content, setContent] = useState('');
  const [notice, setNotice] = useState('');

  function openProject(event: React.ChangeEvent<HTMLInputElement>) {
    const selected = Array.from(event.target.files ?? []);
    event.target.value = '';
    if (!selected.length) return;
    const projectFiles = selected
      .map((file) => ({ path: file.webkitRelativePath || file.name, file }))
      .filter(({ path, file }) => !path.split('/').some((part) => part.startsWith('.') || part === 'node_modules' || part === 'dist' || part === 'build') && file.size <= 512 * 1024)
      .sort((a, b) => a.path.localeCompare(b.path));
    setProjectName(selected[0].webkitRelativePath.split('/')[0] || 'Local project');
    setFiles(projectFiles);
    setActivePath('');
    setContent('');
    setNotice(projectFiles.length ? '' : 'No previewable files found in this folder.');
  }

  async function openFile(entry: ProjectFile) {
    setNotice('Opening file…');
    try {
      const text = await entry.file.text();
      if (text.includes('\0')) throw new Error('This file is not plain text.');
      setActivePath(entry.path);
      setContent(text);
      setNotice('');
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Could not open this file.');
    }
  }

  return (
    <section className="local-projects" aria-label="Local projects">
      <div className="local-projects-heading">
        <div><span className="workbench-kicker">PROJECTS</span><h2>Local projects</h2><p>Open a folder from your computer to browse its files.</p></div>
        <button type="button" onClick={() => inputRef.current?.click()}><FolderOpen size={18} /> Open local project</button>
        <input ref={inputRef} type="file" hidden multiple {...{ webkitdirectory: '' }} onChange={openProject} aria-label="Choose a local project folder" />
      </div>
      {projectName ? (
        <div className="local-projects-card">
          <header><FolderClosed size={20} /><strong>{projectName}</strong><span>{files.length} files</span></header>
          <div className="local-projects-grid">
            <div className="local-projects-files" aria-label="Local project files">
              {files.map((entry) => <button key={entry.path} type="button" className={activePath === entry.path ? 'selected' : ''} onClick={() => void openFile(entry)}><FileCode2 size={15} /><span>{entry.path.split('/').slice(1).join('/') || entry.path}</span></button>)}
            </div>
            <div className="local-projects-preview" aria-label="File preview">
              <div className="workbench-section-title">{activePath || 'Choose a file to preview'}</div>
              {activePath ? <pre>{content}</pre> : <p>Select a file from this local project.</p>}
            </div>
          </div>
          {notice && <output aria-live="polite">{notice}</output>}
        </div>
      ) : (
        <div className="local-projects-empty"><FolderOpen size={36} /><strong>No local project open</strong><p>Choose a project folder to see its files here.</p><button type="button" onClick={() => inputRef.current?.click()}>Open local project</button></div>
      )}
    </section>
  );
}
