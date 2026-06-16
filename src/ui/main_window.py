import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QProgressBar, QLabel,
    QFileDialog, QMessageBox, QStatusBar, QFrame,
)
from PySide6.QtCore import Qt, QThread, Signal, QObject

from .file_list_widget import FileListWidget, SUPPORTED_EXT
from .preview_widget import PreviewWidget
from .header_form import HeaderForm
from .build_history_widget import BuildHistoryWidget
from .styles import apply_header_bar, apply_primary_button, style_header_title, style_header_subtitle, style_header_status
from ..models.fragment import Fragment, FragmentStatus
from ..builders.protocol_builder import build_protocol


class _ExtractionWorker(QObject):
    fragment_ready = Signal(object)
    finished = Signal()

    def __init__(self, file_paths: list, parent=None):
        super().__init__(parent)
        self._paths = file_paths

    def run(self):
        from ..extractors.docx_extractor import DocxExtractor
        from ..extractors.pdf_extractor import PdfExtractor
        from ..extractors.image_extractor import ImageExtractor

        extractors = {
            '.docx': DocxExtractor(),
            '.pdf': PdfExtractor(),
            '.jpg': ImageExtractor(), '.jpeg': ImageExtractor(),
            '.png': ImageExtractor(), '.bmp': ImageExtractor(),
            '.tiff': ImageExtractor(),
        }

        def process(path):
            ext = os.path.splitext(path)[1].lower()
            extractor = extractors.get(ext)
            if extractor:
                return extractor.extract(path)
            return Fragment(
                file_path=path,
                original_number='',
                assigned_number='',
                status=FragmentStatus.ERROR,
                confidence=0,
                error_message=f'Неподдерживаемый формат: {ext}',
            )

        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = {pool.submit(process, p): p for p in self._paths}
            for future in as_completed(futures):
                frag = future.result()
                self.fragment_ready.emit(frag)

        self.finished.emit()


class _BuildWorker(QObject):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, fragments, header, output_path, parent=None):
        super().__init__(parent)
        self._fragments = fragments
        self._header = header
        self._output_path = output_path

    def run(self):
        try:
            path = build_protocol(self._fragments, self._header, self._output_path)
            self.finished.emit(path)
        except Exception as e:
            self.error.emit(str(e))


class _HeaderBar(QWidget):
    """Top header with app title and status."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(64)
        self.setObjectName('headerBar')
        apply_header_bar(self)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel('Сборщик протокола')
        style_header_title(title)
        subtitle = QLabel('Сборка итогового DOCX из выписок')
        style_header_subtitle(subtitle)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        text_col.addWidget(title)
        text_col.addWidget(subtitle)
        layout.addLayout(text_col)
        layout.addStretch()

        self._status_dot = QLabel('●')
        self._status_dot.setStyleSheet('font-size: 10px; background: transparent;')
        self._status_text = QLabel('Готов к работе')
        style_header_status(self._status_text)
        layout.addWidget(self._status_dot)
        layout.addWidget(self._status_text)

    def set_status(self, text: str, active: bool = False):
        color = '#D97706' if active else '#059669'
        self._status_dot.setStyleSheet(
            f'color: {color}; font-size: 10px; background: transparent;'
        )
        self._status_text.setText(text)
        style_header_status(self._status_text)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Сборщик протокола')
        self.resize(1180, 740)
        self._fragments = []  # type: list[Fragment]
        self._ext_thread = None  # type: Optional[QThread]
        self._build_thread = None  # type: Optional[QThread]
        self._build()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Header bar
        self._header_bar = _HeaderBar()
        root_layout.addWidget(self._header_bar)

        # Tab container
        tab_container = QWidget()
        tab_container.setStyleSheet('background: #F0F2F8;')
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        tab_layout.addWidget(self.tabs)
        root_layout.addWidget(tab_container)

        # Tab 1: Files
        self.file_widget = FileListWidget()
        self.tabs.addTab(self.file_widget, '  Файлы  ')
        self.file_widget.process_requested.connect(self._start_extraction)
        self.file_widget.files_changed.connect(self._sync_fragments)

        # Tab 2: Header
        self.header_form = HeaderForm()
        self.header_form.btn_autofill.clicked.connect(self._autofill_header)
        self.tabs.addTab(self.header_form, '  Шапка  ')

        # Tab 3: Preview
        self.preview_widget = PreviewWidget()
        self.tabs.addTab(self.preview_widget, '  Предпросмотр  ')

        # Tab 4: Build
        build_tab = self._make_build_tab()
        self.tabs.addTab(build_tab, '  Сборка  ')

        self.setStatusBar(QStatusBar())

    def _make_build_tab(self) -> QWidget:
        outer = QWidget()
        outer.setStyleSheet('background: #F0F2F8;')
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(24, 24, 24, 24)
        outer_layout.setSpacing(16)

        # Instruction card
        info_card = QFrame()
        info_card.setStyleSheet("""
            QFrame {
                background: #EEF2FF;
                border: 1.5px solid #C7D2FE;
                border-radius: 10px;
                padding: 4px;
            }
        """)
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(16, 12, 16, 12)
        info_lbl = QLabel(
            '<b>Как собрать протокол</b><br>'
            '1. Добавьте выписки на вкладке <b>Файлы</b><br>'
            '2. Проверьте шапку на вкладке <b>Шапка</b><br>'
            '3. При необходимости исключите файлы в <b>Предпросмотре</b><br>'
            '4. Нажмите кнопку ниже и выберите путь сохранения'
        )
        info_lbl.setStyleSheet('color: #3730A3; background: transparent; font-size: 13px;')
        info_lbl.setWordWrap(True)
        info_layout.addWidget(info_lbl)
        outer_layout.addWidget(info_card)

        # Build button
        self.btn_build = QPushButton('  Сформировать протокол')
        self.btn_build.setFixedHeight(48)
        apply_primary_button(self.btn_build, ' QPushButton { font-size: 15px; }')
        outer_layout.addWidget(self.btn_build)

        # Progress
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setFixedHeight(8)
        outer_layout.addWidget(self.progress)

        # History of generated protocols
        self.build_history = BuildHistoryWidget()
        outer_layout.addWidget(self.build_history, stretch=1)

        self.btn_build.clicked.connect(self._start_build)
        return outer

    # ── extraction ─────────────────────────────────────────────────────────
    def _start_extraction(self, paths: list[str]):
        if self._ext_thread and self._ext_thread.isRunning():
            return

        self._header_bar.set_status(f'Обработка {len(paths)} файл(ов)…', active=True)
        self.statusBar().showMessage(f'Обработка {len(paths)} файл(ов)…')
        worker = _ExtractionWorker(paths)
        thread = QThread(self)
        worker.moveToThread(thread)
        worker.fragment_ready.connect(self._on_fragment)
        worker.finished.connect(thread.quit)
        worker.finished.connect(lambda: self._header_bar.set_status('Готово'))
        worker.finished.connect(lambda: self.statusBar().showMessage('Готово'))
        thread.started.connect(worker.run)
        thread.start()
        self._ext_thread = thread
        self._ext_worker = worker

    def _on_fragment(self, frag: Fragment):
        for i, f in enumerate(self._fragments):
            if f.file_path == frag.file_path:
                self._fragments[i] = frag
                self.file_widget.update_fragment(frag.file_path, frag)
                self.preview_widget.update_fragment(frag)
                return
        self._fragments.append(frag)
        self.file_widget.update_fragment(frag.file_path, frag)
        self.preview_widget.set_fragments(self._fragments)

    def _sync_fragments(self):
        paths = self.file_widget.get_file_paths()
        frag_map = {f.file_path: f for f in self._fragments}
        self._fragments = [frag_map[p] for p in paths if p in frag_map]
        self.preview_widget.set_fragments(self._fragments)

    # ── build ──────────────────────────────────────────────────────────────
    def _start_build(self):
        if not self._fragments:
            QMessageBox.warning(self, 'Нет файлов', 'Добавьте файлы перед сборкой.')
            return

        today = date.today().strftime('%Y-%m-%d')
        default_name = f'Протокол_сформированный_{today}.docx'
        output_path, _ = QFileDialog.getSaveFileName(
            self, 'Сохранить протокол', default_name,
            'Word Document (*.docx)'
        )
        if not output_path:
            return

        header = self.header_form.get_header()

        self.btn_build.setEnabled(False)
        self.build_history.clear_error()
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self._header_bar.set_status('Формирование протокола…', active=True)

        worker = _BuildWorker(list(self._fragments), header, output_path)
        thread = QThread(self)
        worker.moveToThread(thread)
        worker.finished.connect(self._on_build_done)
        worker.error.connect(self._on_build_error)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        thread.started.connect(worker.run)
        thread.start()
        self._build_thread = thread
        self._build_worker = worker

    def _on_build_done(self, path: str):
        self.progress.setVisible(False)
        self.btn_build.setEnabled(True)
        self.build_history.add_entry(path)
        self._header_bar.set_status('Протокол готов')
        self.tabs.setCurrentIndex(3)

    def _on_build_error(self, msg: str):
        self.progress.setVisible(False)
        self.btn_build.setEnabled(True)
        self.build_history.show_error(msg)
        self._header_bar.set_status('Ошибка сборки', active=True)
        QMessageBox.critical(self, 'Ошибка сборки', msg)

    def _autofill_header(self):
        paths = self.file_widget.get_file_paths()
        if paths:
            self.header_form.autofill_from_docx(paths[0])
