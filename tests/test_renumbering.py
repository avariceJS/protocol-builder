import sys, os
import copy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.utils.renumbering import renumber_text, renumber_node
from src.extractors.docx_extractor import DocxExtractor
from src.models.fragment import FragmentStatus

SAMPLE = os.path.join(os.path.dirname(__file__), 'fixtures', 'sample_extract.docx')


class TestRenumberText:
    def test_basic(self):
        assert renumber_text('1.1. Заголовок', 3) == '1.3. Заголовок'

    def test_large_number(self):
        assert renumber_text('1.50. Текст', 2) == '1.2. Текст'

    def test_no_match(self):
        text = 'Предложено: что-то сделать'
        assert renumber_text(text, 5) == text

    def test_three_fragments(self):
        originals = ['1.1. A', '1.7. B', '1.50. C']
        expected = ['1.1. A', '1.2. B', '1.3. C']
        for i, (orig, exp) in enumerate(zip(originals, expected), start=1):
            assert renumber_text(orig, i) == exp


class TestRenumberNode:
    @pytest.fixture
    def fragment(self):
        return DocxExtractor().extract(SAMPLE)

    def test_renumber_xml(self, fragment):
        assert fragment.status == FragmentStatus.SUCCESS
        nodes = [copy.deepcopy(n) for n in fragment.xml_nodes]
        result = renumber_node(nodes[0], 7)
        assert result is True
        from src.utils.anchors import get_para_text
        text = get_para_text(nodes[0])
        assert '1.7.' in text, f'Expected 1.7. in: {text!r}'
        assert '1.1.' not in text, f'Old number should be replaced, got: {text!r}'
