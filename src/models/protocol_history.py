"""Persistent history of generated protocol files."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QStandardPaths


@dataclass
class ProtocolHistoryEntry:
    id: str
    path: str
    created_at: str  # ISO 8601 UTC
    file_name: str

    @property
    def exists(self) -> bool:
        return os.path.isfile(self.path)

    @classmethod
    def from_path(cls, path: str) -> 'ProtocolHistoryEntry':
        normalized = os.path.abspath(path)
        return cls(
            id=str(uuid.uuid4()),
            path=normalized,
            created_at=datetime.now(timezone.utc).isoformat(),
            file_name=os.path.basename(normalized),
        )

    @classmethod
    def from_dict(cls, data: dict) -> 'ProtocolHistoryEntry':
        return cls(
            id=str(data['id']),
            path=str(data['path']),
            created_at=str(data['created_at']),
            file_name=str(data.get('file_name') or os.path.basename(str(data['path']))),
        )


def _history_file() -> Path:
    config_dir = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
    Path(config_dir).mkdir(parents=True, exist_ok=True)
    return Path(config_dir) / 'protocol_history.json'


class ProtocolHistoryStore:
    def __init__(self) -> None:
        self._entries: List[ProtocolHistoryEntry] = []
        self.load()

    @property
    def entries(self) -> List[ProtocolHistoryEntry]:
        return list(self._entries)

    def load(self) -> None:
        path = _history_file()
        if not path.is_file():
            self._entries = []
            return
        try:
            raw = json.loads(path.read_text(encoding='utf-8'))
            items = raw if isinstance(raw, list) else raw.get('entries', [])
            self._entries = [ProtocolHistoryEntry.from_dict(item) for item in items]
        except (json.JSONDecodeError, OSError, KeyError, TypeError):
            self._entries = []

        seen: set[str] = set()
        unique: List[ProtocolHistoryEntry] = []
        for entry in self._entries:
            key = entry.path.casefold() if os.name == 'nt' else entry.path
            if key in seen:
                continue
            seen.add(key)
            unique.append(entry)
        self._entries = unique
        self._sort()
        self.save()

    def save(self) -> None:
        path = _history_file()
        payload = [asdict(entry) for entry in self._entries]
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )

    def add(self, file_path: str) -> ProtocolHistoryEntry:
        normalized = os.path.abspath(file_path)
        for entry in self._entries:
            if entry.path == normalized:
                entry.created_at = datetime.now(timezone.utc).isoformat()
                self._sort()
                self.save()
                return entry

        entry = ProtocolHistoryEntry.from_path(normalized)
        self._entries.insert(0, entry)
        self.save()
        return entry

    def remove(self, entry_id: str, *, delete_file: bool = False) -> Optional[ProtocolHistoryEntry]:
        entry = self.get(entry_id)
        if entry is None:
            return None

        if delete_file and entry.exists:
            os.remove(entry.path)

        self._entries = [e for e in self._entries if e.id != entry_id]
        self.save()
        return entry

    def get(self, entry_id: str) -> Optional[ProtocolHistoryEntry]:
        for entry in self._entries:
            if entry.id == entry_id:
                return entry
        return None

    def _sort(self) -> None:
        self._entries.sort(key=lambda e: e.created_at, reverse=True)
