from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QSettings, QThread, pyqtSignal
from bs4 import BeautifulSoup
from time import sleep
from selenium import webdriver
from tqdm import tqdm
import traceback
import shutil
import cfscrape
import requests
import re
import os
from Model import FileUtil, FirebaseClient, Logger
from View import Settings, Dialog

URL_HIYOBI = "https://hiyobi.me/"
READER_URL = "https://hybcomics.xyz"

regex_hiyobi_group = re.compile(r'\((.*?)\)')
regex_remove_bracket = re.compile(r'[\(|\)]')
regex_replace_path = re.compile(r'\\|\:|\/|\*|\?|\"|\<|\>|\|')

# TODO 이 부분은 Private Data로 Crypto 필요
fbclient = FirebaseClient.FirebaseClient(
    '397love@gmail.com',
    '397love'
)


class Gallery:
    """
    Hiyobi Gallery 데이터를 구조화한 클래스
    """
    artist, code, group, keyword, original, path, title, type, url = "", "", "", "", "", "", "", "", ""

    def initialize(self, source):
        self.title = source.find('b').text
        self.url = source.find('a', attrs={'target': '_blank'})['href']
        self.code = self.url[self.url.rfind('/') + 1:]
        sub_data = source.find_all('td')
        for j in range(0, len(sub_data)):
            if sub_data[j].text == '작가 : ':
                self.artist = re.sub(regex_hiyobi_group, "", sub_data[j + 1].text).strip()
                self.group = sub_data[j + 1].text.replace(self.artist, "")
                self.group = re.sub(regex_remove_bracket, "", self.group).strip()
            elif sub_data[j].text == '원작 : ':
                self.original = sub_data[j + 1].text.strip()
            elif sub_data[j].text == '종류 : ':
                self.type = sub_data[j + 1].text.strip()
            elif sub_data[j].text == '태그 : ':
                for tag in sub_data[j + 1].find_all('a'):
                    self.keyword = self.keyword + '|' + tag.text.strip()
                    self.keyword = self.keyword[1:]
        # make path
        if self.artist is not "":
            self.path = "[" + self.artist + "]"
        self.path = self.path + self.title + "(" + self.code + ")"
        self.path = re.sub(pattern=regex_replace_path, repl='_', string=self.path)

    def print_gallery(self):
        """
        Gallery 데이터 출력 함수(Debug 용)
        :return: 
        """
        print("artist: " + self.artist)
        print('code: ' + self.code)
        print("group: " + self.group)
        print("keyword: " + self.keyword)
        print("original: " + self.original)
        print('path: ' + self.path)
        print('title: ' + self.title)
        print("type: " + self.type)
        print('url: ' + self.url)

    def valid_input_error(self):
        """
        필수 항목(code, title, url) 입력 체크
        :return: 필수 항목 입력 여부
        """
        if self.code == "" or self.title == "" or self.url == "":
            return False
        else:
            return True


class ImageDownload(QThread):
    """
    단일 이미지 다운로드용 스레드
    """

    def __init__(self, target_url, save_path, header, cookie, parent):
        super().__init__()
        self.target_url = target_url
        self.save_path = save_path
        self.header = header
        self.cookie = cookie
        self.parent = parent

    def run(self):
        try:
            # print(self.target_url)
            if self.header is not None and self.cookie is not None:
                cf_url = requests.get(self.target_url, cookies=self.cookie, headers=self.header).content
            else:
                cf_url = requests.get(self.target_url).content
            name = self.target_url.split('/')[-1]
            save_directory = self.save_path + "/"
            with open(save_directory + name, 'wb') as f:
                f.write(cf_url)
            self.parent.current_cnt = self.parent.current_cnt+1
            self.parent.state.emit(str(self.parent.current_cnt)+'/'+str(self.parent.total_cnt))
        except requests.exceptions.RequestException:
            Logger.LOGGER.error(traceback.format_exc())
            QMessageBox.critical(self, "Download Error",
                                 "Error raised while download '"+self.target_url+"'\n\n"+traceback.format_exc())


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

        use_cluodflare = None
        try:
            cookie_value = '__cfduid=' + self.driver.get_cookie('__cfduid')['value'] + \
                           '; cf_clearance=' + self.driver.get_cookie('cf_clearance')['value']
            headers = {'User-Agent': user_agent}
            cookies = {'session_id': cookie_value}
            use_cluodflare = True
        except TypeError:
            Logger.LOGGER.warning("Not apply cookies to requests")
            headers = None
            cookies = None
            use_cluodflare = False

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

        while len(img_urls) > 0:
            if len(self.thread_pool) > pref_max_pool_cnt:
                for thread in self.thread_pool:
                    thread.wait()
                self.thread_pool.clear()
            else:
                img_url = img_urls.pop()
                if use_cluodflare is True:
                    thread = ImageDownload(READER_URL + img_url.text, gallery_save_path, headers, cookies, self)
                else:
                    thread = ImageDownload(READER_URL + img_url.text, gallery_save_path, None, None, self)
                thread.start()
                self.thread_pool.append(thread)
        for thread in self.thread_pool:
            thread.wait()

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
        # fbclient.insert_data(self.gallery)


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
    exception_list = fbclient.get_document_list()
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
        Dialog.ErrorDialog().open_dialog("Unexpected Exception Error", "Unexpected Exception Request Error!")

    try:
        for i in tqdm(range(1, crawl_page+1)):
            # print("[SYSTEM]: Load From Page %d.." % i)
            parent.current_state.emit("Load From Page %d.." % i)
            soup = BeautifulSoup(requests.get(URL_HIYOBI+'list/'+str(i), cookies=cookies, headers=headers).content, 'html.parser')
            galleries = soup.find_all('div', class_="gallery-content")
            for data in galleries:
                gallery = Gallery()
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



