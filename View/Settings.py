from PyQt5.QtWidgets import *
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QIntValidator
from PyQt5.QtCore import QSettings, Qt, QModelIndex, pyqtSlot
import os
from Model import Logger

SETTINGS_DEFAULT_ROLL_COUNT = 'settings/roll/cnt'
SETTINGS_TOGGLE_RELOAD = 'settings/roll/reload'
SETTINGS_TOGGLE_SHUFFLE = 'settings/roll/shuffle'
SETTINGS_VIEWER_PATH = 'settings/general/viewer'
SETTINGS_TARGET_PATH = 'settings/general/target'
SETTINGS_SAVE_PATH = 'settings/download/save'
SETTINGS_TOGGLE_PREVIEW = 'settings/general/preview'
SETTINGS_MAX_POOL_CNT = 'settings/download/pool'
HONEYVIEW_PATH = os.environ['ProgramW6432'] + '\\Honeyview\\Honeyview.exe'
DEFAULT_TARGET_PATH = 'D:/hiyobi/new/'
DEFAULT_MAX_POOL = 8


class StWidgetForm(QGroupBox):
    def __init__(self):
        QGroupBox.__init__(self)
        self.box = QBoxLayout(QBoxLayout.TopToBottom)
        self.box.setAlignment(Qt.AlignTop)
        self.setLayout(self.box)


class DownloadSetting(StWidgetForm):
    def __init__(self):
        super(DownloadSetting, self).__init__()
        settings = QSettings()
        pref_save_path = settings.value(SETTINGS_SAVE_PATH, DEFAULT_TARGET_PATH, type=str)
        pref_max_pool_cnt = settings.value(SETTINGS_MAX_POOL_CNT, DEFAULT_MAX_POOL, type=int)

        self.setTitle('Download Settings')
        lbl_save_path = QLabel()
        lbl_save_path.setText('Download Path:')
        lbl_max_pool_cnt = QLabel()
        lbl_max_pool_cnt.setText('Max Download Pool:')

        self.input_save_path = QLineEdit()
        self.input_save_path.setReadOnly(True)
        self.input_save_path.setText(pref_save_path)
        self.input_max_pool_cnt = QLineEdit()
        self.input_max_pool_cnt.setValidator(QIntValidator())
        self.input_max_pool_cnt.setText(str(pref_max_pool_cnt))

        btn_configure_save_path = QPushButton()
        btn_configure_save_path.setText('Set path..')
        btn_configure_save_path.clicked.connect(self.change_save_path)

        layout_save_path = QHBoxLayout()
        layout_save_path.addWidget(lbl_save_path)
        layout_save_path.addWidget(self.input_save_path)
        layout_save_path.addWidget(btn_configure_save_path)

        layout_max_pool_cnt = QHBoxLayout()
        layout_max_pool_cnt.addWidget(lbl_max_pool_cnt)
        layout_max_pool_cnt.addWidget(self.input_max_pool_cnt)

        self.box.addLayout(layout_save_path)
        self.box.addLayout(layout_max_pool_cnt)

    def save_download_settings(self):
        settings = QSettings()
        settings.setValue(SETTINGS_SAVE_PATH, self.input_save_path.text())
        settings.setValue(SETTINGS_MAX_POOL_CNT, self.input_max_pool_cnt.text())
        settings.sync()

    def change_save_path(self):
        path = str(QFileDialog.getExistingDirectory(self, "Select Directory", self.input_save_path.text()))
        if path is not "":
            self.input_save_path.setText(path)


class GeneralSetting(StWidgetForm):
    def __init__(self):
        super(GeneralSetting, self).__init__()
        settings = QSettings()
        pref_viewer_path = settings.value(SETTINGS_VIEWER_PATH, HONEYVIEW_PATH, type=str)

        self.setTitle("General Settings")

        lbl_viewer_path = QLabel()
        lbl_viewer_path.setText("Viewer Path:")

        self.input_viewer_path = QLineEdit()
        self.input_viewer_path.setReadOnly(True)
        self.input_viewer_path.setText(pref_viewer_path)

        btn_configure_viewer = QPushButton()
        btn_configure_viewer.setText("Set path..")
        btn_configure_viewer.clicked.connect(self.change_viewer_path)

        btn_set_default_viewer = QPushButton()
        btn_set_default_viewer.setText("Set Default")
        btn_set_default_viewer.clicked.connect(self.set_default_viewer_path)

        set_btn_viewer = QHBoxLayout()
        set_btn_viewer.addWidget(btn_configure_viewer)
        set_btn_viewer.addWidget(btn_set_default_viewer)

        self.chkbox_toggle_preivew = QCheckBox()
        self.chkbox_toggle_preivew.setText("Show Preview on Table")
        self.chkbox_toggle_preivew.setChecked(settings.value(SETTINGS_TOGGLE_PREVIEW, False, type=bool))

        self.box.addWidget(lbl_viewer_path)
        self.box.addWidget(self.input_viewer_path)
        self.box.addLayout(set_btn_viewer)
        self.box.addWidget(self.chkbox_toggle_preivew)

    def save_general_settings(self):
        settings = QSettings()
        settings.setValue(SETTINGS_VIEWER_PATH, self.input_viewer_path.text())
        settings.setValue(SETTINGS_TOGGLE_PREVIEW, self.chkbox_toggle_preivew.isChecked())
        settings.sync()

    def set_default_viewer_path(self):
        self.input_viewer_path.setText(HONEYVIEW_PATH)

    def change_viewer_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Directory")
        if path is not "":
            self.input_viewer_path.setText(path)


class RollSetting(StWidgetForm):
    def __init__(self):
        super(RollSetting, self).__init__()
        settings = QSettings()
        pref_toggle_reload = settings.value(SETTINGS_TOGGLE_RELOAD, False, type=bool)
        pref_toggle_shuffle = settings.value(SETTINGS_TOGGLE_SHUFFLE, True, type=bool)
        pref_default_roll_cnt = settings.value(SETTINGS_DEFAULT_ROLL_COUNT, 5, type=int)

        self.setTitle("Roll Settings")
        lbl_default_roll_cnt = QLabel()
        lbl_default_roll_cnt.setText("Default Roll Count: ")
        self.input_default_roll_cnt = QLineEdit()
        self.input_default_roll_cnt.setText(str(pref_default_roll_cnt))

        self.chkbox_default_toggle_load = QCheckBox()
        self.chkbox_default_toggle_load.setText("Reload Items on Instant Roll")
        self.chkbox_default_toggle_load.setChecked(pref_toggle_reload)

        self.chkbox_default_toggle_shuffle = QCheckBox()
        self.chkbox_default_toggle_shuffle.setText("Shuffle Items on Instant Roll")
        self.chkbox_default_toggle_shuffle.setChecked(pref_toggle_shuffle)

        set_default_roll_cnt = QHBoxLayout()
        set_default_roll_cnt.addWidget(lbl_default_roll_cnt)
        set_default_roll_cnt.addWidget(self.input_default_roll_cnt)

        self.box.addLayout(set_default_roll_cnt)
        self.box.addWidget(self.chkbox_default_toggle_load)
        self.box.addWidget(self.chkbox_default_toggle_shuffle)

    def save_roll_settings(self):
        settings = QSettings()
        settings.setValue(SETTINGS_TOGGLE_RELOAD, self.chkbox_default_toggle_load.isChecked())
        settings.setValue(SETTINGS_TOGGLE_SHUFFLE, self.chkbox_default_toggle_shuffle.isChecked())
        settings.setValue(SETTINGS_DEFAULT_ROLL_COUNT, self.input_default_roll_cnt.text())
        settings.sync()


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.stk_w = QStackedWidget(self)
        self.settings_general = GeneralSetting()
        self.settings_roll = RollSetting()
        self.settings_download = DownloadSetting()
        self.init_widget()

    def init_widget(self):
        self.setWindowTitle("Settings")
        self.setMinimumWidth(600)
        widget_layout = QBoxLayout(QBoxLayout.LeftToRight)

        btn_apply = QPushButton()
        btn_apply.setText('Apply')
        btn_apply.clicked.connect(self.save_settings)

        btn_apply_close = QPushButton()
        btn_apply_close.setText('Apply && Close')
        btn_apply_close.clicked.connect(self.apply_and_close)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_apply)
        btn_layout.addWidget(btn_apply_close)

        group = QGroupBox()
        box = QBoxLayout(QBoxLayout.TopToBottom)
        group.setLayout(box)
        group.setTitle("Settings")
        group.setFixedWidth(150)
        widget_layout.addWidget(group)

        fruits = ["General", "Roll", "Download"]
        view = QListView(self)
        model = QStandardItemModel()
        for f in fruits:
            model.appendRow(QStandardItem(f))
        view.setModel(model)
        box.addWidget(view)

        self.stk_w.addWidget(self.settings_general)
        self.stk_w.addWidget(self.settings_roll)
        self.stk_w.addWidget(self.settings_download)

        widget_layout.addWidget(self.stk_w)

        layout = QVBoxLayout()
        layout.addLayout(widget_layout)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # 시그널 슬롯 연결
        view.clicked.connect(self.slot_clicked_item)

    def apply_and_close(self):
        self.save_settings()
        self.close()

    def save_settings(self):
        self.settings_general.save_general_settings()
        self.settings_roll.save_roll_settings()
        self.settings_download.save_download_settings()
        Logger.LOGGER.info('[SYSTEM]: Settings Saved..')

    @pyqtSlot(QModelIndex)
    def slot_clicked_item(self, QModelIndex):
        self.stk_w.setCurrentIndex(QModelIndex.row())
