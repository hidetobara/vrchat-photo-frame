import io
import requests
import gspread
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from src.Env import Env
from src.Item import Item


env = Env()

class Drive:
    """
    権限
    https://developers.google.com/drive/api/v3/reference/permissions/list
    """
    def __init__(self, key):
        self.key = key
        self.credentials = env.get_google_credentials()
        self.owner = None

    def get_file_owner(self):
        service = build('drive', 'v3', credentials=self.credentials)
        
        file_metadata = service.files().get(fileId=self.key, fields="owners").execute()
        owners = file_metadata.get('owners', [])
        
        if owners:
            for owner in owners:
                self.owner = owner.get('emailAddress')
        else:
            print("WARN: No owner.")

    def download(self, path):
        """Google Driveからファイルをダウンロードする関数"""
        service = build('drive', 'v3', credentials=self.credentials)

        # ファイル取得
        request = service.files().get_media(fileId=self.key)
        fh = io.FileIO(path, 'wb')
        
        # ダウンロードプロセス
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%.")

    def prepare(self) -> any:
        self.get_file_owner()
        return self


class Sheet(Drive):
    def __init__(self, key):
        super().__init__(key)
        self.gc = gspread.authorize(self.credentials)

    def close(self):
        if self.gc is not None and hasattr(self.gc, "session"):
            self.gc.session.close()
            self.gc = None

    def load(self, title) -> dict:
        sheet = self.gc.open_by_key(self.key)
        target = sheet.sheet1
        for w in sheet.worksheets():
            if w.title == title:
                target = w
                break
        table = {}
        for row in target.get_all_values():
            i = Item(row)
            if not i.is_valid(): continue
            table[i.id] = i
        return table


class Photos:
    """
    やっぱり動かないな
    """
    def __init__(self, keys: tuple):
        self.share_id = keys[0]
        self.photo_id = keys[1]
        self.credentials = env.get_google_credentials()
        self.owner = None

    def prepare(self) -> any:
        # 何もしない
        return self

    def download(self, path):
        service = build('photoslibrary', 'v1', credentials=self.credentials)
        response = service.sharedAlbums().get(sharedAlbumId=self.share_id).execute()
        album_id = response['id']
        print(response)

        results = service.mediaItems().search(body={'albumId': album_id}).execute()
        items = results.get('mediaItems', [])

        for item in items:
            if item['id'] != self.photo_id:
                continue
            base_url = item['baseUrl']
            download_url = f"{base_url}=d"
            response = requests.get(download_url)
            with open(path, 'wb') as f:
                f.write(response.content)
