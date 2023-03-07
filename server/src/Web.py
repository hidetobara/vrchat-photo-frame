import os, hashlib, shutil, requests, json
from flask import Flask, render_template, request, send_from_directory, redirect, jsonify
from PIL import Image

from src.Config import Config
from src.Sheet import Sheet


MIMETYPES = {".png": "image/png", ".jpg": "image/jpeg"}

class Web:

    TMP_DIR = "/tmp/"
    ITEM_LIMIT = 10

    def __init__(self, config: Config):
        self.limits = config.get("limits", {})

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

    def get_item(self, key: str, worksheet: str, name: str):
        sheet = Sheet(key)
        table = sheet.load(worksheet)
        for value in table.values():
            if value.name == name:
                return value
        return None

    def get_sheet(self, key: str, worksheet: str, format: str):
        sheet = Sheet(key)
        table = sheet.load(worksheet)
        items = list(table.values())

        limit = Web.ITEM_LIMIT
        limit_key = key + "|" + worksheet
        if limit_key in self.limits:
            limit = self.limits[limit_key]
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
        
    def download_img(self, key: str, worksheet: str, name: str):
        sha_name = hashlib.sha256((key + "/" + worksheet + "/" + name).encode("utf-8")).hexdigest()
        ext = None
        for e, type in MIMETYPES.items():
            path = Web.TMP_DIR + sha_name + e
            if os.path.isfile(path):
                ext = e
                break
        if ext is None:
            item = self.get_item(key, worksheet, name)
            if item is None:
                raise Exception(f"Not found {name}")
            response = requests.get(item.url)
            response.raise_for_status()
            tmp_path = Web.TMP_DIR + sha_name
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
            shutil.move(tmp_path, Web.TMP_DIR + sha_name + ext)

        return sha_name + ext, MIMETYPES[ext]


