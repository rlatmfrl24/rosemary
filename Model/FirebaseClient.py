import requests
import json
import datetime
from Model import Logger


class Encoder(json.JSONEncoder):
    """
    JSON Encoder Class
    """
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        else:
            return json.JSONEncoder.default(self, obj)


class FirebaseClient:
    """
    Firebase Client Class
    """
    firebase_web_key = 'AIzaSyAZnLwVTfuf6plvdrzxwESwJHD-6caPPP8'
    firestore_api_url = 'https://firestore.googleapis.com/v1beta1/'
    auth_url = 'https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key='
    database_route = 'projects/soulkey-rosemary/databases/(default)'
    idToken = ""
    item_list = []
    email = ""
    password = ""

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.idToken = self.get_firebase_id_token(self.email, self.password)

    def get_firebase_id_token(self, email, password):
        """
        firebase 인증 토큰을 발급받는다
        :param email: 인증 Email
        :param password: 인증 Password
        :return: Firebase ID Token
        """
        auth_url = self.auth_url + self.firebase_web_key
        auth_data = {
            u'email': email,
            u'password': password,
            u'returnSecureToken': True
        }
        response = requests.post(
            auth_url,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(auth_data))
        token = response.json()['idToken']
        return token

    def get_document_list(self):
        """
        Firebase로부터 Document Code List를 가져온다
        :return: Firebase로부터 가져온 Code List
        """
        code_list = []
        target_url = self.firestore_api_url + self.database_route + '/documents:runQuery?key='+self.firebase_web_key
        structed_query = {
            "structuredQuery": {
                "from": [
                    {
                        "collectionId": 'hiyobi'
                    }
                ],
            }
        }
        headers = {'Authorization': 'Bearer ' + self.idToken}
        response = requests.post(target_url, headers=headers, json=structed_query)
        for item in response.json():
            code_list.append(str(item['document']['fields']['code']['stringValue']))
        return code_list

    def insert_data(self, gallery):
        """
        Firebase에 다운로드한 Hiyobi Gallery 데이터를 저장한다
        :param gallery: 저장할 Hiyobi Gallery 데이터
        :return:
        """
        target_url = self.firestore_api_url+self.database_route+'/documents/hiyobi?key='+self.firebase_web_key
        headers = {'Authorization': 'Bearer '+ self.idToken}
        data = {
            'fields': {
                "artist": {"stringValue": gallery.artist},
                "code": {"stringValue": gallery.code},
                "group": {"stringValue": gallery.group},
                "keyword": {"stringValue": gallery.keyword},
                "original": {"stringValue": gallery.original},
                "path": {"stringValue": gallery.path},
                "title": {"stringValue": gallery.title},
                "type": {"stringValue": gallery.type},
                "url": {"stringValue": gallery.url},
                "createdTimestamp": {"timestampValue": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')},
            }
        }
        response = requests.post(target_url, headers=headers, data=json.dumps(data, cls=Encoder))
        Logger.LOGGER.info("[SYSTEM]: Save Data to Firebase Document ID at '"+response.json()['name'].split('/')[-1]+"'")
