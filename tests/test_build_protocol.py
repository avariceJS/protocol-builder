"""
Integration tests: build a full protocol DOCX from sample copies.
"""
import sys, os, shutil, tempfile, copy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.extractors.docx_extractor import DocxExtractor
from src.builders.protocol_builder import build_protocol
from src.models.protocol_header import ProtocolHeader
from src.models.fragment import FragmentStatus

SAMPLE = os.path.join(os.path.dirname(__file__), 'fixtures', 'sample_extract.docx')


def make_fragments(n: int, tmpdir: str) -> list:
    extractor = DocxExtractor()
    fragments = []
    for i in range(n):
        dest = os.path.join(tmpdir, f'sample_{i+1}.docx')
        shutil.copy(SAMPLE, dest)
        frag = extractor.extract(dest)
        fragments.append(frag)
    return fragments


class TestBuildProtocol50:
    def test_50_files_docx(self, tmp_path):
        fragments = make_fragments(50, str(tmp_path))
        assert all(f.status == FragmentStatus.SUCCESS for f in fragments)

        header = ProtocolHeader(
            protocol_number='2001',
            protocol_date='05.05.2026',
            session_name='Тестовое заседание',
            organization='Тестовая организация',
        )
        output = str(tmp_path / 'protocol_50.docx')
        build_protocol(fragments, header, output)
        assert os.path.exists(output)
        assert os.path.getsize(output) > 10_000

        # Verify content
        import zipfile
        from lxml import etree
        from src.utils.anchors import W_NS, get_para_text
        with zipfile.ZipFile(output, 'r') as z:
            xml = z.read('word/document.xml')
        root = etree.fromstring(xml)
        _W = f'{{{W_NS}}}'
        body = root.find(f'.//{_W}body')
        all_text = ' '.join(
            get_para_text(e)
            for e in body.iter(f'{_W}p')
        )
        # Check that points 1.1 through 1.50 are present
        for i in range(1, 51):
            assert f'1.{i}.' in all_text, f'Point 1.{i}. not found in output'


class TestProblematicSection:
    def test_not_found_file_in_section(self, tmp_path):
        """File without fragment -> appears in problematic section."""
        from src.models.fragment import Fragment
        good = DocxExtractor().extract(SAMPLE)
        good.file_path = SAMPLE

        bad = Fragment(
            file_path='/fake/no_fragment.docx',
            original_number='',
            assigned_number='',
            status=FragmentStatus.NOT_FOUND,
            confidence=0,
            warnings=['Начальный якорь не найден'],
        )

        output = str(tmp_path / 'protocol_with_bad.docx')
        build_protocol([good, bad], ProtocolHeader(), output)
        assert os.path.exists(output)

        import zipfile
        from lxml import etree
        from src.utils.anchors import W_NS, get_para_text
        with zipfile.ZipFile(output, 'r') as z:
            xml = z.read('word/document.xml')
        root = etree.fromstring(xml)
        _W = f'{{{W_NS}}}'
        body = root.find(f'.//{_W}body')
        all_text = ' '.join(get_para_text(e) for e in body.iter(f'{_W}p'))
        assert 'требующие ручной проверки' in all_text
        assert 'no_fragment.docx' in all_text
