import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials 

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


class Item:
    G_DRIVE = "G_DRIVE"
    G_PHOTOS = "G_PHOTOS"
    UNKNOWN = "UNKNOWN"

    def __init__(self, row: list) -> None:
        self.id = row[0] if len(row) > 0 else None
        self.url = row[1] if len(row) > 1 else None
        self.title = row[2] if len(row) > 2 else None
        self.public_url = None

    def is_valid(self) -> bool:
        if len(self.id) == 0 or len(self.url) == 0:
            return False
        return self.url.startswith("https://") or self.url.startswith("http://")

    def get_type(self):
        if self.get_drive_key():
            return self.G_DRIVE
        if self.get_photos_key():
            return self.G_PHOTOS
        return self.UNKNOWN

    def get_drive_key(self):
        if self.url is None: return None
        m = re.match(r"https://drive\.google\.com/file/d/([\w_-]+)", self.url)
        if m:
            return m.group(1)
        return None

    def get_photos_key(self):
        if self.url is None: return None
        m = re.match(r"https://photos\.app\.goo\.gl/([\w_-]+)", self.url)
        if m:
            return m.group(1)
        return None

    def to_csv(self) -> list:
        return [self.id, self.url, self.title, self.get_type(), self.public_url]
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "type": self.get_type(),
            "public": self.public_url
        }

class Drive:
    """
    権限
    https://developers.google.com/drive/api/v3/reference/permissions/list
    """
    SCOPES = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']

    def __init__(self, key):
        self.key = key
        self.credentials = ServiceAccountCredentials.from_json_keyfile_name('/app/private/vrchat-analyzer.json', self.SCOPES)
        self.file = None
        self.owner = None

    def checkOwner(self):
        gauth = GoogleAuth()
        gauth.auth_method = 'service'
        gauth.credentials = self.credentials
        drive = GoogleDrive(gauth)
        self.file = drive.CreateFile({'id': self.key})
        for permission in self.file.GetPermissions():
            if permission['role'] == 'owner':
                self.owner = permission['emailAddress']

    def prepare(self) -> any:
        self.checkOwner()
        return self

    def download(self, path):
        self.file.GetContentFile(path)

class Sheet(Drive):
    def __init__(self, key):
        super().__init__(key)
        self.gc = gspread.authorize(self.credentials)

    def close(self):
        if self.gc is not None:
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

