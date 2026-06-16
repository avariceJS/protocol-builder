"""History of generated protocol files on the Build tab."""

from __future__ import annotations

import os
import shutil
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QFileDialog, QMessageBox, QSizePolicy,
)

from ..models.protocol_history import ProtocolHistoryEntry, ProtocolHistoryStore
from ..utils.platform_utils import open_path, reveal_path
from ..utils.russian import format_files_count
from .styles import (
    apply_danger_button,
    apply_plain_label,
    apply_secondary_button,
    apply_success_button,
)


_HISTORY_PANEL_STYLE = """
QFrame#historyPanel {
    background: #FFFFFF;
    border: 1.5px solid #E0E4F0;
    border-radius: 12px;
}
"""

_COMPACT_BUTTON_EXTRA = """
QPushButton {
    padding: 5px 12px;
    font-size: 12px;
    border-radius: 6px;
}
"""


def _format_created_at(iso_value: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_value.replace('Z', '+00:00'))
        local = dt.astimezone()
        return local.strftime('%d.%m.%Y  %H:%M')
    except ValueError:
        return iso_value


def _elide_path(path: str, max_chars: int = 52) -> str:
    if len(path) <= max_chars:
        return path
    folder, name = os.path.split(path)
    if len(name) + 6 >= max_chars:
        return '…' + name[-(max_chars - 1):]
    budget = max_chars - len(name) - 3
    if budget <= 0:
        return '…' + name
    if len(folder) <= budget:
        return path
    return '…' + folder[-budget:] + os.sep + name


class _DocBadge(QLabel):
    def __init__(self, parent=None):
        super().__init__('DOCX', parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(40, 40)
        self.setStyleSheet("""
            QLabel {
                background: #EEF2FF;
                color: #4338CA;
                border: 1px solid #C7D2FE;
                border-radius: 8px;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.4px;
            }
        """)


class _HistoryEntryRow(QFrame):
    def __init__(self, entry: ProtocolHistoryEntry, on_delete, parent=None):
        super().__init__(parent)
        self._entry = entry
        self._on_delete = on_delete
        self._build()

    def _build(self) -> None:
        missing = not self._entry.exists
        self.setObjectName('historyEntry')
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        if missing:
            bg, border = '#FFFBEB', '#FDE68A'
            path_color = '#B45309'
        else:
            bg, border = '#F8F9FF', '#E0E7FF'
            path_color = '#64748B'

        self.setStyleSheet(f"""
            QFrame#historyEntry {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 10px;
            }}
            QFrame#historyEntry QLabel {{
                border: none;
                background: transparent;
                padding: 0;
                margin: 0;
            }}
        """)

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 12, 14, 12)
        root.setSpacing(12)

        badge = _DocBadge()
        if missing:
            badge.setStyleSheet("""
                QLabel {
                    background: #FEF3C7;
                    color: #B45309;
                    border: 1px solid #FCD34D;
                    border-radius: 8px;
                    font-size: 10px;
                    font-weight: 700;
                    letter-spacing: 0.4px;
                }
            """)
        root.addWidget(badge, alignment=Qt.AlignmentFlag.AlignTop)

        body = QVBoxLayout()
        body.setSpacing(4)
        body.setContentsMargins(0, 0, 0, 0)

        top = QHBoxLayout()
        top.setSpacing(10)

        title = QLabel(self._entry.file_name)
        apply_plain_label(
            title,
            'font-size: 13px; font-weight: 600;',
            '#1E1B4B',
        )
        top.addWidget(title, stretch=1)

        date_chip = QLabel(_format_created_at(self._entry.created_at))
        date_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date_chip.setStyleSheet("""
            QLabel {
                background: #FFFFFF;
                color: #64748B;
                border: 1px solid #E2E8F0;
                border-radius: 999px;
                padding: 2px 10px;
                font-size: 11px;
                font-weight: 500;
            }
        """)
        top.addWidget(date_chip, alignment=Qt.AlignmentFlag.AlignTop)
        body.addLayout(top)

        self._path_lbl = QLabel(_elide_path(self._entry.path))
        self._path_lbl.setToolTip(self._entry.path)
        apply_plain_label(self._path_lbl, 'font-size: 11px;', path_color)
        body.addWidget(self._path_lbl)

        if missing:
            warn = QLabel('Файл не найден на диске')
            apply_plain_label(warn, 'font-size: 12px; font-weight: 500;', '#B45309')
            body.addWidget(warn)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        btn_row.setContentsMargins(0, 6, 0, 0)

        self.btn_open = QPushButton('Открыть')
        self.btn_folder = QPushButton('В папке')
        self.btn_copy = QPushButton('Копия…')
        self.btn_delete = QPushButton('Удалить')

        apply_success_button(self.btn_open)
        apply_secondary_button(self.btn_folder)
        apply_secondary_button(self.btn_copy)
        apply_danger_button(self.btn_delete)

        for btn in (self.btn_open, self.btn_folder, self.btn_copy, self.btn_delete):
            btn.setStyleSheet(btn.styleSheet() + _COMPACT_BUTTON_EXTRA)

        self.btn_open.setEnabled(not missing)
        self.btn_folder.setEnabled(bool(self._entry.path))
        self.btn_copy.setEnabled(not missing)

        btn_row.addWidget(self.btn_open)
        btn_row.addWidget(self.btn_folder)
        btn_row.addWidget(self.btn_copy)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_delete)
        body.addLayout(btn_row)

        root.addLayout(body, stretch=1)

        self.btn_open.clicked.connect(self._open_file)
        self.btn_folder.clicked.connect(self._open_folder)
        self.btn_copy.clicked.connect(self._save_copy)
        self.btn_delete.clicked.connect(self._delete_entry)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        metrics = QFontMetrics(self._path_lbl.font())
        elided = metrics.elidedText(
            self._entry.path,
            Qt.TextElideMode.ElideMiddle,
            max(self._path_lbl.width(), 120),
        )
        self._path_lbl.setText(elided)

    def _open_file(self) -> None:
        if self._entry.exists:
            open_path(self._entry.path)

    def _open_folder(self) -> None:
        if self._entry.path:
            reveal_path(self._entry.path)

    def _save_copy(self) -> None:
        if not self._entry.exists:
            return
        dest, _ = QFileDialog.getSaveFileName(
            self, 'Сохранить копию', self._entry.file_name, 'Word Document (*.docx)'
        )
        if dest:
            shutil.copy2(self._entry.path, dest)

    def _delete_entry(self) -> None:
        if self._entry.exists:
            text = (
                f'Удалить «{self._entry.file_name}» из истории и с диска?\n\n'
                f'{self._entry.path}'
            )
        else:
            text = f'Файл уже отсутствует. Убрать «{self._entry.file_name}» из истории?'

        answer = QMessageBox.question(
            self,
            'Удалить протокол',
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._on_delete(self._entry.id, delete_file=self._entry.exists)


class BuildHistoryWidget(QWidget):
    def __init__(self, store: ProtocolHistoryStore | None = None, parent=None):
        super().__init__(parent)
        self._store = store or ProtocolHistoryStore()
        self._rows: list[_HistoryEntryRow] = []
        self._build()
        self.refresh()

    @property
    def store(self) -> ProtocolHistoryStore:
        return self._store

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._panel = QFrame()
        self._panel.setObjectName('historyPanel')
        self._panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._panel.setStyleSheet(_HISTORY_PANEL_STYLE)

        panel_layout = QVBoxLayout(self._panel)
        panel_layout.setContentsMargins(16, 14, 16, 14)
        panel_layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(8)

        title = QLabel('История сформированных протоколов')
        apply_plain_label(title, 'font-size: 14px; font-weight: 700;', '#1E1B4B')
        header.addWidget(title)
        header.addStretch()

        self._count_lbl = QLabel('')
        self._count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._count_lbl.setStyleSheet("""
            QLabel {
                background: #EEF2FF;
                color: #4338CA;
                border: 1px solid #C7D2FE;
                border-radius: 999px;
                padding: 2px 10px;
                font-size: 11px;
                font-weight: 600;
            }
        """)
        self._count_lbl.setVisible(False)
        header.addWidget(self._count_lbl)
        panel_layout.addLayout(header)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self._scroll.setStyleSheet('QScrollArea { background: transparent; border: none; }')

        self._list_host = QWidget()
        self._list_host.setStyleSheet('background: transparent;')
        self._list_layout = QVBoxLayout(self._list_host)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(8)

        self._empty_frame = QFrame()
        self._empty_frame.setObjectName('historyEmpty')
        self._empty_frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._empty_frame.setStyleSheet("""
            QFrame#historyEmpty {
                background: #F8F9FF;
                border: 1.5px dashed #C7D2FE;
                border-radius: 10px;
            }
            QFrame#historyEmpty QLabel {
                border: none;
                background: transparent;
            }
        """)
        empty_layout = QVBoxLayout(self._empty_frame)
        empty_layout.setContentsMargins(20, 28, 20, 28)
        empty_layout.setSpacing(4)

        empty_title = QLabel('Пока нет сформированных протоколов')
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        apply_plain_label(empty_title, 'font-size: 13px; font-weight: 600;', '#6366F1')

        empty_hint = QLabel('После сборки файл появится здесь — можно открыть, скопировать или удалить')
        empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_hint.setWordWrap(True)
        apply_plain_label(empty_hint, 'font-size: 12px;', '#94A3B8')

        empty_layout.addWidget(empty_title)
        empty_layout.addWidget(empty_hint)

        self._scroll.setWidget(self._list_host)
        panel_layout.addWidget(self._scroll)

        self._error_frame = QFrame()
        self._error_frame.setVisible(False)
        self._error_frame.setObjectName('historyError')
        self._error_frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._error_frame.setStyleSheet("""
            QFrame#historyError {
                background: #FFF1F2;
                border: 1px solid #FECDD3;
                border-radius: 10px;
            }
            QFrame#historyError QLabel {
                border: none;
                background: transparent;
                padding: 0;
            }
        """)
        error_layout = QVBoxLayout(self._error_frame)
        error_layout.setContentsMargins(14, 12, 14, 12)
        self._error_label = QLabel('')
        self._error_label.setWordWrap(True)
        apply_plain_label(self._error_label, 'font-size: 13px;', '#9F1239')
        error_layout.addWidget(self._error_label)
        panel_layout.addWidget(self._error_frame)

        layout.addWidget(self._panel)

    def _update_scroll_height(self) -> None:
        entries = len(self._rows)
        if entries == 0:
            self._scroll.setMinimumHeight(self._empty_frame.sizeHint().height())
            self._scroll.setMaximumHeight(16777215)
            return

        row_height = self._rows[0].sizeHint().height() if self._rows else 96
        spacing = self._list_layout.spacing()
        content_h = entries * row_height + max(0, entries - 1) * spacing + 4
        max_visible = min(content_h, 320)
        self._scroll.setMinimumHeight(max_visible)
        self._scroll.setMaximumHeight(max_visible if content_h > 320 else 16777215)

    def add_entry(self, path: str) -> ProtocolHistoryEntry:
        entry = self._store.add(path)
        self.refresh()
        self._error_frame.setVisible(False)
        return entry

    def show_error(self, message: str) -> None:
        self._error_label.setText(f'✗  Ошибка сборки:\n{message}')
        self._error_frame.setVisible(True)

    def clear_error(self) -> None:
        self._error_frame.setVisible(False)

    def _clear_list_layout(self) -> None:
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            widget = item.widget()
            if widget and widget is not self._empty_frame:
                widget.deleteLater()

    def refresh(self) -> None:
        for row in self._rows:
            row.setParent(None)
            row.deleteLater()
        self._rows.clear()
        self._clear_list_layout()

        entries = self._store.entries
        count = len(entries)
        self._count_lbl.setText(format_files_count(count) if count else '')
        self._count_lbl.setVisible(count > 0)

        if not entries:
            self._list_layout.addWidget(self._empty_frame)
            self._empty_frame.show()
            self._update_scroll_height()
            return

        self._empty_frame.hide()
        for entry in entries:
            row = _HistoryEntryRow(entry, self._delete_entry)
            self._rows.append(row)
            self._list_layout.addWidget(row)

        self._update_scroll_height()

    def _delete_entry(self, entry_id: str, *, delete_file: bool) -> None:
        self._store.remove(entry_id, delete_file=delete_file)
        self.refresh()
