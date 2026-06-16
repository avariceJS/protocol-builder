"""Tests for protocol build history persistence."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.models.protocol_history import ProtocolHistoryStore


def test_add_and_list_entries():
    with tempfile.TemporaryDirectory() as tmp:
        history_file = Path(tmp) / 'protocol_history.json'
        with patch('src.models.protocol_history._history_file', return_value=history_file):
            store = ProtocolHistoryStore()
            first = store.add('/tmp/one.docx')
            second = store.add('/tmp/two.docx')

            assert len(store.entries) == 2
            assert store.entries[0].id == second.id
            assert store.entries[1].id == first.id


def test_remove_deletes_file_when_requested():
    with tempfile.TemporaryDirectory() as tmp:
        history_file = Path(tmp) / 'protocol_history.json'
        docx = Path(tmp) / 'protocol.docx'
        docx.write_text('demo', encoding='utf-8')

        with patch('src.models.protocol_history._history_file', return_value=history_file):
            store = ProtocolHistoryStore()
            entry = store.add(str(docx))
            assert docx.exists()

            removed = store.remove(entry.id, delete_file=True)
            assert removed is not None
            assert not docx.exists()
            assert store.entries == []


def test_history_persists_to_disk():
    with tempfile.TemporaryDirectory() as tmp:
        history_file = Path(tmp) / 'protocol_history.json'
        with patch('src.models.protocol_history._history_file', return_value=history_file):
            store = ProtocolHistoryStore()
            store.add('/tmp/persisted.docx')

            reloaded = ProtocolHistoryStore()
            assert len(reloaded.entries) == 1
            assert reloaded.entries[0].path == os.path.abspath('/tmp/persisted.docx')


def test_same_path_updates_timestamp_instead_of_duplicating():
    with tempfile.TemporaryDirectory() as tmp:
        history_file = Path(tmp) / 'protocol_history.json'
        with patch('src.models.protocol_history._history_file', return_value=history_file):
            store = ProtocolHistoryStore()
            first = store.add('/tmp/same.docx')
            first_time = first.created_at
            second = store.add('/tmp/same.docx')

            assert len(store.entries) == 1
            assert second.id == first.id
            assert second.created_at >= first_time
