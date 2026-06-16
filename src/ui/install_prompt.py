"""First-run install prompt for the Windows .exe."""

from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
)

from ..utils.windows_installer import (
    SETTINGS_APP,
    SETTINGS_ORG,
    install_application,
    is_running_from_install_dir,
    is_windows_frozen,
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
        layout.addSpacing(8)
        layout.addWidget(buttons)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

    def wants_desktop_shortcut(self) -> bool:
        return self.chk_desktop.isChecked()

    def wants_skip_future_prompts(self) -> bool:
        return self.chk_skip.isChecked()


def _settings() -> QSettings:
    return QSettings(SETTINGS_ORG, SETTINGS_APP)


def maybe_offer_install(app: QApplication) -> bool:
    """Return True if the current process should exit (installed copy launched)."""
    if not is_windows_frozen() or is_running_from_install_dir():
        return False

    settings = _settings()
    if not should_offer_install(prompt_skipped=bool(settings.value('install_prompt_skipped', False))):
        return False

    dialog = InstallPromptDialog(parent=app.activeWindow())
    if dialog.exec() != QDialog.DialogCode.Accepted:
        if dialog.wants_skip_future_prompts():
            settings.setValue('install_prompt_skipped', True)
        return False

    target = install_application(
        desktop_shortcut=dialog.wants_desktop_shortcut(),
        start_menu_shortcut=True,
    )
    settings.setValue('install_prompt_skipped', False)
    launch_installed_copy(target)
    return True
