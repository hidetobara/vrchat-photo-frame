import gspread
from oauth2client.service_account import ServiceAccountCredentials 

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


class Item:
    def __init__(self, row: list) -> None:
        self.name = row[0] if len(row) > 0 else None
        self.url = row[1] if len(row) > 1 else None
        self.title = row[2] if len(row) > 2 else None

    def is_valid(self):
        if len(self.name) == 0 or len(self.url) == 0:
            return False
        return self.url.startswith("https://") or self.url.startswith("http://")

    def to_csv(self):
        return [self.name, self.url, self.title]
    def to_json(self):
        return {"name": self.name, "url": self.url, "title": self.title}

class Sheet:
    def __init__(self, key):
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive.readonly']
        credentials = ServiceAccountCredentials.from_json_keyfile_name('./private/vrchat-analyzer-ba2bcb1497e6.json', scope)
        self.gc = gspread.authorize(credentials)
        self.key = key
        self.owner = self.selectOwner(credentials)

    def close(self):
        if self.gc is not None:
            self.gc.session.close()
            self.gc = None

    def selectOwner(self, credentials):
        gauth = GoogleAuth()
        gauth.auth_method = 'service'
        gauth.credentials = credentials
        drive = GoogleDrive(gauth)
        file = drive.CreateFile({'id': self.key})
        for permission in file.GetPermissions():
            if permission['role'] == 'owner':
                return permission['emailAddress']
        return None

    def load(self, worksheet) -> dict:
        worksheet = self.gc.open_by_key(self.key).worksheet(worksheet)
        table = {}
        for row in worksheet.get_all_values():
            i = Item(row)
            if not i.is_valid(): continue

            table[i.name] = i
        return table

