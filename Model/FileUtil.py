from PyQt5.QtCore import QSettings
from PIL import Image
from View import Settings
from Model import Logger
import datetime
import io
import os
import pytz
import subprocess
import zipfile


def get_filetime(mtime):
    """
    시스템 형식의 시간을 Human-Readable한 형식으로 변환
    :param mtime: 시스템 형식의 시간 데이터
    :return: Human-Readable한 시간 데이터
    """
    tz_seoul = pytz.timezone('Asia/Seoul')
    fmt = '%Y-%m-%d %H:%M:%S %Z%z'
    utc_dt = pytz.utc.localize(datetime.datetime.utcfromtimestamp(mtime))
    return utc_dt.astimezone(tz_seoul).strftime(fmt)


def sizeof_fmt(num, suffix='B'):
    """
    바이트 단위 사이즈를 Human-Readable한 형식으로 변환
    :param num: 변환할 바이트 사이즈
    :param suffix: 변환 데이터 뒤에 붙일 Suffix
    :return: Human-Readable한 사이즈 데이터
    """
    for unit in ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def get_json_from_path(path):
    """
    입력받은 경로의 파일의 정보를 분석하여 JSON 형식의 데이터로 변환
    :param path: 분석할 파일의 경로
    :return: 분석된 파일의 JSON 데이터
    """
    settings = QSettings()
    pref_target_path = settings.value(Settings.SETTINGS_TARGET_PATH, Settings.DEFAULT_TARGET_PATH, type=str)
    pref_toggle_preview = settings.value(Settings.SETTINGS_TOGGLE_PREVIEW, True, type=bool)

    filename = path[path.rfind('/')+1:]
    path = path.replace('\\', "/")
    (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(path)
    if '[' in filename:
        author = filename[filename.index('[') + 1:filename.index(']')]
        title = filename[filename.index(']') + 1:filename.rfind('(')]
    else:
        author = ""
        title = filename[:filename.rfind('(')]
    code = filename[filename.rfind('(') + 1:filename.rfind(')')]
    kinds = path[len(pref_target_path):path.rfind('/')]
    try:
        if pref_toggle_preview:
            thumbnail = get_thumbnail_from_zip(path)
        else:
            thumbnail = None
    except OSError:
        thumbnail = None
    Logger.LOGGER.debug("Gallery '"+path+"' Data")
    Logger.LOGGER.debug('author: ' + author)
    Logger.LOGGER.debug('code: ' + code)
    Logger.LOGGER.debug('title: ' + title)
    Logger.LOGGER.debug('kinds: ' + kinds)
    Logger.LOGGER.debug('mtime: ' + get_filetime(mtime))
    Logger.LOGGER.debug('size: ' + str(size))
    Logger.LOGGER.debug('size_fmt: ' + sizeof_fmt(size))
    Logger.LOGGER.debug('path: ' + path)
    Logger.LOGGER.debug('thumbnail: ' + str(thumbnail))

    result = {
        'author': author,
        'code': code,
        'title': title,
        'kinds': kinds,
        'mtime': get_filetime(mtime),
        'size': size,
        'size_fmt': sizeof_fmt(size),
        'path': path,
        'thumbnail': thumbnail
    }
    return result


def get_thumbnail_from_zip(path):
    """
    입력받은 경로의 ZIP 파일로부터 썸네일을 추출
    :param path: 썸네일을 추출한 ZIP의 경로
    :return: 입력받은 경로의 ZIP 파일의 썸네일
    """
    Logger.LOGGER.debug('Get Thumbnail images from "'+path+'"')
    zipped_img = zipfile.ZipFile(path)
    data = zipped_img.read(zipped_img.namelist()[0])
    data_encoded = io.BytesIO(data)
    img = Image.open(data_encoded)
    img.thumbnail((128, 128))
    return img


def open_viewer(path):
    """
    지정된 경로의 Viewer로 입력받은 경로의 파일을 연다
    :param path: Viewer로 열 파일의 경로
    :return:
    """
    settings = QSettings()
    pref_viewer_path = settings.value(Settings.SETTINGS_VIEWER_PATH, Settings.HONEYVIEW_PATH, type=str)
    Logger.LOGGER.info('Open "'+path+'" with "'+pref_viewer_path+'"')
    subprocess.SW_HIDE = 1
    subprocess.Popen(pref_viewer_path + " "+ path)


def open_explorer(path):
    """
    입력받은 경로의 파일을 윈도우 탐색기로 연다
    :param path: 윈도우 탐색기로 열 파일의 경로
    :return: 
    """
    Logger.LOGGER.info(f'explorer /select,{os.path.normpath(path)}')
    subprocess.Popen(f'explorer /select,{os.path.normpath(path)}')


# def unzip(source_file, dest_path):
#     """
#     ZIP의 압축을 해제한다
#     :param source_file: 압축을 해제할 ZIP 파일
#     :param dest_path: 압축을 해제할 경로
#     :return:
#     """
#     with zipfile.ZipFile(source_file, 'r') as zf:
#         zf.extractall(path=dest_path)
#         zf.close()


def make_zip(src_path, dest_file):
    """
    지정된 경로의 폴더를 ZIP로 압축한다.
    :param src_path: 압축할 폴더 경로
    :param dest_file: 압축파일을 저장할 경로
    :return:
    """
    with zipfile.ZipFile(dest_file, 'w') as zf:
        root_path = src_path
        for (path, dir, files) in os.walk(src_path):
            for file in files:
                full_path = os.path.join(path, file)
                relpath = os.path.relpath(full_path, root_path);
                zf.write(full_path, relpath, zipfile.ZIP_DEFLATED)
        zf.close()
    Logger.LOGGER.info('[SYSTEM]: "'+relpath+'" ZIP file is created successfully..')
