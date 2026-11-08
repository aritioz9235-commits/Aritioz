from __future__ import annotations

import uuid

from app.rag import chunk_text
from app.storage import safe_storage_path


def test_chunk_text_has_overlap_and_no_empty_chunks() -> None:
    chunks = chunk_text("a" * 2500, size=1000, overlap=100)
    assert len(chunks) == 3
    assert chunks[0][-100:] == chunks[1][:100]


def test_storage_paths_are_workspace_scoped_and_safe() -> None:
    workspace_id = uuid.uuid4()
    path = safe_storage_path(workspace_id, "../../secrets?.pdf")
    assert path.startswith(f"{workspace_id}/")
    assert ".." not in path
    assert "/secrets" in path
