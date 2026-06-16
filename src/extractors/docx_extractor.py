import zipfile
import copy
from lxml import etree

from ..models.fragment import Fragment, FragmentStatus
from ..utils.anchors import (
    W_NS, get_para_text, is_start_anchor, is_end_anchor,
    extract_point_number, PROPOSED, VOTING_RESULT, ACCEPTED_DECISION,
)
from .base import BaseExtractor

_W = f'{{{W_NS}}}'
_P = f'{_W}p'
_TBL = f'{_W}tbl'
_BODY = f'{_W}body'
_SECT = f'{_W}sectPr'


class DocxExtractor(BaseExtractor):

    def extract(self, file_path: str) -> Fragment:
        try:
            return self._extract(file_path)
        except Exception as exc:
            return Fragment(
                file_path=file_path,
                original_number='',
                assigned_number='',
                status=FragmentStatus.ERROR,
                confidence=0,
                error_message=str(exc),
            )

    def _extract(self, file_path: str) -> Fragment:
        with zipfile.ZipFile(file_path, 'r') as z:
            xml_bytes = z.read('word/document.xml')

        root = etree.fromstring(xml_bytes)
        body = root.find(f'.//{_BODY}')
        if body is None:
            raise ValueError('No <w:body> found')

        blocks = [e for e in body if e.tag != _SECT]

        # Find start
        start_idx = None
        original_number = ''
        for i, elem in enumerate(blocks):
            if elem.tag == _P:
                text = get_para_text(elem)
                if is_start_anchor(text):
                    start_idx = i
                    original_number = extract_point_number(text)
                    break

        if start_idx is None:
            return Fragment(
                file_path=file_path,
                original_number='',
                assigned_number='',
                status=FragmentStatus.NOT_FOUND,
                confidence=0,
                warnings=['Начальный якорь 1.X. не найден'],
            )

        # Find end
        end_idx = None
        for i in range(start_idx + 1, len(blocks)):
            if blocks[i].tag == _P:
                text = get_para_text(blocks[i]).strip()
                if is_end_anchor(text):
                    end_idx = i
                    break

        # Fallback: last "Принято решение" + 1–2 paras
        if end_idx is None:
            last_dec = None
            for i in range(start_idx, len(blocks)):
                if blocks[i].tag == _P and ACCEPTED_DECISION.search(get_para_text(blocks[i])):
                    last_dec = i
            if last_dec is not None:
                end_idx = min(last_dec + 2, len(blocks) - 1)
            else:
                end_idx = min(start_idx + 20, len(blocks) - 1)

        nodes = blocks[start_idx: end_idx + 1]

        has_table = any(e.tag == _TBL for e in nodes)
        has_proposed = has_voting = has_decision = has_end = False
        text_parts: list[str] = []

        for elem in nodes:
            if elem.tag == _P:
                t = get_para_text(elem)
                text_parts.append(t)
                if PROPOSED.search(t):          has_proposed = True
                if VOTING_RESULT.search(t):     has_voting = True
                if ACCEPTED_DECISION.search(t): has_decision = True
                if is_end_anchor(t.strip()):    has_end = True
            elif elem.tag == _TBL:
                text_parts.append(_table_text(elem))

        confidence = self.calculate_confidence(
            has_start=True,
            has_table=has_table,
            has_proposed=has_proposed,
            has_voting=has_voting,
            has_decision=has_decision,
            has_end=has_end,
        )

        if confidence >= 85:
            status = FragmentStatus.SUCCESS
        elif confidence >= 50:
            status = FragmentStatus.NEEDS_REVIEW
        else:
            status = FragmentStatus.NOT_FOUND

        warnings = []
        if not has_table:    warnings.append("Таблица не найдена")
        if not has_proposed: warnings.append("'Предложено' не найдено")
        if not has_voting:   warnings.append("'В результате голосования' не найдено")
        if not has_decision: warnings.append("'Принято решение' не найдено")
        if not has_end:      warnings.append("Конечный якорь не найден")

        return Fragment(
            file_path=file_path,
            original_number=original_number,
            assigned_number='',
            status=status,
            confidence=confidence,
            xml_nodes=[copy.deepcopy(e) for e in nodes],
            text_preview='\n'.join(text_parts),
            warnings=warnings,
            source_type='docx',
        )


def _table_text(tbl_elem) -> str:
    """Extract table content as text rows for text_preview."""
    _TR = f'{_W}tr'
    _TC = f'{_W}tc'
    rows = []
    for row in tbl_elem.iter(_TR):
        cells = [
            get_para_text(cell).strip()
            for cell in row.findall(_TC)
        ]
        if any(cells):
            rows.append(' | '.join(c for c in cells if c))
    return '[ТАБЛИЦА]\n' + '\n'.join(rows) if rows else '[ТАБЛИЦА]'
