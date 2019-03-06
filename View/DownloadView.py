from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, pyqtSignal, QSettings
from PyQt5.QtGui import QIntValidator
from Model import HiyobiController, HitomiController, Logger
from View import Dialog, Settings
import traceback

TARGET_CRAWL_PAGE = 0
download_list = []


class LoadDownloadData(QThread):
    notifyProgress = pyqtSignal(int)
    current_state = pyqtSignal(str)

    def run(self):
        settings = QSettings()
        global pref_download_site
        pref_download_site = settings.value(Settings.SETTINGS_TARGET_SITE, Settings.SITE.Hiyobi, type=Settings.SITE)
        global download_list
        if pref_download_site is Settings.SITE.Hiyobi:
            download_list = HiyobiController.get_download_list(TARGET_CRAWL_PAGE, self)
        elif pref_download_site is Settings.SITE.Hitomi:
            download_list = HitomiController.get_download_list(TARGET_CRAWL_PAGE, self)


class DownloaderDialog(QDialog):

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.index = -1

    def closeEvent(self, event):
        try:
            if self.thread is not None and self.thread.isRunning():
                btn_reply = QMessageBox.question(self, 'Download is Progressing!',
                                                 'Download Process is running.'
                                                 '\nIf you close this dialog, '
                                                 'download thread still running until last download finished.'
                                                 '\nAre you sure close this dialog?',
                                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if btn_reply == QMessageBox.Yes:
                    Logger.LOGGER.warning('(DownloadDialog) Thread Process will close shortly..')
                    self.thread.terminate()
                    event.accept()
                else:
                    event.ignore()
        except AttributeError:
            Logger.LOGGER.warning('(DownloadDialog) No running thread, close dialog')
        except:
            Logger.LOGGER.error(traceback.format_exc())
            pass

    def init_ui(self):
        self.setGeometry(150, 150, 1000, 200)
        self.setWindowTitle('Manga Downloader')
        layout = QVBoxLayout()
        lbl_crawl_pages = QLabel()
        lbl_crawl_pages.setText("Pages:")
        self.input_crawl_pages = QLineEdit()
        self.input_crawl_pages.setValidator(QIntValidator())
        self.btn_find = QPushButton()
        self.btn_find.setText("Find")
        self.btn_find.clicked.connect(self.load_table_data)

        self.btn_download = QPushButton()
        self.btn_download.setText("Download")
        self.btn_download.clicked.connect(self.download_all)

        layout_operator = QHBoxLayout()
        layout_operator.addWidget(lbl_crawl_pages)
        layout_operator.addWidget(self.input_crawl_pages)
        layout_operator.addWidget(self.btn_find)
        layout_operator.addWidget(self.btn_download)
        self.download_table = QTableWidget()
        self.download_table.setColumnCount(3)
        self.download_table.setHorizontalHeaderLabels(["Code", "Title", "Progress", "Desc"])
        self.download_table.setSelectionBehavior(QTableWidget.SelectRows)

        table_header = self.download_table.horizontalHeader()
        table_header.setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addLayout(layout_operator)
        layout.addWidget(self.download_table)
        self.setLayout(layout)

    def load_table_data(self):
        if self.input_crawl_pages.text() != "":
            self.index = -1
            while self.download_table.rowCount() > 0:
                self.download_table.removeRow(0)
            global TARGET_CRAWL_PAGE
            TARGET_CRAWL_PAGE = int(self.input_crawl_pages.text())
            dlg = Dialog.ProgressBar(LoadDownloadData())
            dlg.exec_()
            for item in download_list:
                self.index = self.index + 1
                self.download_table.insertRow(self.index)
                self.download_table.setItem(self.index, 0, QTableWidgetItem(item.code))
                self.download_table.setItem(self.index, 1, QTableWidgetItem(item.title))
                self.download_table.setItem(self.index, 2, QTableWidgetItem("Ready.."))

    def download_all(self):
        self.btn_download.setEnabled(False)
        self.btn_find.setEnabled(False)
        if pref_download_site is Settings.SITE.Hiyobi:
            self.thread = HiyobiController.DownloadByTable(download_list, self)
        elif pref_download_site is Settings.SITE.Hitomi:
            self.thread = HitomiController.DownloadByTable(download_list, self)
        self.thread.item_index.connect(self.set_index)
        self.thread.current_state.connect(self.on_progress)
        self.thread.thread_finished.connect(self.thread_finished)
        self.thread.start()

    def test_download(self):
        test_list = []
        test_list.append(download_list[0])
        if pref_download_site is Settings.SITE.Hiyobi:
            self.thread = HiyobiController.DownloadByTable(test_list, self)
        elif pref_download_site is Settings.SITE.Hitomi:
            self.thread = HitomiController.DownloadByTable(test_list, self)
        self.thread.item_index.connect(self.set_index)
        self.thread.current_state.connect(self.on_progress)
        self.thread.thread_finished.connect(self.thread_finished)
        self.thread.start()

    def set_index(self, i):
        self.index = i
        self.download_table.selectRow(i)

    def on_progress(self, str):
        item = self.download_table.item(self.index, 2)
        item.setText(str)

    def thread_finished(self, isFinished):
        self.btn_find.setEnabled(isFinished)
        self.btn_download.setEnabled(isFinished)
        print('\a')
        QMessageBox.information(self, "Hiyobi Downloader", "Download Complete!", QMessageBox.Ok)

