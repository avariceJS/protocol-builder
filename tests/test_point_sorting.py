import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.builders.protocol_builder import _sort_by_point
from src.models.fragment import Fragment, FragmentStatus
from src.utils.anchors import point_sort_key


def _frag(number: str, path: str) -> Fragment:
    return Fragment(
        file_path=path,
        original_number=number,
        assigned_number='',
        status=FragmentStatus.SUCCESS,
        confidence=90,
    )


def test_point_sort_key_numeric():
    assert point_sort_key('1.6.') < point_sort_key('1.30.')
    assert point_sort_key('1.1.') < point_sort_key('1.2.')


def test_sort_fragments_by_point():
    fragments = [
        _frag('1.30.', '/a.docx'),
        _frag('1.1.', '/b.docx'),
        _frag('1.6.', '/c.docx'),
        _frag('1.1.', '/d.docx'),
    ]
    sorted_frags = _sort_by_point(fragments)
    assert [f.file_path for f in sorted_frags] == [
        '/b.docx', '/d.docx', '/c.docx', '/a.docx',
    ]
    assert [f.original_number for f in sorted_frags] == [
        '1.1.', '1.1.', '1.6.', '1.30.',
    ]
