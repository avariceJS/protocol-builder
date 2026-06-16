"""Persistent workspace state: loaded files, fragments metadata, header form."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QStandardPaths

from .fragment import Fragment, FragmentStatus
from .protocol_header import ProtocolHeader


@dataclass
class WorkspaceState:
    file_paths: List[str] = field(default_factory=list)
    fragments: List[dict] = field(default_factory=list)
    header: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> 'WorkspaceState':
        return cls(
            file_paths=[str(p) for p in data.get('file_paths', [])],
            fragments=list(data.get('fragments', [])),
            header=dict(data.get('header', {})),
        )


def _state_file() -> Path:
    config_dir = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
    Path(config_dir).mkdir(parents=True, exist_ok=True)
    return Path(config_dir) / 'workspace_state.json'


def fragment_to_saved(frag: Fragment) -> dict:
    return {
        'file_path': os.path.abspath(frag.file_path),
        'original_number': frag.original_number,
        'assigned_number': frag.assigned_number,
        'status': frag.status.name,
        'confidence': frag.confidence,
        'text_preview': frag.text_preview,
        'warnings': list(frag.warnings),
        'error_message': frag.error_message,
        'include_in_protocol': frag.include_in_protocol,
        'source_type': frag.source_type,
    }


def fragment_from_saved(data: dict) -> Fragment:
    status_name = str(data.get('status', FragmentStatus.ERROR.name))
    try:
        status = FragmentStatus[status_name]
    except KeyError:
        status = FragmentStatus.ERROR

    return Fragment(
        file_path=str(data['file_path']),
        original_number=str(data.get('original_number', '')),
        assigned_number=str(data.get('assigned_number', '')),
        status=status,
        confidence=int(data.get('confidence', 0)),
        text_preview=str(data.get('text_preview', '')),
        warnings=list(data.get('warnings', [])),
        error_message=str(data.get('error_message', '')),
        include_in_protocol=bool(data.get('include_in_protocol', True)),
        source_type=str(data.get('source_type', 'docx')),
    )


class WorkspaceStateStore:
    def __init__(self) -> None:
        self._state = WorkspaceState()

    @property
    def state(self) -> WorkspaceState:
        return self._state

    def load(self) -> WorkspaceState:
        path = _state_file()
        if not path.is_file():
            self._state = WorkspaceState()
            return self._state
        try:
            raw = json.loads(path.read_text(encoding='utf-8'))
            self._state = WorkspaceState.from_dict(raw if isinstance(raw, dict) else {})
        except (json.JSONDecodeError, OSError, TypeError):
            self._state = WorkspaceState()
        return self._state

    def save(
        self,
        file_paths: List[str],
        fragments: List[Fragment],
        header: ProtocolHeader,
    ) -> None:
        normalized_paths = [os.path.abspath(p) for p in file_paths]
        frag_map = {os.path.abspath(f.file_path): f for f in fragments}
        saved_fragments = [
            fragment_to_saved(frag_map[p])
            for p in normalized_paths
            if p in frag_map
        ]
        self._state = WorkspaceState(
            file_paths=normalized_paths,
            fragments=saved_fragments,
            header=asdict(header),
        )
        path = _state_file()
        path.write_text(
            json.dumps(asdict(self._state), ensure_ascii=False, indent=2),
            encoding='utf-8',
        )

    def clear(self) -> None:
        self._state = WorkspaceState()
        path = _state_file()
        if path.is_file():
            path.unlink()

    def fragment_meta_by_path(self) -> dict[str, Fragment]:
        return {
            str(item['file_path']): fragment_from_saved(item)
            for item in self._state.fragments
            if 'file_path' in item
        }
