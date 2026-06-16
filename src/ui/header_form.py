from PySide6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QTextEdit, QPushButton,
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
)
from PySide6.QtCore import Signal, Qt

from ..models.protocol_header import ProtocolHeader
from .styles import apply_primary_button


class HeaderForm(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Page header
        page_header = QFrame()
        page_header.setStyleSheet('background: #F8F9FF; border-bottom: 1.5px solid #E5E7EB;')
        ph_layout = QVBoxLayout(page_header)
        ph_layout.setContentsMargins(24, 16, 24, 16)
        ph_title = QLabel('Шапка протокола')
        ph_title.setStyleSheet('font-size: 16px; font-weight: 700; color: #1E1B4B; background: transparent;')
        ph_desc = QLabel('Данные будут вставлены в начало итогового документа')
        ph_desc.setStyleSheet('font-size: 12px; color: #6B7280; background: transparent;')
        ph_layout.addWidget(ph_title)
        ph_layout.addWidget(ph_desc)
        outer.addWidget(page_header)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet('background: #F0F2F8;')

        content = QWidget()
        content.setStyleSheet('background: #F0F2F8;')
        cv = QVBoxLayout(content)
        cv.setContentsMargins(24, 20, 24, 20)
        cv.setSpacing(16)

        # Card
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1.5px solid #E5E7EB;
                border-radius: 12px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 20, 24, 24)
        card_layout.setSpacing(0)

        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setVerticalSpacing(12)
        form.setHorizontalSpacing(16)
        form.setContentsMargins(0, 0, 0, 0)

        label_style = 'color: #374151; font-size: 13px; font-weight: 500; background: transparent;'

        def _lbl(text):
            l = QLabel(text)
            l.setStyleSheet(label_style)
            return l

        self.f_number = QLineEdit()
        self.f_number.setPlaceholderText('Например: 12')
        self.f_date = QLineEdit()
        self.f_date.setPlaceholderText('Например: 15.06.2026')
        self.f_session = QLineEdit()
        self.f_session.setPlaceholderText('Заседание Совета директоров')
        self.f_org = QLineEdit()
        self.f_org.setPlaceholderText('Полное наименование организации')
        self.f_participants = QTextEdit()
        self.f_participants.setFixedHeight(90)
        self.f_participants.setPlaceholderText('Иванов И.И.\nПетров П.П.')
        self.f_secretary = QLineEdit()
        self.f_secretary.setPlaceholderText('Фамилия И.О.')
        self.f_quorum = QTextEdit()
        self.f_quorum.setFixedHeight(70)
        self.f_quorum.setPlaceholderText('На заседании присутствуют…')
        self.f_agenda = QTextEdit()
        self.f_agenda.setFixedHeight(70)
        self.f_agenda.setPlaceholderText('Повестка дня…')

        form.addRow(_lbl('Номер протокола:'), self.f_number)
        form.addRow(_lbl('Дата протокола:'), self.f_date)
        form.addRow(_lbl('Название заседания:'), self.f_session)
        form.addRow(_lbl('Организация:'), self.f_org)
        form.addRow(_lbl('Участники:'), self.f_participants)
        form.addRow(_lbl('Секретарь:'), self.f_secretary)
        form.addRow(_lbl('Текст о кворуме:'), self.f_quorum)
        form.addRow(_lbl('Вопрос повестки:'), self.f_agenda)

        card_layout.addLayout(form)
        cv.addWidget(card)

        # Action row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.btn_autofill = QPushButton('Заполнить из первого DOCX')
        apply_primary_button(self.btn_autofill)
        self.btn_clear = QPushButton('Очистить форму')
        btn_row.addWidget(self.btn_autofill)
        btn_row.addWidget(self.btn_clear)
        btn_row.addStretch()
        cv.addLayout(btn_row)
        cv.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

        self.btn_clear.clicked.connect(self._clear)
        for widget in (self.f_number, self.f_date, self.f_session,
                       self.f_org, self.f_secretary):
            widget.textChanged.connect(self.changed)
        for widget in (self.f_participants, self.f_quorum, self.f_agenda):
            widget.textChanged.connect(self.changed)

    def _clear(self):
        for w in (self.f_number, self.f_date, self.f_session, self.f_org, self.f_secretary):
            w.clear()
        for w in (self.f_participants, self.f_quorum, self.f_agenda):
            w.clear()

    def get_header(self) -> ProtocolHeader:
        return ProtocolHeader(
            protocol_number=self.f_number.text().strip(),
            protocol_date=self.f_date.text().strip(),
            session_name=self.f_session.text().strip(),
            organization=self.f_org.text().strip(),
            participants=self.f_participants.toPlainText().strip(),
            secretary=self.f_secretary.text().strip(),
            quorum_text=self.f_quorum.toPlainText().strip(),
            agenda_item=self.f_agenda.toPlainText().strip(),
        )

    def set_header(self, header: ProtocolHeader) -> None:
        self.f_number.setText(header.protocol_number)
        self.f_date.setText(header.protocol_date)
        self.f_session.setText(header.session_name)
        self.f_org.setText(header.organization)
        self.f_participants.setPlainText(header.participants)
        self.f_secretary.setText(header.secretary)
        self.f_quorum.setPlainText(header.quorum_text)
        self.f_agenda.setPlainText(header.agenda_item)

    def autofill_from_docx(self, file_path: str):
        """Try to extract header info from a DOCX выписка."""
        try:
            import zipfile
            from lxml import etree
            from ..utils.anchors import W_NS, get_para_text

            with zipfile.ZipFile(file_path, 'r') as z:
                xml_bytes = z.read('word/document.xml')

            root = etree.fromstring(xml_bytes)
            _W = f'{{{W_NS}}}'
            body = root.find(f'.//{_W}body')
            paras = [get_para_text(e) for e in body if e.tag == f'{_W}p']

            for text in paras[:20]:
                if 'Протокол №' in text or 'Протокола №' in text:
                    import re
                    m = re.search(r'№\s*(\S+)', text)
                    if m and not self.f_number.text():
                        self.f_number.setText(m.group(1))
                    m2 = re.search(r'от\s+([\d.]+)', text)
                    if m2 and not self.f_date.text():
                        self.f_date.setText(m2.group(1))
                if 'Ассоциац' in text and not self.f_org.text():
                    self.f_org.setText(text.strip())
        except Exception:
            pass
