"""Application-wide QSS stylesheet."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QLabel, QPushButton, QWidget

# Header styles are applied per-widget (not via APP_STYLE) because ID selectors
# in the global sheet override local styles on macOS while backgrounds may not paint.

HEADER_BAR_STYLE = """
QWidget#headerBar {
    background-color: transparent;
    border: none;
}
"""

APP_CHROME_STYLE = """
QWidget#appChrome {
    background-color: #FFFFFF;
    border: none;
}
"""

HEADER_TITLE_STYLE = 'color: #1E1B4B; font-size: 20px; font-weight: 700; background: transparent; letter-spacing: -0.3px;'
HEADER_SUBTITLE_STYLE = 'color: #94A3B8; font-size: 12px; font-weight: 400; background: transparent;'
HEADER_STATUS_STYLE = 'color: #475569; font-size: 12px; font-weight: 500; background: transparent;'

PRIMARY_BUTTON_STYLE = """
QPushButton {
    background-color: #EEF2FF;
    color: #312E81;
    border: 1.5px solid #4F46E5;
    border-radius: 7px;
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #4F46E5;
    color: #FFFFFF;
    border-color: #3730A3;
}
QPushButton:pressed {
    background-color: #3730A3;
    color: #FFFFFF;
}
QPushButton:disabled {
    background-color: #F3F4F6;
    color: #9CA3AF;
    border-color: #E5E7EB;
}
"""

DANGER_BUTTON_STYLE = """
QPushButton {
    background-color: #FFF1F2;
    color: #BE123C;
    border: 1.5px solid #FECDD3;
    border-radius: 7px;
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #FFE4E6;
    border-color: #FDA4AF;
}
QPushButton:pressed {
    background-color: #FECDD3;
}
"""

SECONDARY_BUTTON_STYLE = """
QPushButton {
    background-color: #F9FAFB;
    color: #6B7280;
    border: 1.5px solid #D1D5DB;
    border-radius: 7px;
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #F3F4F6;
    border-color: #9CA3AF;
}
QPushButton:pressed {
    background-color: #E5E7EB;
}
"""

SUCCESS_BUTTON_STYLE = """
QPushButton {
    background-color: #ECFDF5;
    color: #065F46;
    border: 1.5px solid #6EE7B7;
    border-radius: 7px;
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #D1FAE5;
    border-color: #34D399;
    color: #064E3B;
}
QPushButton:pressed {
    background-color: #A7F3D0;
}
"""


def _set_label_color(label: QLabel, css: str, color: str) -> None:
    label.setStyleSheet(css)
    palette = label.palette()
    palette.setColor(label.foregroundRole(), QColor(color))
    label.setPalette(palette)


def apply_plain_label(label: QLabel, css: str, color: str) -> None:
    """Label without macOS focus/frame box around text."""
    label.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
    label.setAutoFillBackground(False)
    label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    _set_label_color(label, css + ' border: none; outline: none; padding: 0; margin: 0;', color)


GHOST_BUTTON_STYLE = """
QPushButton {
    background-color: transparent;
    color: #4F46E5;
    border: none;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #EEF2FF;
}
QPushButton:pressed {
    background-color: #E0E7FF;
}
QPushButton:disabled {
    color: #9CA3AF;
    background: transparent;
}
"""

GHOST_MUTED_BUTTON_STYLE = """
QPushButton {
    background-color: transparent;
    color: #6B7280;
    border: none;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #F3F4F6;
    color: #374151;
}
QPushButton:pressed {
    background-color: #E5E7EB;
}
QPushButton:disabled {
    color: #9CA3AF;
    background: transparent;
}
"""

GHOST_DANGER_BUTTON_STYLE = """
QPushButton {
    background-color: transparent;
    color: #BE123C;
    border: none;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #FFF1F2;
}
QPushButton:pressed {
    background-color: #FFE4E6;
}
QPushButton:disabled {
    color: #9CA3AF;
    background: transparent;
}
"""


def apply_ghost_button(button: QPushButton, variant: str = 'primary') -> None:
    styles = {
        'primary': ('#4F46E5', GHOST_BUTTON_STYLE),
        'muted': ('#6B7280', GHOST_MUTED_BUTTON_STYLE),
        'danger': ('#BE123C', GHOST_DANGER_BUTTON_STYLE),
    }
    color, css = styles[variant]
    button.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    button.setAutoFillBackground(False)
    button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    button.setFlat(True)
    palette = button.palette()
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(color))
    button.setPalette(palette)
    button.setStyleSheet(css)


def apply_header_bar(widget: QWidget) -> None:
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    widget.setAutoFillBackground(False)
    widget.setStyleSheet(HEADER_BAR_STYLE)


def apply_app_chrome(widget: QWidget) -> None:
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    widget.setAutoFillBackground(True)
    palette = widget.palette()
    palette.setColor(widget.backgroundRole(), QColor('#FFFFFF'))
    widget.setPalette(palette)
    widget.setStyleSheet(APP_CHROME_STYLE)


def style_header_title(label: QLabel) -> None:
    _set_label_color(label, HEADER_TITLE_STYLE, '#1E1B4B')


def style_header_subtitle(label: QLabel) -> None:
    _set_label_color(label, HEADER_SUBTITLE_STYLE, '#6B7280')


def style_header_status(label: QLabel) -> None:
    _set_label_color(label, HEADER_STATUS_STYLE, '#374151')


def apply_primary_button(button: QPushButton, extra: str = '') -> None:
    button.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    button.setAutoFillBackground(True)
    palette = button.palette()
    palette.setColor(QPalette.ColorRole.Button, QColor('#EEF2FF'))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor('#312E81'))
    button.setPalette(palette)
    button.setStyleSheet(PRIMARY_BUTTON_STYLE + extra)


def apply_danger_button(button: QPushButton) -> None:
    button.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    button.setAutoFillBackground(True)
    palette = button.palette()
    palette.setColor(QPalette.ColorRole.Button, QColor('#FFF1F2'))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor('#BE123C'))
    button.setPalette(palette)
    button.setStyleSheet(DANGER_BUTTON_STYLE)


def apply_secondary_button(button: QPushButton) -> None:
    button.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    button.setAutoFillBackground(True)
    palette = button.palette()
    palette.setColor(QPalette.ColorRole.Button, QColor('#F9FAFB'))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor('#6B7280'))
    button.setPalette(palette)
    button.setStyleSheet(SECONDARY_BUTTON_STYLE)


def apply_success_button(button: QPushButton) -> None:
    button.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    button.setAutoFillBackground(True)
    palette = button.palette()
    palette.setColor(QPalette.ColorRole.Button, QColor('#ECFDF5'))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor('#065F46'))
    button.setPalette(palette)
    button.setStyleSheet(SUCCESS_BUTTON_STYLE)


APP_TABS_STYLE = """
QTabWidget#appTabs {
    background-color: #FFFFFF;
}
QTabWidget#appTabs::pane {
    border: none;
    background-color: #F0F2F8;
    top: 0px;
}
QTabWidget#appTabs QTabBar {
    background: #FFFFFF;
    border: none;
    border-bottom: 1px solid #E8EBF0;
}
QTabWidget#appTabs QTabBar::tab {
    background: transparent;
    color: #64748B;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 11px 8px 9px 8px;
    margin: 0;
    border-radius: 0;
    font-weight: 500;
    font-size: 13px;
}
QTabWidget#appTabs QTabBar::tab:hover:!selected {
    background: #F8F9FF;
    color: #374151;
}
QTabWidget#appTabs QTabBar::tab:selected {
    background: transparent;
    color: #4F46E5;
    border-bottom: 2px solid #4F46E5;
    font-weight: 600;
}
"""


def apply_app_tabs(widget: QWidget) -> None:
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    widget.setAutoFillBackground(True)
    palette = widget.palette()
    palette.setColor(widget.backgroundRole(), QColor('#FFFFFF'))
    widget.setPalette(palette)
    widget.setStyleSheet(APP_TABS_STYLE)


APP_STYLE = """
/* ═══════════════════════════════════════════════════════
   Base
═══════════════════════════════════════════════════════ */
QMainWindow {
    background-color: #F0F2F8;
}

QWidget {
    color: #1E1B4B;
    font-family: "SF Pro Display", "Helvetica Neue", "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

/* ═══════════════════════════════════════════════════════
   Buttons
═══════════════════════════════════════════════════════ */
QPushButton {
    background-color: #FFFFFF;
    color: #374151;
    border: 1.5px solid #D1D5DB;
    border-radius: 7px;
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 500;
    outline: none;
}
QPushButton:hover {
    background-color: #F3F4F6;
    border-color: #9CA3AF;
}
QPushButton:pressed {
    background-color: #E5E7EB;
}
QPushButton:disabled {
    background-color: #F9FAFB;
    color: #9CA3AF;
    border-color: #E5E7EB;
}

QPushButton#small {
    padding: 5px 12px;
    font-size: 12px;
    border-radius: 6px;
}

/* ═══════════════════════════════════════════════════════
   Input fields
═══════════════════════════════════════════════════════ */
QLineEdit, QTextEdit {
    background: #FFFFFF;
    color: #1E1B4B;
    border: 1.5px solid #D1D5DB;
    border-radius: 7px;
    padding: 6px 10px;
    selection-background-color: #C7D2FE;
    selection-color: #1E1B4B;
}
QLineEdit:focus, QTextEdit:focus {
    border-color: #6366F1;
    background: #FAFAFA;
}
QLineEdit:disabled, QTextEdit:disabled {
    background: #F9FAFB;
    color: #9CA3AF;
}

/* ═══════════════════════════════════════════════════════
   Table
═══════════════════════════════════════════════════════ */
QTableWidget {
    background: #FFFFFF;
    alternate-background-color: #F8F9FF;
    gridline-color: #E5E7EB;
    border: 1.5px solid #E5E7EB;
    border-radius: 8px;
    outline: none;
    font-size: 13px;
}
QTableWidget::item {
    padding: 6px 8px;
    border: none;
}
QTableWidget::item:selected {
    background: #EEF2FF;
    color: #1E1B4B;
}
QHeaderView::section {
    background-color: #EEF2FF;
    color: #4B5563;
    border: none;
    border-bottom: 2px solid #E0E4F0;
    border-right: 1px solid #E5E7EB;
    padding: 8px 10px;
    font-weight: 600;
    font-size: 12px;
}
QHeaderView::section:last {
    border-right: none;
}

/* ═══════════════════════════════════════════════════════
   List widget
═══════════════════════════════════════════════════════ */
QListWidget {
    background: #FFFFFF;
    border: 1.5px solid #E5E7EB;
    border-radius: 8px;
    outline: none;
    padding: 4px;
}
QListWidget::item {
    padding: 8px 10px;
    border-radius: 6px;
    margin: 1px 0;
    color: #1E1B4B;
}
QListWidget::item:hover {
    background: #EEF2FF;
}
QListWidget::item:selected {
    background: #C7D2FE;
    color: #1E1B4B;
}

/* ═══════════════════════════════════════════════════════
   Scroll bars
═══════════════════════════════════════════════════════ */
QScrollBar:vertical {
    background: #F1F5F9;
    width: 8px;
    border-radius: 4px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #CBD5E1;
    border-radius: 4px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #94A3B8;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #F1F5F9;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #CBD5E1;
    border-radius: 4px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover {
    background: #94A3B8;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ═══════════════════════════════════════════════════════
   Group box
═══════════════════════════════════════════════════════ */
QGroupBox {
    background: #FFFFFF;
    border: 1.5px solid #E5E7EB;
    border-radius: 10px;
    margin-top: 14px;
    padding: 12px 16px 16px 16px;
    font-weight: 600;
    font-size: 13px;
    color: #374151;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    top: -1px;
    padding: 0 6px;
    background: #FFFFFF;
    color: #4F46E5;
}

/* ═══════════════════════════════════════════════════════
   Progress bar
═══════════════════════════════════════════════════════ */
QProgressBar {
    background: #E0E4F0;
    border: none;
    border-radius: 5px;
    height: 8px;
    text-align: center;
    font-size: 11px;
    color: transparent;
}
QProgressBar::chunk {
    background-color: #4F46E5;
    border-radius: 5px;
}

/* ═══════════════════════════════════════════════════════
   Splitter
═══════════════════════════════════════════════════════ */
QSplitter::handle {
    background: #E5E7EB;
    width: 2px;
    height: 2px;
}
QSplitter::handle:hover {
    background: #6366F1;
}

/* ═══════════════════════════════════════════════════════
   Message boxes
═══════════════════════════════════════════════════════ */
QMessageBox {
    background: #FFFFFF;
}
QMessageBox QPushButton {
    min-width: 80px;
}

/* ═══════════════════════════════════════════════════════
   Tooltip
═══════════════════════════════════════════════════════ */
QToolTip {
    background: #1E1B4B;
    color: #FFFFFF;
    border: none;
    padding: 5px 10px;
    border-radius: 5px;
    font-size: 12px;
}

/* ═══════════════════════════════════════════════════════
   File dialog
═══════════════════════════════════════════════════════ */
QFileDialog QListView, QFileDialog QTreeView {
    background: #FFFFFF;
}
"""

# Status badge colors (background, text, border)
STATUS_PALETTE = {
    'success':  ('#ECFDF5', '#065F46', '#6EE7B7'),
    'review':   ('#FFFBEB', '#92400E', '#FCD34D'),
    'error':    ('#FFF1F2', '#9F1239', '#FCA5A5'),
    'pending':  ('#F8F9FF', '#4B5563', '#CBD5E1'),
}
