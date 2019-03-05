import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QSettings, Qt, QThread, pyqtSignal, QCoreApplication
from PIL import Image
from random import shuffle
from send2trash import send2trash
import shutil
import traceback

from Model import FileUtil, Logger
from View import Dialog, DownloadView, Settings

ORGANIZATION_NAME = 'Herb'
ORGANIZATION_DOMAIN = 'soulkey.com'
APPLICATION_NAME = 'Rosemary'
logger_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
data_list = []


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.statusBar()
        self.mainWidget = MainView(parent=self)
        self.setCentralWidget(self.mainWidget)
        self.setGeometry(100, 100, 1200, 500)
        self.setWindowTitle('Rosemary')

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip('프로그램을 종료합니다.')
        exit_action.triggered.connect(close_application)


        change_targetpath_action = QAction("Change Target Path..", self)
        change_targetpath_action.setShortcut("Ctrl+T")
        change_targetpath_action.setStatusTip("Target Path를 변경합니다.")
        change_targetpath_action.triggered.connect(self.mainWidget.change_targetpath)

        move_new_files_to_precede = QAction("Move Files to precede path..", self)
        move_new_files_to_precede.setShortcut("Ctrl+M")
        move_new_files_to_precede.setStatusTip("다운로드 경로의 신규 파일들을 모두 상위 경로로 이동시킵니다.")
        move_new_files_to_precede.triggered.connect(self.mainWidget.move_files_to_precede_path)

        setting_action = QAction("Settings..", self)
        setting_action.setStatusTip("설정 화면을 엽니다.")
        setting_action.setShortcut('Ctrl+S')
        setting_action.triggered.connect(open_settings)

        open_roll_option_action = QAction('Roll with option..', self)
        open_roll_option_action.setShortcut('Ctrl+R')
        open_roll_option_action.setStatusTip('입력받은 옵션으로 Roll 작업을 수행합니다')
        open_roll_option_action.triggered.connect(self.open_roll_option_dialog)

        instant_roll_action = QAction('Instant Roll', self)
        instant_roll_action.setShortcut('Ctrl+Shift+R')
        instant_roll_action.setStatusTip('기본 설정으로 바로 Roll 작업을 수행합니다')
        instant_roll_action.triggered.connect(self.instant_roll)

        open_downloader_action = QAction("Open Downloader..", self)
        open_downloader_action.setShortcut("Ctrl+D")
        open_downloader_action.setStatusTip("Hiyobi Downloader를 실행합니다.")
        open_downloader_action.triggered.connect(open_downloader)

        manual_input_action = QAction('Manual Input data to Firebase', self)
        manual_input_action.setShortcut("Ctrl+I")
        manual_input_action.setStatusTip('수동으로 Hiyobi 데이터를 Firebase에 입력합니다.')
        manual_input_action.triggered.connect(open_manual_input)

        main_menu = self.menuBar()
        menu_file = main_menu.addMenu('&File')
        menu_file.addAction(change_targetpath_action)
        menu_file.addAction(move_new_files_to_precede)
        menu_file.addAction(setting_action)
        menu_file.addAction(exit_action)
        menu_roll = main_menu.addMenu('&Roll')
        menu_roll.addAction(open_roll_option_action)
        menu_roll.addAction(instant_roll_action)
        menu_download = main_menu.addMenu('&Download')
        menu_download.addAction(open_downloader_action)
        menu_download.addAction(manual_input_action)

    def open_roll_option_dialog(self):
        dlg = Dialog.RollOptionDialog()
        dlg.exec_()
        if dlg.roll_cnt is not None:
            self.mainWidget.max_item_count = dlg.roll_cnt
            self.mainWidget.toggle_loading = dlg.is_reload
            self.mainWidget.toggle_shuffle = True
            self.mainWidget.init_table_data()

    def instant_roll(self):
        settings = QSettings()
        pref_toggle_reload = settings.value(Settings.SETTINGS_TOGGLE_RELOAD, False, type=bool)
        pref_toggle_shuffle = settings.value(Settings.SETTINGS_TOGGLE_SHUFFLE, True, type=bool)
        pref_default_roll_cnt = settings.value(Settings.SETTINGS_DEFAULT_ROLL_COUNT, 5, type=int)
        self.mainWidget.max_item_count = pref_default_roll_cnt
        self.mainWidget.toggle_loading = pref_toggle_reload
        self.mainWidget.toggle_shuffle = pref_toggle_shuffle
        self.mainWidget.init_table_data()


class MainView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.max_item_count = 0
        self.toggle_loading = True
        self.toggle_shuffle = False

    def init_ui(self):
        settings = QSettings()
        pref_target_path = settings.value(Settings.SETTINGS_TARGET_PATH, Settings.DEFAULT_TARGET_PATH, type=str)

        self.TargetPath = QLineEdit()
        self.TargetPath.setText(pref_target_path)
        self.TargetPath.setReadOnly(True)

        btn_change_target = QPushButton()
        btn_change_target.setText("Change")
        btn_change_target.clicked.connect(self.change_targetpath)
        btn_load_target = QPushButton()
        btn_load_target.setText("Load")
        btn_load_target.clicked.connect(self.init_table_data)

        layout_info = QHBoxLayout()
        layout_info.addWidget(self.TargetPath)
        layout_info.addWidget(btn_change_target)
        layout_info.addWidget(btn_load_target)
        gb_info = QGroupBox(self)
        gb_info.setTitle("Target Path")
        gb_info.setLayout(layout_info)

        self.mainTable = QTableWidget()
        self.mainTable.setColumnCount(6)
        self.mainTable.setColumnWidth(1, 128)
        self.mainTable.setColumnWidth(2, 300)
        self.mainTable.setColumnWidth(3, 100)
        self.mainTable.setColumnWidth(4, 80)
        self.mainTable.setColumnWidth(5, 100)
        self.mainTable.setColumnWidth(6, 100)
        self.mainTable.setHorizontalHeaderLabels(["Preview", "Code", "Title", "Kinds", "Size", "Path"])
        table_header = self.mainTable.horizontalHeader()
        table_header.setSectionResizeMode(5, QHeaderView.Stretch)
        # self.init_table_data()
        self.mainTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.mainTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.mainTable.setSelectionBehavior(QTableWidget.SelectRows)
        self.mainTable.doubleClicked.connect(self.table_open_viewer_action)
        self.mainTable.setContextMenuPolicy(Qt.ActionsContextMenu)

        open_viewer_action = QAction("Open with Viewer", self.mainTable)
        open_explorer_action = QAction("View on Explorer", self.mainTable)
        move_file_action = QAction("Move to..", self.mainTable)
        copy_file_action = QAction("Copy to..", self.mainTable)
        remove_item_action = QAction("Remove Item from table", self.mainTable)
        delete_file_action = QAction("Delete File", self.mainTable)
        remove_item_action.setShortcut('Del')
        delete_file_action.setShortcut('Shift+Del')
        open_viewer_action.setShortcuts(['Return', 'Enter'])
        delete_file_action.triggered.connect(self.delete_item)
        remove_item_action.triggered.connect(self.remove_item)
        open_viewer_action.triggered.connect(self.table_open_viewer_action)
        open_explorer_action.triggered.connect(self.table_open_explorer_action)
        move_file_action.triggered.connect(self.move_item)
        copy_file_action.triggered.connect(self.copy_item)
        self.mainTable.addAction(open_viewer_action)
        self.mainTable.addAction(open_explorer_action)
        self.mainTable.addAction(move_file_action)
        self.mainTable.addAction(copy_file_action)
        self.mainTable.addAction(remove_item_action)
        self.mainTable.addAction(delete_file_action)

        layout_main = QVBoxLayout()
        layout_main.addWidget(gb_info)
        layout_main.addWidget(self.mainTable)
        self.setLayout(layout_main)

    def init_table_data(self):
        settings = QSettings()
        pref_toggle_preview = settings.value(Settings.SETTINGS_TOGGLE_PREVIEW, False, type=bool)

        self.mainTable.setSortingEnabled(False)
        index = -1
        while self.mainTable.rowCount() > 0:
            self.mainTable.removeRow(0)
        if self.toggle_loading:
            open_loading_dialog(FileLoadFromTarget())
        if self.toggle_shuffle:
            shuffle(data_list)
        # print(data_list)

        for line_data in data_list:
            index = index + 1
            if self.max_item_count != 0 and index >= self.max_item_count:
                break

            self.mainTable.insertRow(index)
            if pref_toggle_preview:
                try:
                    self.mainTable.setCellWidget(index, 0, ThumbnailWidget(line_data['thumbnail']))
                except AttributeError:
                    Logger.LOGGER.warning("[Error]: Non-Valid Image or ZIP File")
            self.mainTable.setItem(index, 1, QTableWidgetItem(line_data['code']))
            self.mainTable.setItem(index, 2, QTableWidgetItem(line_data['title']))
            self.mainTable.setItem(index, 3, QTableWidgetItem(line_data['kinds']))
            item_size = NumericItem(line_data['size_fmt'])
            item_size.setData(Qt.UserRole, line_data['size'])
            self.mainTable.setItem(index, 4, item_size)
            self.mainTable.setItem(index, 5, QTableWidgetItem(line_data['path']))

        self.mainTable.resizeRowsToContents()
        self.mainTable.resizeColumnToContents(0)
        self.max_item_count = 0
        self.toggle_loading = True
        self.mainTable.setSortingEnabled(True)

    def table_open_viewer_action(self):
        try:
            row_number = self.mainTable.selectionModel().selectedIndexes()[0].row()
            selected_item_path = self.mainTable.item(row_number, 5).text()
            FileUtil.open_viewer(selected_item_path)
        except IndexError:
            print('\a')
            QMessageBox.information(self, "Error",
                                    "Not selected any item.\nPlease Load or Selected any Item",
                                    QMessageBox.Ok)

    def table_open_explorer_action(self):
        try:
            row_number = self.mainTable.selectionModel().selectedIndexes()[0].row()
            selected_item_path = self.mainTable.item(row_number, 5).text()
            FileUtil.open_explorer(selected_item_path)
        except IndexError:
            print('\a')
            QMessageBox.information(self, "Error",
                                    "Not selected any item.\nPlease Load or Selected any Item",
                                    QMessageBox.Ok)

    def change_targetpath(self):
        settings = QSettings()
        file = str(QFileDialog.getExistingDirectory(self, "Select Directory", self.TargetPath.text()))
        if file is not "":
            FileUtil.targetPath = file
            while self.mainTable.rowCount() > 0:
                self.mainTable.removeRow(0)
            self.TargetPath.setText(FileUtil.targetPath)
            settings.setValue(Settings.SETTINGS_TARGET_PATH, self.TargetPath.text())
            Logger.LOGGER.info("Change to target path => " + file)

    def move_files_to_precede_path(self):
        btn_reply = QMessageBox.question(self,
                                         'Move Items', 'Are you sure to Move to Precede Path items in Download Directory?',
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)
        if btn_reply == QMessageBox.Yes:
            open_loading_dialog(MoveFilesToPrecede())

    def remove_item(self):
        try:
            row_number = self.mainTable.selectionModel().selectedIndexes()[0].row()
            self.mainTable.removeRow(row_number)
        except IndexError:
            print('\a')
            QMessageBox.information(self, "Error", "Not selected any item.\nPlease Load or Selected any Item", QMessageBox.Ok)

    def delete_item(self):
        try:
            row_number = self.mainTable.selectionModel().selectedIndexes()[0].row()
            btn_reply = QMessageBox.question(self,
                                             'Delete Item', 'Are you sure to delete this item?',
                                             QMessageBox.Yes | QMessageBox.No,
                                             QMessageBox.No)
            if btn_reply == QMessageBox.Yes:
                selected_item_path = self.mainTable.item(row_number, 5).text()
                send2trash(selected_item_path.replace('/', '\\'))
                self.mainTable.removeRow(row_number)
        except IndexError:
            print('\a')
            QMessageBox.information(self, "Error", "Not selected any item.\nPlease Load or Selected any Item", QMessageBox.Ok)

    def move_item(self):
        try:
            row_number = self.mainTable.selectionModel().selectedIndexes()[0].row()
            selected_item_path = self.mainTable.item(row_number, 5).text()
            file = str(QFileDialog.getExistingDirectory(self, "Select Directory", selected_item_path))
            target_path = file+'/' + selected_item_path[selected_item_path.rfind('/')+1:]
            shutil.move(selected_item_path, target_path)
            self.mainTable.removeRow(row_number)
            print('\a')
            QMessageBox.information(self, "Move",
                                    selected_item_path+"\nis Moved to \n"+target_path,
                                    QMessageBox.Ok)
        except IndexError:
            print('\a')
            QMessageBox.information(self, "Error",
                                    "Not selected any item.\nPlease Load or Selected any Item",
                                    QMessageBox.Ok)

    def copy_item(self):
        try:
            row_number = self.mainTable.selectionModel().selectedIndexes()[0].row()
            selected_item_path = self.mainTable.item(row_number, 5).text()
            file = str(QFileDialog.getExistingDirectory(self, "Select Directory", selected_item_path))
            target_path = file+'/' + selected_item_path[selected_item_path.rfind('/')+1:]
            shutil.copyfile(selected_item_path, target_path)
            print('\a')
            QMessageBox.information(self, "Copy",
                                    selected_item_path+"\nis Copied to \n"+target_path,
                                    QMessageBox.Ok)
        except IndexError:
            print('\a')
            QMessageBox.information(self, "Error",
                                    "Not selected any item.\nPlease Load or Selected any Item",
                                    QMessageBox.Ok)


class NumericItem(QTableWidgetItem):
    def __lt__(self, other):
        return (self.data(Qt.UserRole) <
                other.data(Qt.UserRole))


class ThumbnailWidget(QLabel):
    def __init__(self, thumbnail_img, parent=None):
        super(ThumbnailWidget, self).__init__(parent)
        if thumbnail_img.mode == "RGB":
            r, g, b = thumbnail_img.split()
            thumbnail_img = Image.merge("RGB", (b, g, r))
        elif thumbnail_img.mode == "RGBA":
            r, g, b, a = thumbnail_img.split()
            thumbnail_img = Image.merge("RGBA", (b, g, r, a))
        elif thumbnail_img.mode == "L":
            thumbnail_img = thumbnail_img.convert("RGBA")

        im2 = thumbnail_img.convert("RGBA")
        data = im2.tobytes("raw", "RGBA")
        qim = QImage(data, thumbnail_img.size[0], thumbnail_img.size[1], QImage.Format_ARGB32)
        pixel_map = QPixmap.fromImage(qim)
        self.setPixmap(pixel_map)


class MoveFilesToPrecede(QThread):
    notifyProgress = pyqtSignal(int)
    current_state = pyqtSignal(str)

    def run(self):
        settings = QSettings()
        pref_save_path = settings.value(Settings.SETTINGS_SAVE_PATH, Settings.DEFAULT_TARGET_PATH, type=str)
        move_path = pref_save_path[:pref_save_path.rfind('/')]
        cpt = sum([len(files) for r, d, files in os.walk(pref_save_path)])
        index = 0

        for (path, _, files) in os.walk(pref_save_path):
            for filename in files:
                index = index + 1
                fix_path = path.replace(pref_save_path, move_path)
                if not os.path.exists(fix_path):
                    os.makedirs(fix_path)
                path = path.replace('\\', '/')
                fix_path = fix_path.replace('\\', '/')
                print(path+' '+fix_path)
                shutil.copy(path+'/'+filename, fix_path+'/'+filename)
                Logger.LOGGER.info(filename+" is moved to "+fix_path)
                self.notifyProgress.emit(100 * index / cpt)
                self.current_state.emit((fix_path+'/'+filename).replace('\\', '/'))
        shutil.rmtree(pref_save_path)
        os.makedirs(pref_save_path)


class FileLoadFromTarget(QThread):
    notifyProgress = pyqtSignal(int)
    current_state = pyqtSignal(str)

    def run(self):
        settings = QSettings()
        pref_target_path = settings.value(Settings.SETTINGS_TARGET_PATH, Settings.DEFAULT_TARGET_PATH, type=str)
        cpt = sum([len(files) for r, d, files in os.walk(pref_target_path)])
        index = 0
        data_list.clear()
        for (path, directory, files) in os.walk(pref_target_path):
            for filename in files:
                ext = filename[filename.rfind('.'):]
                if ext == '.zip':
                    try:
                        index = index + 1
                        canonical_path = path + '/' + filename
                        line_data = FileUtil.get_json_from_path(canonical_path)
                        data_list.append(line_data)
                        # print(line_data)
                        self.notifyProgress.emit(100*index/cpt)
                        self.current_state.emit(line_data['path'])
                        # sleep(0.1)
                    except OSError:
                        Logger.LOGGER.error(traceback.format_exc())
                        continue


def close_application():
    sys.exit()


def open_settings():
    dlg = Settings.SettingsDialog()
    dlg.exec_()


def open_downloader():
    dlg = DownloadView.DownloaderDialog()
    dlg.exec_()


def open_loading_dialog(thread):
    dlg = Dialog.ProgressBar(thread)
    dlg.show()
    dlg.exec_()


def open_manual_input():
    dlg = Dialog.ManualInputDialog()
    dlg.exec_()


if __name__ == '__main__':

    QCoreApplication.setApplicationName(ORGANIZATION_NAME)
    QCoreApplication.setOrganizationDomain(ORGANIZATION_DOMAIN)
    QCoreApplication.setApplicationName(APPLICATION_NAME)

    app = QApplication(sys.argv)
    view = MainWindow()
    view.show()
    sys.exit(app.exec_())
