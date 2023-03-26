import os
import io
from PIL import Image

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/app/private/vrchat-analyzer.json"

class Photos:
    """
    サービスアカウントは使えない、いったん保留
    """
    SERVICE_ACCOUNT = "/app/private/vrchat-analyzer.json"
    SCOPES = ['https://www.googleapis.com/auth/photoslibrary',
              'https://www.googleapis.com/auth/photoslibrary.sharing']

    def download_photos(self, album_id):
        service = build('photoslibrary', 'v1', static_discovery=False)
        photos = []
        nextpagetoken = ''
        while nextpagetoken is not None:
            results = service.mediaItems().search(
                body={'albumId': album_id,
                    'pageSize': 100,
                    'pageToken': nextpagetoken}).execute()
            items = results.get('mediaItems', [])
            nextpagetoken = results.get('nextPageToken', None)
            photos.extend(items)
        for photo in photos:
            response = service.mediaItems().getMedia(mediaItemId=photo['id']).execute()
            print(photo)
            bytes_io = io.BytesIO(response)
            image = Image.open(bytes_io)
            image.save(photo['filename'])
