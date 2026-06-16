"""First-run install prompt for the portable Windows .exe."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
)
from pathlib import Path

from ..utils.windows_installer import (
    install_application,
    is_running_from_install_dir,
    install_dir as default_install_dir,
    is_windows_frozen,
    output_dir as default_output_dir,
    set_install_dir,
    set_install_prompt_skipped,
    set_output_dir,
    launch_installed_copy,
    should_offer_install,
)


class InstallPromptDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Установка')
        self.setModal(True)
        self.setMinimumWidth(460)

        title = QLabel('Установить «Сборщик протокола» на этот компьютер?')
        title.setWordWrap(True)
        title.setStyleSheet('font-size: 15px; font-weight: 600; color: #1E1B4B;')

        body = QLabel(
            'Программа будет скопирована в папку пользователя, '
            'можно создать ярлык на рабочем столе.\n\n'
            'После установки запускайте приложение с ярлыка — '
            'не нужно каждый раз открывать файл из «Загрузок».'
        )
        body.setWordWrap(True)
        body.setStyleSheet('font-size: 13px; color: #4B5563;')

        self.chk_desktop = QCheckBox('Создать ярлык на рабочем столе')
        self.chk_desktop.setChecked(True)
        self.chk_skip = QCheckBox('Больше не спрашивать')
        self.chk_skip.setChecked(False)

        self.edit_install_dir = QLineEdit(str(default_install_dir()))
        self.edit_install_dir.setMinimumWidth(260)
        choose_install_btn = QPushButton('Выбрать…')

        self.edit_output_dir = QLineEdit(str(default_output_dir()))
        self.edit_output_dir.setMinimumWidth(260)
        choose_output_btn = QPushButton('Выбрать…')

        choose_install_btn.clicked.connect(
            lambda: self._choose_dir(
                'Выберите папку для установки программы',
                self.edit_install_dir,
            )
        )
        choose_output_btn.clicked.connect(
            lambda: self._choose_dir(
                'Выберите папку для сохранения документов',
                self.edit_output_dir,
            )
        )

        install_row = QHBoxLayout()
        install_row.addWidget(QLabel('Папка установки:'))
        install_row.addWidget(self.edit_install_dir, 1)
        install_row.addWidget(choose_install_btn)

        output_row = QHBoxLayout()
        output_row.addWidget(QLabel('Папка для документов:'))
        output_row.addWidget(self.edit_output_dir, 1)
        output_row.addWidget(choose_output_btn)

        buttons = QDialogButtonBox()
        self.btn_install = buttons.addButton('Установить', QDialogButtonBox.ButtonRole.AcceptRole)
        self.btn_skip = buttons.addButton(
            'Запустить без установки',
            QDialogButtonBox.ButtonRole.RejectRole,
        )
        self.btn_install.setDefault(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(12)
        layout.addWidget(title)
        layout.addWidget(body)
        layout.addWidget(self.chk_desktop)
        layout.addWidget(self.chk_skip)
        layout.addLayout(install_row)
        layout.addLayout(output_row)
        layout.addSpacing(8)
        layout.addWidget(buttons)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

    def wants_desktop_shortcut(self) -> bool:
        return self.chk_desktop.isChecked()

    def wants_skip_future_prompts(self) -> bool:
        return self.chk_skip.isChecked()

    def selected_install_dir(self) -> Path:
        return Path(self.edit_install_dir.text().strip())

    def selected_output_dir(self) -> Path:
        return Path(self.edit_output_dir.text().strip())

    def _choose_dir(self, title: str, target_edit: QLineEdit) -> None:
        start = target_edit.text().strip() or '.'
        chosen = QFileDialog.getExistingDirectory(self, title, start)
        if chosen:
            target_edit.setText(chosen)


def maybe_offer_install(app: QApplication) -> bool:
    """Return True if the current process should exit (installed copy launched)."""
    if not is_windows_frozen() or is_running_from_install_dir():
        return False

    if not should_offer_install(prompt_skipped=None):
        return False

    dialog = InstallPromptDialog(parent=app.activeWindow())
    if dialog.exec() != QDialog.DialogCode.Accepted:
        # Запомним выбор папок даже если пользователь не устанавливает программу
        set_install_dir(dialog.selected_install_dir())
        set_output_dir(dialog.selected_output_dir())
        if dialog.wants_skip_future_prompts():
            set_install_prompt_skipped(True)
        return False

    target = install_application(
        desktop_shortcut=dialog.wants_desktop_shortcut(),
        start_menu_shortcut=True,
        custom_install_dir=dialog.selected_install_dir(),
        default_output_dir=dialog.selected_output_dir(),
    )
    set_install_prompt_skipped(False)
    launch_installed_copy(target)
    return True
