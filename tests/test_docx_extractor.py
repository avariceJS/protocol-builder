"""
Tests for DocxExtractor.
Run from project root: python -m pytest tests/ -v
"""
import os
import sys
import copy
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.extractors.docx_extractor import DocxExtractor
from src.models.fragment import FragmentStatus

SAMPLE = os.path.join(os.path.dirname(__file__), 'fixtures', 'sample_extract.docx')


@pytest.fixture
def extractor():
    return DocxExtractor()


@pytest.fixture
def fragment(extractor):
    return extractor.extract(SAMPLE)


class TestExtractFragment:
    def test_status_success(self, fragment):
        assert fragment.status == FragmentStatus.SUCCESS, (
            f'Expected SUCCESS, got {fragment.status.value} (confidence={fragment.confidence})'
        )

    def test_starts_with_point_number(self, fragment):
        first_line = fragment.text_preview.splitlines()[0].strip()
        assert first_line.startswith('1.1.'), f'Fragment should start with 1.1., got: {first_line!r}'

    def test_ends_with_edinoglasno(self, fragment):
        last_nonempty = next(
            (l.strip() for l in reversed(fragment.text_preview.splitlines()) if l.strip()),
            ''
        )
        assert 'диногласно' in last_nonempty.lower(), (
            f'Fragment should end with Единогласно, got: {last_nonempty!r}'
        )

    def test_contains_ivanov(self, fragment):
        # Name appears in table cell and in body paragraphs (genitive case)
        assert 'Иванов' in fragment.text_preview

    def test_contains_petrov(self, fragment):
        # Name appears in last table row and body paragraphs
        assert 'Петров' in fragment.text_preview

    def test_contains_table(self, fragment):
        assert '[ТАБЛИЦА]' in fragment.text_preview, 'Fragment should contain a table'

    def test_no_document_header(self, fragment):
        assert 'Выписка из Протокола №' not in fragment.text_preview

    def test_no_director_signature(self, fragment):
        # The signature line is a paragraph that is purely "Директор" + trailing spaces.
        # "Директор" also appears inside the body text ("Директору Ассоциации...") — that's fine.
        # Check that no standalone "Директор" line (signature) leaked into the fragment.
        lines = [l.strip() for l in fragment.text_preview.splitlines()]
        assert 'Директор' not in lines, (
            "Signature-only line 'Директор' should not be in fragment"
        )

    def test_confidence_high(self, fragment):
        assert fragment.confidence >= 85

    def test_has_xml_nodes(self, fragment):
        assert len(fragment.xml_nodes) > 0

    def test_no_warnings(self, fragment):
        assert fragment.warnings == [], f'Unexpected warnings: {fragment.warnings}'


class TestMissingFile:
    def test_error_status(self, extractor):
        frag = extractor.extract('/nonexistent/path/file.docx')
        assert frag.status == FragmentStatus.ERROR
        assert frag.error_message != ''
