"""Tests for workspace session persistence."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.models.fragment import Fragment, FragmentStatus
from src.models.protocol_header import ProtocolHeader
from src.models.workspace_state import WorkspaceStateStore, fragment_from_saved, fragment_to_saved


def test_save_and_load_workspace():
    with tempfile.TemporaryDirectory() as tmp:
        state_file = Path(tmp) / 'workspace_state.json'
        with patch('src.models.workspace_state._state_file', return_value=state_file):
            store = WorkspaceStateStore()
            frag = Fragment(
                file_path='/tmp/one.docx',
                original_number='1.1.',
                assigned_number='1.1.',
                status=FragmentStatus.SUCCESS,
                confidence=95,
                text_preview='preview',
                include_in_protocol=False,
            )
            header = ProtocolHeader(protocol_number='12', protocol_date='15.06.2026')
            store.save(['/tmp/one.docx'], [frag], header)

            reloaded = WorkspaceStateStore()
            assert reloaded.state.file_paths == [os.path.abspath('/tmp/one.docx')]
            assert reloaded.state.header['protocol_number'] == '12'
            meta = reloaded.fragment_meta_by_path()
            assert meta[os.path.abspath('/tmp/one.docx')].include_in_protocol is False
            assert meta[os.path.abspath('/tmp/one.docx')].confidence == 95


def test_fragment_roundtrip():
    frag = Fragment(
        file_path='/tmp/two.pdf',
        original_number='2.1.',
        assigned_number='2.1.',
        status=FragmentStatus.NEEDS_REVIEW,
        confidence=70,
        warnings=['check anchor'],
        include_in_protocol=True,
        source_type='pdf',
    )
    restored = fragment_from_saved(fragment_to_saved(frag))
    assert restored.file_path == os.path.abspath('/tmp/two.pdf')
    assert restored.status == FragmentStatus.NEEDS_REVIEW
    assert restored.warnings == ['check anchor']
    assert restored.source_type == 'pdf'


def test_clear_removes_state_file():
    with tempfile.TemporaryDirectory() as tmp:
        state_file = Path(tmp) / 'workspace_state.json'
        with patch('src.models.workspace_state._state_file', return_value=state_file):
            store = WorkspaceStateStore()
            store.save([], [], ProtocolHeader())
            assert state_file.is_file()

            store.clear()
            assert not state_file.is_file()
