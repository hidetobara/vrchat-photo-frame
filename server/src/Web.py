import os, hashlib, shutil, requests, json, glob
from flask import Flask, render_template, request, send_from_directory, redirect, jsonify
from PIL import Image

from src.Config import Config
from src.Sheet import Sheet


MIMETYPES = {".png": "image/png", ".jpg": "image/jpeg"}

class Web:

    TMP_DIR = "/tmp/"
    ITEM_LIMIT = 5

    def __init__(self, config: Config):
        self.limits = config.get("limits", {})
        self.key = None
        self.sheet = None

    def get_base_context(self):
        return {}

    def get_locale(self):
        locale = 'en'
        try:
            languages = request.headers.get('Accept-Language').split(',')
            for language in languages:
                locale_long = language.split(';')[0]
                locale = locale_long.split('-')[0]
                break
            if locale not in ['ja', 'en']:
                locale = 'en'
            return locale.lower()
        except:
            return 'en'

    def get_index(self):
        context = self.get_base_context()
        return render_template('top.html', **context)

    def prepare(self, key: str):
        self.key = key
        if self.sheet is None:
            self.sheet = Sheet(key)
        if self.sheet.owner is None:
            raise Exception("This sheet has No owner")
        return self

    def get_limit(self, owner: str):
        if owner in self.limits:
            return self.limits[owner]
        return Web.ITEM_LIMIT

    def get_item(self, worksheet: str, name: str):
        table = self.sheet.load(worksheet)
        for value in table.values():
            if value.name == name:
                return value
        return None

    def get_sheet(self, worksheet: str, format: str):
        table = self.sheet.load(worksheet)
        items = list(table.values())
        print("KEY=", self.key, "OWNER=", self.sheet.owner)
        
        limit = self.get_limit(self.sheet.owner)
        if len(items) > limit:
            items = items[0:limit]

        if format == "csv":
            lines = []
            for item in items:
                lines.append(",".join(item.to_csv()))
            return "\n".join(lines)
        elif format == "json":
            box = []
            for item in items:
                box.append(item.to_json())
            return json.dumps(box, ensure_ascii=False)
        else:
            raise Exception("Invalid format")
        
    def download_img(self, worksheet: str, name: str):
        sha_folder = hashlib.md5((self.sheet.owner).encode("utf-8")).hexdigest()
        sha_name = hashlib.md5((worksheet + "/" + name).encode("utf-8")).hexdigest()

        limit = self.get_limit(self.sheet.owner)
        tmp_dir = Web.TMP_DIR + sha_folder + "/"
        os.makedirs(tmp_dir, exist_ok=True)

        ext = None
        for e, type in MIMETYPES.items():
            path = tmp_dir + sha_name + e
            if os.path.isfile(path):
                ext = e
                break
        if ext is None:
            files = glob.glob(tmp_dir + "*")
            if len(files) >= limit:
                raise Exception("Limit of images")
            item = self.get_item(worksheet, name)
            if item is None:
                raise Exception(f"Not found {name}")
            response = requests.get(item.url)
            response.raise_for_status()
            tmp_path = tmp_dir + sha_name
            with open(tmp_path, "wb") as f:
                f.write(response.content)
            with Image.open(tmp_path) as im:
                if im.size[0] > 2048 or im.size[1] > 2048:
                    raise Exception("Too big image")
                if im.format == "PNG":
                    ext = ".png"
                if im.format == "JPEG":
                    ext = ".jpg"
            if ext is None:
                raise Exception("Unknown format")
            shutil.move(tmp_path, tmp_dir + sha_name + ext)

        return tmp_dir, sha_name + ext, MIMETYPES[ext]
    
    def clear_my_dir(self, worksheet: str):
        sha_folder = hashlib.md5((self.sheet.owner).encode("utf-8")).hexdigest()
        tmp_dir = Web.TMP_DIR + sha_folder + "/"
        shutil.rmtree(tmp_dir, ignore_errors=True)
