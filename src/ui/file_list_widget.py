import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QFileDialog,
    QAbstractItemView, QHeaderView, QFrame, QMenu, QStyleFactory,
)
from PySide6.QtCore import Qt, Signal, QSize, QPoint
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QIcon, QPixmap, QCursor, QPainterPath, QRegion

from ..models.fragment import Fragment, FragmentStatus
from ..utils.assets import asset_path
from ..utils.russian import format_files_count
from .styles import STATUS_PALETTE, apply_primary_button, apply_danger_button

# (bg, text, border) per status
_STATUS_COLORS = {
    FragmentStatus.SUCCESS:      STATUS_PALETTE['success'],
    FragmentStatus.NEEDS_REVIEW: STATUS_PALETTE['review'],
    FragmentStatus.NOT_FOUND:    STATUS_PALETTE['error'],
    FragmentStatus.ERROR:        STATUS_PALETTE['error'],
}

SUPPORTED_EXT = {'.docx', '.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff'}

_ICON_BUTTON_STYLE = """
QPushButton {
    background: #F3F4F6;
    border: 1px solid #E5E7EB;
    border-radius: 6px;
    padding: 4px;
}
QPushButton:hover {
    background: #E5E7EB;
    border-color: #D1D5DB;
}
QPushButton:pressed {
    background: #D1D5DB;
}
"""

_DROP_ZONE_MENU_STYLE = """
QMenu#dropZoneMenu {
    background-color: #FFFFFF;
    color: #1E1B4B;
    border: 1px solid #E0E4F0;
    border-radius: 8px;
    padding: 6px;
    outline: none;
}
QMenu#dropZoneMenu::item {
    background-color: transparent;
    color: #374151;
    padding: 8px 32px 8px 14px;
    margin: 2px 0;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    border: none;
    outline: none;
}
QMenu#dropZoneMenu::item:selected {
    background-color: #EEF2FF;
    color: #4338CA;
}
QMenu#dropZoneMenu::item:disabled {
    color: #9CA3AF;
}
"""

_MENU_CORNER_RADIUS = 8


def _icon_button(icon_name: str, tooltip: str) -> QPushButton:
    btn = QPushButton()
    btn.setIcon(QIcon(asset_path(icon_name)))
    btn.setIconSize(QSize(16, 16))
    btn.setFixedSize(38, 38)
    btn.setToolTip(tooltip)
    btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    btn.setStyleSheet(_ICON_BUTTON_STYLE)
    return btn


def _apply_rounded_menu_mask(menu: QMenu) -> None:
    radius = _MENU_CORNER_RADIUS
    rect = menu.rect()
    path = QPainterPath()
    path.addRoundedRect(
        float(rect.x()), float(rect.y()),
        float(rect.width()), float(rect.height()),
        radius, radius,
    )
    menu.setMask(QRegion(path.toFillPolygon().toPolygon()))


def _configure_drop_zone_menu(menu: QMenu) -> None:
    menu.setObjectName('dropZoneMenu')
    menu.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    menu.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
    menu.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
    fusion = QStyleFactory.create('Fusion')
    if fusion:
        menu.setStyle(fusion)
    menu.setStyleSheet(_DROP_ZONE_MENU_STYLE)
    menu.aboutToShow.connect(_apply_rounded_menu_mask)


class _DropZone(QFrame):
    files_dropped = Signal(list)
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFixedHeight(64)
        self._idle_style = """
            QFrame {
                background: #FAFBFF;
                border: 2px dashed #C7D2FE;
                border-radius: 10px;
            }
        """
        self._hover_style = """
            QFrame {
                background: #EEF2FF;
                border: 2px dashed #6366F1;
                border-radius: 10px;
            }
        """
        self.setStyleSheet(self._idle_style)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        icon = QLabel()
        pixmap = QPixmap(asset_path('downArrowDropZone.png'))
        icon.setPixmap(pixmap.scaled(
            30, 30,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ))
        icon.setStyleSheet('background: transparent; border: none;')
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFixedWidth(44)

        text = QLabel('Перетащите или нажмите для выбора  (DOCX · PDF · JPG · PNG)')
        text.setStyleSheet('color: #6366F1; font-size: 13px; font-weight: 500; background: transparent; border: none;')

        layout.addStretch()
        layout.addWidget(icon)
        layout.addWidget(text)
        layout.addStretch()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            self.setStyleSheet(self._hover_style)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self._idle_style)

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet(self._idle_style)
        paths = []
        for url in event.mimeData().urls():
            p = url.toLocalFile()
            if os.path.isdir(p):
                for fname in sorted(os.listdir(p)):
                    if os.path.splitext(fname)[1].lower() in SUPPORTED_EXT:
                        paths.append(os.path.join(p, fname))
            elif os.path.splitext(p)[1].lower() in SUPPORTED_EXT:
                paths.append(p)
        if paths:
            self.files_dropped.emit(paths)

    def enterEvent(self, event):
        self.setStyleSheet(self._hover_style)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self._idle_style)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class _StatBadge(QLabel):
    def __init__(self, palette_key: str, label: str, parent=None):
        super().__init__(parent)
        bg, fg, border = STATUS_PALETTE[palette_key]
        self.setStyleSheet(f"""
            QLabel {{
                background: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 12px;
                padding: 2px 10px;
                font-size: 12px;
                font-weight: 600;
            }}
        """)
        self._label = label
        self._update(0)

    def _update(self, n: int):
        self.setText(f'{self._label}: {n}')

    def set_count(self, n: int):
        self._update(n)


class FileListWidget(QWidget):
    files_changed = Signal()
    process_requested = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._frag_map: dict[str, Fragment] = {}   # path → Fragment
        self._file_paths: list[str] = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.btn_add_files = QPushButton('+ Добавить файлы')
        apply_primary_button(self.btn_add_files)
        self.btn_add_folder = QPushButton('+ Добавить папку')
        self.btn_clear = QPushButton('Очистить')
        apply_danger_button(self.btn_clear)
        self.btn_up = _icon_button('upArrow.png', 'Переместить вверх')
        self.btn_down = _icon_button('downArrow.png', 'Переместить вниз')

        toolbar.addWidget(self.btn_add_files)
        toolbar.addWidget(self.btn_add_folder)
        toolbar.addWidget(self.btn_clear)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_up)
        toolbar.addWidget(self.btn_down)
        layout.addLayout(toolbar)

        # Drop zone
        self.drop_zone = _DropZone()
        self.drop_zone.files_dropped.connect(self._add_paths)
        self.drop_zone.clicked.connect(self._pick_files_or_folder)
        layout.addWidget(self.drop_zone)

        # Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(['№', 'Файл', 'Тип', 'Пункт', 'Статус', '%'])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setDefaultSectionSize(90)
        self.table.setColumnWidth(0, 46)
        self.table.setColumnWidth(2, 56)
        self.table.setColumnWidth(3, 72)
        self.table.setColumnWidth(5, 56)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setRowHeight(0, 36)
        layout.addWidget(self.table)

        # Status row
        status_row = QHBoxLayout()
        status_row.setSpacing(8)
        self._total_lbl = QLabel('0 файлов')
        self._total_lbl.setStyleSheet('color: #6B7280; font-size: 12px; padding: 0 4px;')
        self._badge_ok = _StatBadge('success', 'Успешно')
        self._badge_review = _StatBadge('review', 'Проверка')
        self._badge_err = _StatBadge('error', 'Ошибки')
        status_row.addWidget(self._total_lbl)
        status_row.addWidget(self._badge_ok)
        status_row.addWidget(self._badge_review)
        status_row.addWidget(self._badge_err)
        status_row.addStretch()
        layout.addLayout(status_row)

        # Signals
        self.btn_add_files.clicked.connect(self._add_files)
        self.btn_add_folder.clicked.connect(self._add_folder)
        self.btn_clear.clicked.connect(self._clear)
        self.btn_up.clicked.connect(self._move_up)
        self.btn_down.clicked.connect(self._move_down)

    # ── drag-and-drop (whole widget fallback) ─────────────────────────────
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        paths = []
        for url in event.mimeData().urls():
            p = url.toLocalFile()
            if os.path.isdir(p):
                paths.extend(self._scan_dir(p))
            elif os.path.splitext(p)[1].lower() in SUPPORTED_EXT:
                paths.append(p)
        self._add_paths(paths)

    # ── public API ─────────────────────────────────────────────────────────
    def get_file_paths(self) -> list[str]:
        return list(self._file_paths)

    def update_fragment(self, file_path: str, fragment: Fragment):
        self._frag_map[file_path] = fragment
        if file_path in self._file_paths:
            i = self._file_paths.index(file_path)
            self._refresh_row(i)
            self._update_status()

    def set_fragments(self, fragments: list[Fragment]):
        self._frag_map = {f.file_path: f for f in fragments}
        self._refresh_table()

    def get_fragments(self) -> list[Fragment]:
        return [self._frag_map[p] for p in self._file_paths if p in self._frag_map]

    def restore_paths(self, paths: list[str]) -> None:
        self._file_paths = list(paths)
        self._frag_map.clear()
        self._refresh_table()

    # ── private ────────────────────────────────────────────────────────────
    def _pick_files_or_folder(self):
        menu = QMenu(self)
        _configure_drop_zone_menu(menu)
        act_files = menu.addAction('Выбрать файлы…')
        act_folder = menu.addAction('Выбрать папку…')
        center = self.drop_zone.rect().center()
        pos = self.drop_zone.mapToGlobal(QPoint(int(center.x()), int(center.y())))
        chosen = menu.exec(pos)
        if chosen == act_files:
            self._add_files()
        elif chosen == act_folder:
            self._add_folder()

    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, 'Выберите файлы', '',
            'Документы (*.docx *.pdf *.jpg *.jpeg *.png *.bmp *.tiff)'
        )
        self._add_paths(paths)

    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Выберите папку')
        if folder:
            self._add_paths(self._scan_dir(folder))

    def _scan_dir(self, folder: str) -> list[str]:
        paths = []
        for fname in sorted(os.listdir(folder)):
            if os.path.splitext(fname)[1].lower() in SUPPORTED_EXT:
                paths.append(os.path.join(folder, fname))
        return paths

    def _add_paths(self, paths: list[str]):
        new = [p for p in paths if p not in self._file_paths]
        self._file_paths.extend(new)
        self._refresh_table()
        self.files_changed.emit()
        if new:
            self.process_requested.emit(new)

    def _clear(self):
        self._file_paths.clear()
        self._frag_map.clear()
        self.table.setRowCount(0)
        self._update_status()
        self.files_changed.emit()

    def _move_up(self):
        row = self.table.currentRow()
        if row > 0:
            self._file_paths[row], self._file_paths[row - 1] = \
                self._file_paths[row - 1], self._file_paths[row]
            self._refresh_table()
            self.table.selectRow(row - 1)
            self.files_changed.emit()

    def _move_down(self):
        row = self.table.currentRow()
        if row < len(self._file_paths) - 1:
            self._file_paths[row], self._file_paths[row + 1] = \
                self._file_paths[row + 1], self._file_paths[row]
            self._refresh_table()
            self.table.selectRow(row + 1)
            self.files_changed.emit()

    def _refresh_table(self):
        self.table.setRowCount(len(self._file_paths))
        for i in range(len(self._file_paths)):
            self.table.setRowHeight(i, 36)
            self._refresh_row(i)
        self._update_status()

    def _refresh_row(self, i: int):
        fp = self._file_paths[i]
        frag = self._frag_map.get(fp)
        ext = os.path.splitext(fp)[1].upper().lstrip('.')

        self.table.setItem(i, 0, _item(str(i + 1), center=True))
        self.table.setItem(i, 1, _item(os.path.basename(fp)))
        self.table.setItem(i, 2, _item(ext, center=True))
        point = frag.original_number if frag else ''
        self.table.setItem(i, 3, _item(point or '—', center=True))

        if frag:
            colors = _STATUS_COLORS.get(frag.status)
            bg_hex, fg_hex, _ = colors if colors else ('#FFFFFF', '#1E1B4B', '#E5E7EB')
            bg = QColor(bg_hex)
            fg = QColor(fg_hex)

            status_item = _item(frag.status.value, center=True)
            conf_item = _item(f'{frag.confidence}%', center=True)

            for col, it in enumerate([
                self.table.item(i, 0),
                self.table.item(i, 1),
                self.table.item(i, 2),
                self.table.item(i, 3),
                status_item,
                conf_item,
            ]):
                if it:
                    it.setBackground(bg)
                    it.setForeground(fg)

            self.table.setItem(i, 4, status_item)
            self.table.setItem(i, 5, conf_item)
        else:
            self.table.setItem(i, 4, _item('Ожидание…', center=True))
            self.table.setItem(i, 5, _item('—', center=True))

    def _update_status(self):
        total = len(self._file_paths)
        frags = self._frag_map.values()
        ok = sum(1 for f in frags if f.status == FragmentStatus.SUCCESS)
        review = sum(1 for f in frags if f.status == FragmentStatus.NEEDS_REVIEW)
        err = sum(1 for f in frags if f.status in (FragmentStatus.NOT_FOUND, FragmentStatus.ERROR))
        self._total_lbl.setText(format_files_count(total))
        self._badge_ok.set_count(ok)
        self._badge_review.set_count(review)
        self._badge_err.set_count(err)


def _item(text: str, center: bool = False) -> QTableWidgetItem:
    it = QTableWidgetItem(text)
    if center:
        it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    else:
        it.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
    return it
