import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QTextEdit, QLabel,
    QPushButton, QFrame, QStyledItemDelegate,
    QStyleOptionViewItem,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor, QFont, QBrush, QPainter

from ..models.fragment import Fragment, FragmentStatus
from .styles import (
    STATUS_PALETTE, apply_danger_button, apply_secondary_button, apply_success_button,
)

_STYLE_ROLE = Qt.ItemDataRole.UserRole + 1

_STATUS_COLORS = {
    FragmentStatus.SUCCESS:      STATUS_PALETTE['success'],
    FragmentStatus.NEEDS_REVIEW: STATUS_PALETTE['review'],
    FragmentStatus.NOT_FOUND:    STATUS_PALETTE['error'],
    FragmentStatus.ERROR:        STATUS_PALETTE['error'],
}


class _FragmentItemDelegate(QStyledItemDelegate):
    """Рисует фон элементов списка — setBackground() не работает при QSS на macOS."""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        style_data = index.data(_STYLE_ROLE)
        if style_data:
            bg_hex, fg_hex = style_data
            bg = QColor(bg_hex)
            fg = QColor(fg_hex)
            opt.backgroundBrush = QBrush(bg)
            opt.palette.setBrush(opt.palette.ColorRole.Text, QBrush(fg))
            opt.palette.setBrush(opt.palette.ColorRole.Highlight, QBrush(bg))
            opt.palette.setBrush(opt.palette.ColorRole.HighlightedText, QBrush(fg))

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = option.rect.adjusted(2, 2, -2, -4)
        if style_data:
            painter.setBrush(QBrush(bg))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 6, 6)
            painter.setPen(fg)
            text_rect = rect.adjusted(10, 0, -10, 0)
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextSingleLine,
                index.data(Qt.ItemDataRole.DisplayRole) or '',
            )
        else:
            super().paint(painter, opt, index)
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 46)


class PreviewWidget(QWidget):
    exclude_toggled = Signal(str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fragments: list[Fragment] = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(6)

        # ── Left panel ────────────────────────────────────────────────────
        left = QWidget()
        left.setStyleSheet('background: #F0F2F8;')
        lv = QVBoxLayout(left)
        lv.setContentsMargins(16, 16, 8, 16)
        lv.setSpacing(8)

        lbl_files = QLabel('Файлы')
        lbl_files.setStyleSheet('color: #4B5563; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;')
        lv.addWidget(lbl_files)

        self.file_list = QListWidget()
        self.file_list.setItemDelegate(_FragmentItemDelegate(self.file_list))
        self.file_list.setStyleSheet("""
            QListWidget {
                background: #FFFFFF;
                border: 1.5px solid #E5E7EB;
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }
            QListWidget::item {
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        self.file_list.currentRowChanged.connect(self._show_fragment)
        lv.addWidget(self.file_list)
        splitter.addWidget(left)

        # ── Right panel ───────────────────────────────────────────────────
        right = QWidget()
        right.setStyleSheet('background: #FFFFFF;')
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(0)

        # File name header
        self._detail_header = QFrame()
        self._detail_header.setStyleSheet("""
            QFrame {
                background: #F8F9FF;
                border-bottom: 1.5px solid #E5E7EB;
            }
        """)
        hh = QVBoxLayout(self._detail_header)
        hh.setContentsMargins(20, 14, 20, 14)
        hh.setSpacing(4)

        self.lbl_name = QLabel('Выберите файл из списка')
        self.lbl_name.setStyleSheet('font-size: 14px; font-weight: 700; color: #1E1B4B; background: transparent;')
        hh.addWidget(self.lbl_name)

        self.lbl_status = QLabel('')
        self.lbl_status.setStyleSheet('font-size: 12px; color: #6B7280; background: transparent;')
        hh.addWidget(self.lbl_status)

        rv.addWidget(self._detail_header)

        # Warning banner
        self._warn_frame = QFrame()
        self._warn_frame.setVisible(False)
        warn_layout = QHBoxLayout(self._warn_frame)
        warn_layout.setContentsMargins(20, 10, 20, 10)
        self.lbl_warnings = QLabel('')
        self.lbl_warnings.setWordWrap(True)
        self.lbl_warnings.setStyleSheet('font-size: 12px; background: transparent;')
        warn_layout.addWidget(self.lbl_warnings)
        rv.addWidget(self._warn_frame)

        # Preview area
        preview_container = QVBoxLayout()
        preview_container.setContentsMargins(20, 16, 20, 0)
        preview_container.setSpacing(6)
        lbl_preview = QLabel('Извлечённый фрагмент')
        lbl_preview.setStyleSheet('color: #4B5563; font-size: 11px; font-weight: 600;')
        preview_container.addWidget(lbl_preview)
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont('Times New Roman', 10))
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background: #FAFBFF;
                border: 1.5px solid #E5E7EB;
                border-radius: 8px;
                padding: 10px;
                color: #1E1B4B;
            }
        """)
        preview_container.addWidget(self.preview_text)
        rv.addLayout(preview_container)

        # Action row
        btn_frame = QFrame()
        btn_frame.setStyleSheet('background: #F8F9FF; border-top: 1.5px solid #E5E7EB;')
        btn_row = QHBoxLayout(btn_frame)
        btn_row.setContentsMargins(20, 12, 20, 12)
        btn_row.setSpacing(10)

        self.btn_exclude = QPushButton('Исключить из протокола')
        apply_danger_button(self.btn_exclude)
        self.btn_include = QPushButton('Включить в протокол')
        apply_secondary_button(self.btn_include)
        btn_row.addWidget(self.btn_exclude)
        btn_row.addWidget(self.btn_include)
        btn_row.addStretch()
        rv.addWidget(btn_frame)

        splitter.addWidget(right)
        splitter.setSizes([230, 650])
        layout.addWidget(splitter)

        self.btn_exclude.clicked.connect(self._exclude_current)
        self.btn_include.clicked.connect(self._include_current)

    def set_fragments(self, fragments: list[Fragment]):
        self._fragments = fragments
        self._rebuild_list()

    def update_fragment(self, fragment: Fragment):
        for i, f in enumerate(self._fragments):
            if f.file_path == fragment.file_path:
                self._fragments[i] = fragment
                self._update_list_item(i, fragment)
                if self.file_list.currentRow() == i:
                    self._show_fragment(i)
                return

    def _rebuild_list(self):
        self.file_list.clear()
        for frag in self._fragments:
            self._add_list_item(frag)

    def _add_list_item(self, frag: Fragment):
        name = os.path.basename(frag.file_path)
        item = QListWidgetItem(name)
        self._apply_item_style(item, frag)
        self.file_list.addItem(item)

    def _apply_item_style(self, item: QListWidgetItem, frag: Fragment, selected: bool = False):
        if not frag.include_in_protocol:
            bg_hex, fg_hex, _ = STATUS_PALETTE['error']
            if selected:
                bg_hex = '#FECDD3'
        else:
            colors = _STATUS_COLORS.get(frag.status)
            bg_hex, fg_hex = '#FFFFFF', '#1E1B4B'
            if colors:
                bg_hex, fg_hex, _ = colors
                if selected:
                    bg_hex, fg_hex = '#C7D2FE', '#1E1B4B'
        item.setData(_STYLE_ROLE, (bg_hex, fg_hex))
        font = item.font()
        font.setStrikeOut(False)
        item.setFont(font)

    def _refresh_list_styles(self):
        current = self.file_list.currentRow()
        for i, frag in enumerate(self._fragments):
            item = self.file_list.item(i)
            if item:
                self._apply_item_style(item, frag, selected=(i == current))
        self.file_list.viewport().update()

    def _update_list_item(self, i: int, frag: Fragment):
        item = self.file_list.item(i)
        if item:
            self._apply_item_style(item, frag, selected=(self.file_list.currentRow() == i))
            self.file_list.viewport().update()

    def _update_action_buttons(self, included: bool):
        if included:
            apply_danger_button(self.btn_exclude)
            apply_secondary_button(self.btn_include)
        else:
            apply_secondary_button(self.btn_exclude)
            apply_success_button(self.btn_include)

    def _show_fragment(self, row: int):
        if row < 0 or row >= len(self._fragments):
            return
        self._refresh_list_styles()
        frag = self._fragments[row]
        self.lbl_name.setText(os.path.basename(frag.file_path))

        status_parts = [f'Статус: {frag.status.value}', f'Confidence: {frag.confidence}%']
        if frag.original_number:
            status_parts.append(f'Пункт: {frag.original_number}')
        if not frag.include_in_protocol:
            status_parts.append('Исключён — не войдёт в протокол')
        self.lbl_status.setText('  ·  '.join(status_parts))
        self._update_action_buttons(frag.include_in_protocol)

        # Warning/error banner
        if frag.warnings or frag.error_message:
            msg = ('⚠  ' + '; '.join(frag.warnings)) if frag.warnings else ('✗  ' + frag.error_message)
            is_err = bool(frag.error_message)
            palette = STATUS_PALETTE['error'] if is_err else STATUS_PALETTE['review']
            bg, fg, border = palette
            self._warn_frame.setStyleSheet(f"""
                QFrame {{
                    background: {bg};
                    border-bottom: 1px solid {border};
                }}
            """)
            self.lbl_warnings.setStyleSheet(f'font-size: 12px; color: {fg}; background: transparent;')
            self.lbl_warnings.setText(msg)
            self._warn_frame.setVisible(True)
        else:
            self._warn_frame.setVisible(False)

        self.preview_text.setPlainText(frag.text_preview or '(нет текста)')

    def _exclude_current(self):
        row = self.file_list.currentRow()
        if 0 <= row < len(self._fragments):
            self._fragments[row].include_in_protocol = False
            self._update_list_item(row, self._fragments[row])
            self._show_fragment(row)
            self.exclude_toggled.emit(self._fragments[row].file_path, False)

    def _include_current(self):
        row = self.file_list.currentRow()
        if 0 <= row < len(self._fragments):
            self._fragments[row].include_in_protocol = True
            self._update_list_item(row, self._fragments[row])
            self._show_fragment(row)
            self.exclude_toggled.emit(self._fragments[row].file_path, True)
