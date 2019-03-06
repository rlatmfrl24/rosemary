import re

regex_hiyobi_group = re.compile(r'\((.*?)\)')
regex_remove_bracket = re.compile(r'[\(|\)]')
regex_replace_path = re.compile(r'\\|\:|\/|\*|\?|\"|\<|\>|\|')


class Gallery:
    """
    Manga Gallery 데이터를 구조화한 클래스
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
        self.make_path()

    def make_path(self):
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
