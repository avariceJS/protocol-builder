from ..models.fragment import Fragment, FragmentStatus
from ..utils.anchors import (
    is_start_anchor, is_end_anchor, extract_point_number,
    PROPOSED, VOTING_RESULT, ACCEPTED_DECISION,
)
from .base import BaseExtractor


class ImageExtractor(BaseExtractor):

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
        lines = self._ocr(file_path)
        if not lines:
            return Fragment(
                file_path=file_path,
                original_number='',
                assigned_number='',
                status=FragmentStatus.NOT_FOUND,
                confidence=0,
                warnings=['OCR не вернул текст'],
            )

        start_idx = None
        original_number = ''
        for i, line in enumerate(lines):
            if is_start_anchor(line.strip()):
                start_idx = i
                original_number = extract_point_number(line.strip())
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

        end_idx = None
        for i in range(start_idx + 1, len(lines)):
            if is_end_anchor(lines[i].strip()):
                end_idx = i
                break

        if end_idx is None:
            last_dec = None
            for i in range(start_idx, len(lines)):
                if ACCEPTED_DECISION.search(lines[i]):
                    last_dec = i
            end_idx = min(last_dec + 2, len(lines) - 1) if last_dec else min(start_idx + 30, len(lines) - 1)

        fragment_lines = lines[start_idx: end_idx + 1]
        text = '\n'.join(fragment_lines)

        has_proposed = bool(PROPOSED.search(text))
        has_voting = bool(VOTING_RESULT.search(text))
        has_decision = bool(ACCEPTED_DECISION.search(text))
        has_end = any(is_end_anchor(l.strip()) for l in fragment_lines)

        # Аналогично изображениям: блок может быть разбит так, что точная
        # фраза «В результате голосования» не распознаётся, но итоговый
        # якорь присутствует.
        if not has_voting and (has_decision or has_end):
            has_voting = True

        confidence = self.calculate_confidence(
            has_start=True,
            has_table=False,
            has_proposed=has_proposed,
            has_voting=has_voting,
            has_decision=has_decision,
            has_end=has_end,
        )

        warnings = ['Изображение: форматирование распознано текстом']
        if not has_proposed: warnings.append("'Предложено' не найдено")
        if not has_voting:   warnings.append("'В результате голосования' не найдено")
        if not has_decision: warnings.append("'Принято решение' не найдено")
        if not has_end:      warnings.append("Конечный якорь не найден")

        status = (
            FragmentStatus.SUCCESS if confidence >= 85
            else FragmentStatus.NEEDS_REVIEW if confidence >= 50
            else FragmentStatus.NOT_FOUND
        )

        return Fragment(
            file_path=file_path,
            original_number=original_number,
            assigned_number='',
            status=status,
            confidence=confidence,
            xml_nodes=[],
            text_preview=text,
            warnings=warnings,
            source_type='image',
        )

    def _ocr(self, file_path: str) -> list[str]:
        try:
            import pytesseract
        except ImportError:
            raise RuntimeError(
                'pytesseract не установлен. Выполните: pip install pytesseract'
            )

        try:
            from PIL import Image
        except ImportError:
            raise RuntimeError(
                'Pillow не установлен. Выполните: pip install Pillow'
            )

        try:
            from PIL import Image
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img, lang='rus')
            return text.splitlines()
        except pytesseract.TesseractNotFoundError:
            raise RuntimeError(
                'Tesseract OCR не найден. Установите Tesseract с русским языковым пакетом.\n'
                'Windows: https://github.com/UB-Mannheim/tesseract/wiki\n'
                'macOS: brew install tesseract tesseract-lang'
            )
        except Exception as e:
            raise RuntimeError(f'Ошибка OCR: {e}')
