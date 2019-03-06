from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QSettings, QThread, pyqtSignal
from bs4 import BeautifulSoup
from time import sleep
from selenium import webdriver
from tqdm import tqdm
from requests_futures.sessions import FuturesSession
import traceback
import shutil
import cfscrape
import requests
import os
from Model import FileUtil, FirebaseClient, Logger, Gallery
from View import Settings, Dialog

URL_HIYOBI = "https://hiyobi.me/"
READER_URL = "https://hybcomics.xyz"


class GalleryDownload(QThread):
    """
    Hiyobi Gallery 다운로드용 스레드
    """
    def __init__(self, gallery, state, driver):
        super().__init__()
        self.gallery = gallery
        self.state = state
        self.total_cnt = 0
        self.current_cnt = 0
        self.thread_pool = []
        self.driver = driver

    def __del__(self):
        self.wait()

    def response_to_file(self, response, name, path):
        save_directory = path + "/"
        with open(save_directory + name, 'wb') as f:
            f.write(response.content)
        self.current_cnt = self.current_cnt + 1
        self.state.emit(str(self.current_cnt) + '/' + str(self.total_cnt))

    def run(self):
        settings = QSettings()
        pref_target_path = settings.value(Settings.SETTINGS_SAVE_PATH, Settings.DEFAULT_TARGET_PATH, type=str)
        pref_max_pool_cnt = settings.value(Settings.SETTINGS_MAX_POOL_CNT, Settings.DEFAULT_MAX_POOL, type=int)
        gallery_save_path = pref_target_path+'/'+self.gallery.path
        if not os.path.exists(gallery_save_path):
            os.makedirs(gallery_save_path)

        # Cloudflare Authorization
        self.state.emit('Authorize..')
        Logger.LOGGER.info("Wait for Cloudflare Authorization..")
        self.driver.get(URL_HIYOBI)
        while "Just a moment..." in self.driver.page_source:
            pass
        user_agent = self.driver.execute_script("return navigator.userAgent;")

        try:
            cookie_value = '__cfduid=' + self.driver.get_cookie('__cfduid')['value'] + \
                           '; cf_clearance=' + self.driver.get_cookie('cf_clearance')['value']
            headers = {'User-Agent': user_agent}
            cookies = {'session_id': cookie_value}
        except TypeError:
            Logger.LOGGER.warning("Not apply cookies to requests")
            headers = None
            cookies = None

        # Fetch image data from gallery page
        self.state.emit('Fetch..')
        Logger.LOGGER.info("Connect to Gallery page..")
        self.driver.get(self.gallery.url)
        sleep(1)
        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        # Start download multi-thread
        Logger.LOGGER.info("Download Start..")
        img_urls = soup.find_all('div', class_="img-url")
        self.total_cnt = len(img_urls)
        session = FuturesSession(max_workers=pref_max_pool_cnt)
        if headers is not None:
            session.headers = headers
        if cookies is not None:
            session.cookies = cookies
        responses = {}
        for url_path in img_urls:
            url = READER_URL+url_path.text
            name = url.split('/')[-1]
            responses[name] = session.get(url)
        for filename in responses:
            self.response_to_file(response=responses[filename].result(), name=filename, path=gallery_save_path)
        session.close()

        # Compress Zip Files
        self.state.emit('Compressing..')
        if self.gallery.original != "":
            zip_path = pref_target_path+'/'+self.gallery.type+'/'+self.gallery.original+'/'+self.gallery.path+'.zip'
        else:
            zip_path = pref_target_path+'/'+self.gallery.type+'/'+self.gallery.path+'.zip'

        try:
            if not os.path.exists(zip_path[:zip_path.rfind('/')]):
                os.makedirs(zip_path[:zip_path.rfind('/')])
            FileUtil.make_zip(gallery_save_path, zip_path)
            shutil.rmtree(gallery_save_path)
        except:
            print(traceback.format_exc())
            Logger.LOGGER.error("Compressing Process Error... pass")
        # Save to Firebase
        # TODO Enable next line on Build
        FirebaseClient.fbclient.insert_data(self.gallery)


class DownloadByTable(QThread):
    """
    Gallery List 다운로드용 스레드
    """
    current_state = pyqtSignal(str)
    item_index = pyqtSignal(int)
    thread_finished = pyqtSignal(bool)

    def __init__(self, download_list, parent):
        super().__init__()
        self.list = download_list
        self.parent = parent

    def __del__(self):
        self.wait()

    def run(self):
        # WebDriver Open
        current_path = os.path.dirname(__file__)
        current_path = current_path[:current_path.rfind('\\')]
        chrome_path = os.path.join(current_path, 'chromedriver.exe')
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=1920x1080')
        options.add_argument("disable-gpu")
        driver = webdriver.Chrome(chrome_options=options, executable_path=chrome_path)
        driver.implicitly_wait(10)

        for item in self.list:
            Logger.LOGGER.info('Download Start => '+item.title)
            self.item_index.emit(self.list.index(item))
            self.current_state.emit('Start!')
            thread = GalleryDownload(item, self.current_state, driver)
            thread.start()
            thread.wait()
            Logger.LOGGER.info('Download Finished => '+item.title)
            Logger.LOGGER.info('='*100)
            self.current_state.emit('Finish!')
        driver.close()
        driver.quit()
        self.thread_finished.emit(True)


def get_download_list(crawl_page, parent):
    """
    Get Download List from Hiyobi
    :param crawl_page: 수집할 페이지 범위
    :param parent: 진행 상황을 표시할 화면
    :return: 수집된 Gallery List
    """
    Logger.LOGGER.info("Load exception list from Firebase")
    parent.current_state.emit("Load exception list from Firebase")
    exception_list = FirebaseClient.fbclient.get_document_list()
    # TODO Remove next line on build
    # exception_list = []
    parent.notifyProgress.emit(100 * 1 / (crawl_page+2))

    try:
        gallery_list = []
        Logger.LOGGER.info("Get cookie data for Cloudflare..")
        parent.current_state.emit("Get cookie data for Cloudflare..")
        cookie_value, user_agent = cfscrape.get_cookie_string(URL_HIYOBI)
        headers = {'User-Agent': user_agent}
        cookies = {'session_id': cookie_value}
        parent.notifyProgress.emit(100 * 2 / (crawl_page+2))
    except Exception:
        Logger.LOGGER.error("Unexpected Exception Error..")
        Logger.LOGGER.error(traceback.format_exc())
        Dialog.ErrorDialog().open_dialog("Unexpected Exception Error", "Unexpected Exception Request Error!")

    try:
        for i in tqdm(range(1, crawl_page+1)):
            # print("[SYSTEM]: Load From Page %d.." % i)
            parent.current_state.emit("Load From Page %d.." % i)
            soup = BeautifulSoup(requests.get(URL_HIYOBI+'list/'+str(i), cookies=cookies, headers=headers).content, 'html.parser')
            galleries = soup.find_all('div', class_="gallery-content")
            for data in galleries:
                gallery = Gallery.Gallery()
                gallery.initialize(data)
                if gallery.code not in exception_list:
                    gallery_list.append(gallery)
            parent.notifyProgress.emit(100 * (i+2) / (crawl_page+2))
        return gallery_list
    except requests.exceptions.RequestException:
        Logger.LOGGER.error("Hiyobi Requests Error..")
        Dialog.ErrorDialog().open_dialog("Hiyobi Error", "Hiyobi Request Error!")
    except Exception:
        Logger.LOGGER.error("Unexpected Error in Hiyobi Request")
        Logger.LOGGER.error(traceback.format_exc())
        Dialog.ErrorDialog().open_dialog("Unexpected Exception Error", "Unexpected Exception Request Error!")



