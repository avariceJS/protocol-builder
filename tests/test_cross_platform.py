"""Tests for cross-platform behaviour and build logic."""
import sys
import os
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.extractors.docx_extractor import DocxExtractor
from src.builders.protocol_builder import build_protocol
from src.models.fragment import Fragment, FragmentStatus
from src.models.protocol_header import ProtocolHeader

SAMPLE = os.path.join(os.path.dirname(__file__), 'fixtures', 'sample_extract.docx')


class TestPlatformUtils:
    def test_open_path_exists(self):
        from src.utils.platform_utils import open_path, reveal_path
        assert callable(open_path)
        assert callable(reveal_path)

    def test_open_path_nonexistent_noop(self):
        from src.utils.platform_utils import open_path
        # Should not raise even for a nonexistent path
        open_path('/nonexistent/path/that/does/not/exist.docx')

    def test_reveal_path_empty_noop(self):
        from src.utils.platform_utils import reveal_path
        reveal_path('')


class TestErrorStatusExcluded:
    """Files with ERROR status must not appear in the main protocol body."""

    def test_error_not_in_body(self, tmp_path):
        good = DocxExtractor().extract(SAMPLE)

        error_frag = Fragment(
            file_path='/fake/broken.docx',
            original_number='',
            assigned_number='',
            status=FragmentStatus.ERROR,
            confidence=0,
            error_message='Файл повреждён',
        )

        output = str(tmp_path / 'protocol.docx')
        build_protocol([good, error_frag], ProtocolHeader(), output)

        import zipfile
        from lxml import etree
        from src.utils.anchors import W_NS, get_para_text

        with zipfile.ZipFile(output) as z:
            xml = z.read('word/document.xml')
        root = etree.fromstring(xml)
        _W = f'{{{W_NS}}}'
        body = root.find(f'.//{_W}body')
        all_text = ' '.join(get_para_text(e) for e in body.iter(f'{_W}p'))

        # Error file should be in problematic section, not as 1.2.
        assert '1.1.' in all_text
        assert '1.2.' not in all_text or 'broken.docx' not in all_text
        assert 'broken.docx' in all_text, "Error file should be listed in problematic section"
        assert 'требующие ручной проверки' in all_text

    def test_needs_review_is_included(self, tmp_path):
        """NEEDS_REVIEW fragments ARE included in the main body."""
        good = DocxExtractor().extract(SAMPLE)
        review_frag = Fragment(
            file_path='/fake/partial.docx',
            original_number='1.7.',
            assigned_number='',
            status=FragmentStatus.NEEDS_REVIEW,
            confidence=60,
            text_preview='1.7. Тестовый фрагмент',
            source_type='pdf',
        )

        output = str(tmp_path / 'protocol_review.docx')
        build_protocol([good, review_frag], ProtocolHeader(), output)

        import zipfile
        from lxml import etree
        from src.utils.anchors import W_NS, get_para_text

        with zipfile.ZipFile(output) as z:
            xml = z.read('word/document.xml')
        root = etree.fromstring(xml)
        _W = f'{{{W_NS}}}'
        body = root.find(f'.//{_W}body')
        all_text = ' '.join(get_para_text(e) for e in body.iter(f'{_W}p'))

        assert '1.1.' in all_text
        assert '1.7.' in all_text


class TestManualExclude:
    """include_in_protocol=False removes the fragment from output."""

    def test_manually_excluded_fragment(self, tmp_path):
        frag = DocxExtractor().extract(SAMPLE)
        frag.include_in_protocol = False

        output = str(tmp_path / 'protocol_empty.docx')
        build_protocol([frag], ProtocolHeader(), output)

        import zipfile
        from lxml import etree
        from src.utils.anchors import W_NS, get_para_text

        with zipfile.ZipFile(output) as z:
            xml = z.read('word/document.xml')
        root = etree.fromstring(xml)
        _W = f'{{{W_NS}}}'
        body = root.find(f'.//{_W}body')
        all_text = ' '.join(get_para_text(e) for e in body.iter(f'{_W}p'))

        assert '1.1.' not in all_text
        assert 'требующие ручной проверки' not in all_text
        assert 'sample_extract' not in all_text

    def test_excluded_middle_preserves_original_numbers(self, tmp_path):
        """Excluded fragments are omitted; remaining ones keep source numbering."""
        f1 = DocxExtractor().extract(SAMPLE)
        f2 = DocxExtractor().extract(SAMPLE)
        f3 = DocxExtractor().extract(SAMPLE)
        f2.file_path = '/tmp/02_excluded.docx'
        f3.file_path = '/tmp/03_excluded.docx'
        f2.include_in_protocol = False
        f3.include_in_protocol = False

        output = str(tmp_path / 'protocol_excluded.docx')
        build_protocol([f1, f2, f3], ProtocolHeader(), output)

        import zipfile
        from lxml import etree
        from src.utils.anchors import W_NS, get_para_text

        with zipfile.ZipFile(output) as z:
            xml = z.read('word/document.xml')
        root = etree.fromstring(xml)
        _W = f'{{{W_NS}}}'
        body = root.find(f'.//{_W}body')
        all_text = ' '.join(get_para_text(e) for e in body.iter(f'{_W}p'))

        assert '1.1.' in all_text
        assert '02_excluded' not in all_text
        assert '03_excluded' not in all_text
