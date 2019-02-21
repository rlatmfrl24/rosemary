from PyQt5.QtWidgets import QMessageBox, QDialog, QLabel, QLineEdit, QPushButton, QHBoxLayout, QWidget, QCheckBox, QVBoxLayout, QProgressBar
from PyQt5.QtGui import QIntValidator
from Model import Logger


class ErrorDialog(QMessageBox):
    def __init__(self):
        super().__init__()

    def open_dialog(self, title, content):
        self.critical(self, title, content)


class RollOptionDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.roll_cnt = None
        self.is_reload = None

    def init_ui(self):
        self.setWindowTitle('Roll Option')
        lbl_roll_cnt = QLabel()
        lbl_roll_cnt.setText('Roll Count: ')
        self.input_roll_cnt = QLineEdit()
        self.input_roll_cnt.setValidator(QIntValidator())
        input_layout = QHBoxLayout()
        btn_roll = QPushButton()
        btn_roll.setText("Roll")
        btn_roll.clicked.connect(self.set_roll_cnt)
        input_layout.addWidget(lbl_roll_cnt)
        input_layout.addWidget(self.input_roll_cnt)
        input_layout.addWidget(btn_roll)
        input_container = QWidget()
        input_container.setLayout(input_layout)

        self.checkbox_loading = QCheckBox()
        self.checkbox_loading.setText("Reload Item List")
        option_layout = QVBoxLayout()
        option_layout.addWidget(self.checkbox_loading)
        option_container = QWidget()
        option_container.setLayout(option_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(input_container)
        main_layout.addWidget(option_container)
        self.setLayout(main_layout)

    def set_roll_cnt(self):
        try:
            self.roll_cnt = int(self.input_roll_cnt.text())
            self.is_reload = self.checkbox_loading.isChecked()
            self.hide()
        except:
            Logger.LOGGER.error('None input error')


class ProgressBar(QDialog):
    def __init__(self, thread, parent=None):
        super(ProgressBar, self).__init__(parent)
        self.setGeometry(200, 200, 400, 80)
        self.setFixedWidth(400)
        layout = QVBoxLayout(self)
        self.setWindowTitle("Loading")

        self.lbl_progress = QLabel()
        self.lbl_progress.setText('')

        self.progressBar = QProgressBar(self)
        self.progressBar.setRange(0, 100)
        layout.addWidget(self.lbl_progress)
        layout.addWidget(self.progressBar)

        self.myLongTask = thread
        self.myLongTask.notifyProgress.connect(self.on_progress)
        self.myLongTask.current_state.connect(self.set_progress_text)
        self.myLongTask.finished.connect(self.close)
        self.myLongTask.start()

    def on_progress(self, i):
        self.progressBar.setValue(i)

    def set_progress_text(self, text):
        self.lbl_progress.setText(text)

    def closeEvent(self, event):
        if self.myLongTask.isRunning():
            self.myLongTask.terminate()
            Logger.LOGGER.warning('[SYSTEM]: (ProgressBar) Thread Process will terminate shortly..')
