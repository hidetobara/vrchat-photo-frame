import gspread
from oauth2client.service_account import ServiceAccountCredentials 

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


class Item:
    def __init__(self, name, url, title) -> None:
        self.name = name
        self.url = url
        self.title = title

    def is_valid(self):
        return len(self.name) > 0 and len(self.url) > 0 and self.url.startswith("https://")

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
            i = Item(row[0], row[1], row[2])
            if not i.is_valid(): continue

            table[i.name] = i
        return table

