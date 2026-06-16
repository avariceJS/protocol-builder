"""History of generated protocol files on the Build tab."""

from __future__ import annotations

import os
import shutil
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QFileDialog, QMessageBox, QSizePolicy,
)

from ..models.protocol_history import ProtocolHistoryEntry, ProtocolHistoryStore
from ..utils.platform_utils import open_path, reveal_path
from .styles import apply_danger_button


def _format_created_at(iso_value: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_value.replace('Z', '+00:00'))
        local = dt.astimezone()
        return local.strftime('%d.%m.%Y  %H:%M')
    except ValueError:
        return iso_value


class _HistoryEntryRow(QFrame):
    def __init__(self, entry: ProtocolHistoryEntry, on_delete, parent=None):
        super().__init__(parent)
        self._entry = entry
        self._on_delete = on_delete
        self._build()

    def _build(self) -> None:
        missing = not self._entry.exists
        bg = '#FFFBEB' if missing else '#ECFDF5'
        border = '#FCD34D' if missing else '#6EE7B7'
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1.5px solid {border};
                border-radius: 10px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        top = QHBoxLayout()
        top.setSpacing(12)

        title = QLabel(self._entry.file_name)
        title.setStyleSheet(
            'font-size: 14px; font-weight: 700; color: #1E1B4B; background: transparent;'
        )
        top.addWidget(title, stretch=1)

        date_lbl = QLabel(_format_created_at(self._entry.created_at))
        date_lbl.setStyleSheet(
            'font-size: 12px; color: #6B7280; background: transparent;'
        )
        top.addWidget(date_lbl)
        layout.addLayout(top)

        path_lbl = QLabel(self._entry.path)
        path_lbl.setWordWrap(True)
        path_lbl.setStyleSheet(
            'font-size: 12px; color: #065F46; background: transparent;'
            if not missing else
            'font-size: 12px; color: #92400E; background: transparent;'
        )
        layout.addWidget(path_lbl)

        if missing:
            warn = QLabel('Файл не найден на диске')
            warn.setStyleSheet(
                'font-size: 12px; color: #92400E; font-weight: 600; background: transparent;'
            )
            layout.addWidget(warn)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.btn_open = QPushButton('Открыть')
        self.btn_folder = QPushButton('Показать в папке')
        self.btn_copy = QPushButton('Сохранить копию…')
        self.btn_delete = QPushButton('Удалить')

        for btn in (self.btn_open, self.btn_folder, self.btn_copy):
            btn.setObjectName('small')

        apply_danger_button(self.btn_delete)
        self.btn_delete.setText('Удалить')

        self.btn_open.setEnabled(not missing)
        self.btn_folder.setEnabled(bool(self._entry.path))
        self.btn_copy.setEnabled(not missing)

        btn_row.addWidget(self.btn_open)
        btn_row.addWidget(self.btn_folder)
        btn_row.addWidget(self.btn_copy)
        btn_row.addWidget(self.btn_delete)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.btn_open.clicked.connect(self._open_file)
        self.btn_folder.clicked.connect(self._open_folder)
        self.btn_copy.clicked.connect(self._save_copy)
        self.btn_delete.clicked.connect(self._delete_entry)

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
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel('История сформированных протоколов')
        title.setStyleSheet(
            'font-size: 14px; font-weight: 700; color: #1E1B4B; background: transparent;'
        )
        self._count_lbl = QLabel('')
        self._count_lbl.setStyleSheet(
            'font-size: 12px; color: #6B7280; background: transparent;'
        )
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self._count_lbl)
        layout.addLayout(header)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet('QScrollArea { background: transparent; border: none; }')

        self._list_host = QWidget()
        self._list_host.setStyleSheet('background: transparent;')
        self._list_layout = QVBoxLayout(self._list_host)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(10)

        self._empty_lbl = QLabel('Пока нет сформированных протоколов')
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setStyleSheet(
            'color: #9CA3AF; font-size: 13px; padding: 24px; background: transparent;'
        )
        self._empty_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._scroll.setWidget(self._list_host)
        layout.addWidget(self._scroll, stretch=1)

        self._error_frame = QFrame()
        self._error_frame.setVisible(False)
        self._error_frame.setStyleSheet("""
            QFrame {
                background: #FFF1F2;
                border: 1.5px solid #FCA5A5;
                border-radius: 10px;
            }
        """)
        error_layout = QVBoxLayout(self._error_frame)
        error_layout.setContentsMargins(14, 12, 14, 12)
        self._error_label = QLabel('')
        self._error_label.setWordWrap(True)
        self._error_label.setStyleSheet(
            'font-size: 13px; color: #9F1239; background: transparent;'
        )
        error_layout.addWidget(self._error_label)
        layout.addWidget(self._error_frame)

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
            if widget and widget is not self._empty_lbl:
                widget.deleteLater()

    def refresh(self) -> None:
        for row in self._rows:
            row.setParent(None)
            row.deleteLater()
        self._rows.clear()
        self._clear_list_layout()

        entries = self._store.entries
        count = len(entries)
        self._count_lbl.setText(f'{count} файл(ов)' if count else '')

        if not entries:
            self._list_layout.addWidget(self._empty_lbl)
            self._empty_lbl.show()
            return

        self._empty_lbl.hide()
        for entry in entries:
            row = _HistoryEntryRow(entry, self._delete_entry)
            self._rows.append(row)
            self._list_layout.addWidget(row)
        self._list_layout.addStretch()

    def _delete_entry(self, entry_id: str, *, delete_file: bool) -> None:
        self._store.remove(entry_id, delete_file=delete_file)
        self.refresh()
