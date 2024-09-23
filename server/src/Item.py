import re


class Item:
    G_DRIVE = "G_DRIVE"
    G_PHOTOS = "G_PHOTOS"
    UNKNOWN = "UNKNOWN"

    def __init__(self, row: list) -> None:
        self.id = row[0] if len(row) > 0 else None
        self.url = row[1] if len(row) > 1 and len(row[1]) > 0 else None
        self.title = row[2] if len(row) > 2 and len(row[2]) > 0 else None
        self.public_url = None

    def is_valid(self) -> bool:
        if len(self.id) == 0:
            return False
        if self.url is None or re.match(r"(http://|https://|/)", self.url):
            return True
        return False
    
    def has_external_image(self) -> bool:
        if self.url is None:
            return False
        if self.url.startswith("https://") or self.url.startswith("http://"):
            return True
        return False

    def has_direct_image(self) -> bool:
        if self.url is None:
            return False
        if self.url.startswith("/"):
            return True
        return False

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
        # 例)
        # https://photos.google.com/share/AF1QipPc63AHAys_G4756KfQrQUFxHyhXSIqAgGBUNkWXIXsdCOFYiEBuoE0CjYand0Jgg/photo/AF1QipPcV66lOAUmCTWjYjF1ba8eoJBcPFkwqgumR_hc?key=c3FUbnVYc0tqSGgzMG5RR0hwdDB6WVBFTDdqc0xR
        if self.url is None:
            return None
        m = re.match(r"https://photos\.google\.com/share/([\w_-]+)/photo/([\w_-]+)\?", self.url)
        if m:
            return m.group(1), m.group(2)
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
