from bs4 import BeautifulSoup
from selenium import webdriver
import requests
import os
from tqdm import tqdm
from Model import FirebaseClient, Gallery

# TODO 이 부분은 Private Data로 Crypto 필요
fbclient = FirebaseClient.FirebaseClient(
    '397love@gmail.com',
    '397love'
)

URL_HITOMI = 'https://hitomi.la'
URL_HITOMI_LIST = URL_HITOMI+"/index-korean-1.html"


def get_download_list(crawl_page):

    exception_list = FirebaseClient.fbclient.get_document_list()

    gallery_list = []
    current_path = os.path.dirname(__file__)
    current_path = current_path[:current_path.rfind('/')]
    chrome_path = os.path.join(current_path, 'chromedriver.exe')
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")
    driver = webdriver.Chrome(chrome_options=options, executable_path=chrome_path)
    driver.implicitly_wait(10)

    for i in tqdm(range(1, crawl_page + 1)):
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
    driver.close()
    return gallery_list


list = get_download_list(3)
print(list.__len__())
for item in list:
    print(item.path)


