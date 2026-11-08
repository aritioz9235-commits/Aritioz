from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

from app.config import Settings

router = APIRouter(prefix="/api/workspace", tags=["workspace"])
IGNORED_DIRS = {".git", "node_modules", ".venv", "venv", ".next", "dist", "build", "__pycache__"}
MAX_FILE_BYTES = 512 * 1024
COMMANDS: dict[str, tuple[str, ...]] = {
    "test": ("npm", "test"),
    "lint": ("npm", "run", "lint"),
    "typecheck": ("npm", "exec", "--no", "--", "tsc", "--noEmit"),
    "build": ("npm", "run", "build"),
}
SENSITIVE_ENV_MARKERS = ("KEY", "TOKEN", "PASSWORD", "SECRET", "CREDENTIAL", "AUTHORIZATION")


class SaveFileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str = Field(min_length=1, max_length=500)
    content: str = Field(max_length=MAX_FILE_BYTES)


class RunCommandRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    command: str = Field(min_length=1, max_length=30)


def root_for(config: Settings) -> Path | None:
    if config.app_env.lower() == "production" or not config.workspace_root.strip():
        return None
    root = Path(config.workspace_root).expanduser().resolve()
    return root if root.is_dir() else None


def safe_path(root: Path, relative: str) -> Path | None:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    if any(part in IGNORED_DIRS or part.startswith(".") for part in candidate.relative_to(root).parts):
        return None
    return candidate


def allowed_origin(request: Request, config: Settings) -> bool:
    origin = request.headers.get("origin", "")
    return bool(origin and origin in config.cors_origins)


@router.get("/status")
async def workspace_status(request: Request):
    config = request.app.state.settings
    root = root_for(config)
    return {"enabled": root is not None, "root_name": root.name if root else None}


@router.get("/files")
async def workspace_files(request: Request, path: str = ""):
    config = request.app.state.settings
    root = root_for(config)
    if root is None:
        return {"enabled": False, "files": []}
    if not allowed_origin(request, config):
        return {"error": "Workspace requests must come from an allowed app origin."}
    folder = safe_path(root, path)
    if folder is None or not folder.is_dir():
        return {"error": "Folder was not found in the connected workspace."}
    files = []
    for item in sorted(folder.iterdir(), key=lambda value: (not value.is_dir(), value.name.lower())):
        if item.name in IGNORED_DIRS or item.name.startswith(".env") or item.name.startswith("."):
            continue
        rel = item.relative_to(root).as_posix()
        if item.is_dir():
            files.append({"path": rel, "kind": "directory"})
        elif item.is_file() and item.stat().st_size <= MAX_FILE_BYTES:
            files.append({"path": rel, "kind": "file"})
        if len(files) >= 300:
            break
    return {"enabled": True, "files": files}


@router.get("/file")
async def read_workspace_file(request: Request, path: str):
    config = request.app.state.settings
    root = root_for(config)
    if root is None:
        return {"error": "Local workspace is not enabled."}
    if not allowed_origin(request, config):
        return {"error": "Workspace requests must come from an allowed app origin."}
    file_path = safe_path(root, path)
    if file_path is None or not file_path.is_file() or file_path.stat().st_size > MAX_FILE_BYTES:
        return {"error": "File was not found or is too large to open."}
    try:
        return {"path": file_path.relative_to(root).as_posix(), "content": file_path.read_text(encoding="utf-8")}
    except UnicodeDecodeError:
        return {"error": "This file is not UTF-8 text and cannot be edited here."}


@router.put("/file")
async def save_workspace_file(request: Request, payload: SaveFileRequest):
    config = request.app.state.settings
    root = root_for(config)
    if root is None:
        return {"error": "Local workspace is not enabled."}
    if not allowed_origin(request, config):
        return {"error": "Workspace requests must come from an allowed app origin."}
    file_path = safe_path(root, payload.path)
    if file_path is None or not file_path.is_file() or file_path.stat().st_size > MAX_FILE_BYTES:
        return {"error": "Only existing project files up to 512 KB can be edited."}
    file_path.write_text(payload.content, encoding="utf-8")
    return {"saved": True, "path": file_path.relative_to(root).as_posix()}


@router.post("/command")
async def run_workspace_command(request: Request, payload: RunCommandRequest):
    config = request.app.state.settings
    root = root_for(config)
    if root is None:
        return {"error": "Local workspace is not enabled."}
    if not allowed_origin(request, config):
        return {"error": "Workspace requests must come from an allowed app origin."}
    argv = COMMANDS.get(payload.command)
    if argv is None:
        return {"error": "That command is not in the workspace allowlist."}

    def run() -> dict[str, object]:
        try:
            command_env = {
                key: value
                for key, value in os.environ.items()
                if not any(marker in key.upper() for marker in SENSITIVE_ENV_MARKERS)
            }
            result = subprocess.run(argv, cwd=root, capture_output=True, text=True, timeout=180, check=False, env=command_env)
            return {
                "command": " ".join(argv),
                "return_code": result.returncode,
                "output": (result.stdout + result.stderr)[-12000:],
            }
        except subprocess.TimeoutExpired as exc:
            output = ""
            for part in (exc.stdout, exc.stderr):
                if isinstance(part, bytes):
                    output += part.decode("utf-8", errors="replace")
                elif part:
                    output += part
            return {"command": " ".join(argv), "return_code": -1, "output": f"Command timed out after 180 seconds.\n{output[-12000:]}"}
        except OSError:
            return {"error": "Command could not be started. Check that its tool is installed."}

    return await asyncio.to_thread(run)
