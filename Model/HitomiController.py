from PyQt5.QtCore import QThread, pyqtSignal, QSettings
from bs4 import BeautifulSoup
from selenium import webdriver
from requests_futures.sessions import FuturesSession
from tqdm import tqdm
import os
import shutil
import traceback
from Model import FirebaseClient, Gallery, Logger, FileUtil
from View import Settings

URL_HITOMI = 'https://hitomi.la'
URL_HITOMI_LIST = URL_HITOMI+"/index-korean-1.html"


class GalleryDownload(QThread):
    def __init__(self, gallery, state, driver):
        super().__init__()
        self.gallery = gallery
        self.state = state
        self.total_cnt = 0
        self.current_cnt = 0
        self.thread_pool = []
        self.driver = driver

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
        self.driver.get(URL_HITOMI)
        while "Just a moment..." in self.driver.page_source:
            pass
        user_agent = self.driver.execute_script("return navigator.userAgent;")

        # Set Cookie Value
        try:
            cookie_value = '__cfduid=' + self.driver.get_cookie('__cfduid')['value'] + \
                           '; cf_clearance=' + self.driver.get_cookie('cf_clearance')['value']
            cookies = {'session_id': cookie_value}
        except TypeError:
            Logger.LOGGER.warning("Not apply cookies to requests")
            cookies = None

        # Set Request Header
        try:
            headers = {
                'User-Agent': user_agent,
                'referer': self.gallery.url.replace('galleries', 'reader')
            }
        except TypeError:
            Logger.LOGGER.warning('Error on Setting HEADER')
            headers = None

        # Make Download Session
        session = FuturesSession(max_workers=pref_max_pool_cnt)
        if headers is not None:
            session.headers = headers
        if cookies is not None:
            session.cookies = cookies
        responses = {}

        # Fetch image data from gallery page
        download_list = []
        self.state.emit('Fetch..')
        Logger.LOGGER.info("Connect to Gallery page..")
        self.driver.get(self.gallery.url.replace('galleries', 'reader'))
        source = self.driver.page_source
        soup = BeautifulSoup(source, 'html.parser')
        ref_url = soup.find('img')['src']
        ref_key = ref_url[:ref_url.index('.')]
        img_urls = soup.find_all('div', class_='img-url')
        self.total_cnt = len(img_urls)
        for img_url in img_urls:
            download_url = 'https:' + img_url.get_text().replace('//g', ref_key)
            download_name = download_url.split('/')[-1]
            responses[download_name] = session.get(download_url)
            download_list.append(download_url)
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
        #FirebaseClient.fbclient.insert_data(self.gallery)


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
    :param crawl_page: 수집할 페이지 범위
    :param parent: 진행 상황을 표시할 화면
    :return: 수집된 Gallery List
    """
    Logger.LOGGER.info("Load exception list from Firebase")
    parent.current_state.emit("Load exception list from Firebase")
    exception_list = FirebaseClient.fbclient.get_document_list()

    Logger.LOGGER.info("Open webdriver for crwaling..")
    parent.current_state.emit("Open webdriver for crwaling..")
    gallery_list = []
    current_path = os.path.dirname(__file__)
    current_path = current_path[:current_path.rfind('\\')]
    chrome_path = os.path.join(current_path, 'chromedriver.exe')
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")
    driver = webdriver.Chrome(chrome_options=options, executable_path=chrome_path)
    driver.implicitly_wait(10)

    for i in tqdm(range(1, crawl_page + 1)):
        parent.current_state.emit("Load From Page %d.." % i)
        driver.get(URL_HITOMI_LIST.replace('1', str(i)))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        gallery_content = soup.find('div', class_="gallery-content")
        temp = gallery_content.findChildren('div', recursive=False)
        for item in temp:
            gallery = Gallery.Gallery()
            gallery.url = URL_HITOMI + item.find('a')['href']
            gallery.code = gallery.url[gallery.url.rfind('/') + 1:gallery.url.index('.html')]
            gallery.title = item.find('h1').string
            gallery.artist = item.find('div', class_="artist-list").get_text().strip().replace('\n', ", ")
            desc_table = item.find('tbody').findChildren('a')
            for desc in desc_table:
                desc_key = desc['href']
                desc_content = desc.get_text().strip()
                if '/type/' in desc_key:
                    if desc_content == 'doujinshi':
                        gallery.type = "동인지"
                    elif desc_content == 'manga':
                        gallery.type = "망가"
                    elif desc_content == 'artist CG':
                        gallery.type = "cg아트"
                elif '/series/' in desc_key:
                    gallery.original = desc_content
                elif '/tag/' in desc_key:
                    gallery.keyword += desc_content + "|"
                # print(desc['href']+" = "+desc.get_text().strip())
            gallery.make_path()
            if gallery.code not in exception_list:
                gallery_list.append(gallery)
                gallery.print_gallery()
            parent.notifyProgress.emit(100 * (i+2) / (crawl_page+2))
    driver.close()
    return gallery_list

