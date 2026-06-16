import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.extractors.base import BaseExtractor
from src.extractors.docx_extractor import DocxExtractor
from src.models.fragment import FragmentStatus

SAMPLE = os.path.join(os.path.dirname(__file__), 'fixtures', 'sample_extract.docx')


class TestConfidenceScoring:
    def test_full_fragment_high_confidence(self):
        score = BaseExtractor.calculate_confidence(
            has_start=True, has_table=True, has_proposed=True,
            has_voting=True, has_decision=True, has_end=True,
        )
        assert score >= 85

    def test_header_only_low_confidence(self):
        score = BaseExtractor.calculate_confidence(
            has_start=True, has_table=False, has_proposed=False,
            has_voting=False, has_decision=False, has_end=False,
        )
        assert score < 50

    def test_sample_full_confidence(self):
        frag = DocxExtractor().extract(SAMPLE)
        assert frag.confidence >= 85
        assert frag.status == FragmentStatus.SUCCESS

    def test_partial_confidence_range(self):
        score = BaseExtractor.calculate_confidence(
            has_start=True, has_table=True, has_proposed=True,
            has_voting=False, has_decision=False, has_end=False,
        )
        assert 50 <= score < 85
