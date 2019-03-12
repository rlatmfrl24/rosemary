from PyQt5.QtWidgets import QMessageBox, QDialog, QLabel, QLineEdit, QPushButton, QHBoxLayout, QWidget, QCheckBox, QVBoxLayout, QProgressBar, QGridLayout
from PyQt5.QtGui import QIntValidator
from Model import Logger, Gallery, FirebaseClient


class ManualInputDialog(QDialog):

    # TODO 이 부분은 Private Data로 Crypto 필요

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Manual Input')
        self.setGeometry(100, 100, 400, 200)
        self.le_artist = QLineEdit()
        self.le_code = QLineEdit()
        self.le_type = QLineEdit()
        self.le_title = QLineEdit()
        self.le_group = QLineEdit()
        self.le_original = QLineEdit()
        self.le_path = QLineEdit()
        self.le_keyword = QLineEdit()
        self.le_url = QLineEdit()
        lbl_artist = QLabel('Artist: ')
        lbl_code = QLabel('Code(*): ')
        lbl_type = QLabel('Type: ')
        lbl_title = QLabel('Title(*): ')
        lbl_group = QLabel('Group: ')
        lbl_original = QLabel('Original: ')
        lbl_path = QLabel('Path: ')
        lbl_keyword = QLabel('Keyword: ')
        lbl_url = QLabel('URL(*): ')

        form_layout = QGridLayout()
        form_layout.addWidget(lbl_code, 0, 0)
        form_layout.addWidget(self.le_code, 0, 1)
        form_layout.addWidget(lbl_title, 1, 0)
        form_layout.addWidget(self.le_title, 1, 1)
        form_layout.addWidget(lbl_artist, 2, 0)
        form_layout.addWidget(self.le_artist, 2, 1)
        form_layout.addWidget(lbl_group, 3, 0)
        form_layout.addWidget(self.le_group, 3, 1)
        form_layout.addWidget(lbl_type, 4, 0)
        form_layout.addWidget(self.le_type, 4, 1)
        form_layout.addWidget(lbl_original, 5, 0)
        form_layout.addWidget(self.le_original, 5, 1)
        form_layout.addWidget(lbl_keyword, 6, 0)
        form_layout.addWidget(self.le_keyword, 6, 1)
        form_layout.addWidget(lbl_path, 7, 0)
        form_layout.addWidget(self.le_path, 7, 1)
        form_layout.addWidget(lbl_url, 8, 0)
        form_layout.addWidget(self.le_url, 8, 1)

        lbl_direction = QLabel("Please input form for Manual Data Input to Firebase.")
        btn_submit = QPushButton('Submit')
        btn_cancel = QPushButton('Cancel')
        btn_cancel.clicked.connect(self.close)
        btn_submit.clicked.connect(self.submit)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_submit)
        btn_layout.addWidget(btn_cancel)
        dl_layout = QVBoxLayout()
        dl_layout.addWidget(lbl_direction)
        dl_layout.addLayout(form_layout)
        dl_layout.addLayout(btn_layout)
        self.setLayout(dl_layout)

    def submit(self):
        gallery = Gallery.Gallery()
        gallery.code = self.le_code.text()
        gallery.title = self.le_title.text()
        gallery.artist = self.le_artist.text()
        gallery.type = self.le_type.text()
        gallery.original = self.le_original.text()
        gallery.path = self.le_path.text()
        gallery.url = self.le_url.text()
        gallery.keyword = self.le_keyword.text()
        if gallery.valid_input_error():
            FirebaseClient.fbclient.insert_data(gallery)
            self.close()
        else:
            QMessageBox.warning(self, "Error", "You must enter the fields with an asterisk.")


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
