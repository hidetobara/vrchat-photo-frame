import os, hashlib, shutil, requests, json, glob
from flask import Flask, render_template, request, send_from_directory, redirect, jsonify
from PIL import Image

from src.Env import Env
from src.Config import Config
from src.Item import Item
from src.Drive import Drive, Sheet, Photos
from src.BucketImage import BucketImage

MIMETYPES = {".png": "image/png", ".jpg": "image/jpeg"}
env = Env()

class Web:
    TMP_DIR = "/app/tmp/"
    PUBLIC_DOMAIN = "https://syncframe.pictures"

    def __init__(self, config: Config):
        self.limits = config.get("limits", {})
        self.seed = env.seed
        self.key = None
        self.sheet = None
        self.is_logging = True
        self.bucket = BucketImage()

    def testing(self):
        self.is_logging = False
        return self

    def __del__(self):
        if self.sheet is not None:
            self.sheet.close()
            self.sheet = None

    @property
    def owner(self):
        return self.sheet.owner

    def gen_hash(self, s):
        return hashlib.md5((s + "|" + self.seed).encode("utf-8")).hexdigest()

    def view_index(self):
        context = {}
        return render_template('top.html', **context)
    
    def get_frame_used(self):
        return self.bucket.count_owner_objects(self.owner)
    
    def view_manage(self, key, worksheet, items, message=None):
        context = {
            "key": key,
            "worksheet": worksheet,
            "items": items,
            "frame_used": self.get_frame_used(),
            "frame_limit": self.get_frame_limit(),
            "message": message,
        }
        return render_template('manage.html', **context)

    def prepare(self, key: str):
        self.key = key
        if self.sheet is None:
            self.sheet = Sheet(key).prepare()
        if self.sheet.owner is None:
            raise Exception("This sheet has No owner")
        return self

    def get_frame_limit(self):
        if self.owner in self.limits:
            return self.limits[self.owner]
        return env.frame_limit

    def get_item(self, worksheet: str, id: str):
        table = self.sheet.load(worksheet)
        if id in table:
            return table[id]
        return None

    def get_public_url(self, worksheet: str, id: str):
        workdir = self.bucket.get_work_dir(self.owner, self.key, worksheet)
        return f"{self.PUBLIC_DOMAIN}/images/{workdir}/{id}"

    def get_sheet(self, worksheet: str):
        if self.is_logging:
            print("KEY=", self.key, "OWNER=", self.owner)
        table = self.sheet.load(worksheet)
        items = list(table.values())
        for item in items:
            item.public_url = self.get_public_url(worksheet, item.id)
        return items

    def get_sheet_csv(self, worksheet: str):
        items = self.get_sheet(worksheet)
        lines = []
        for item in items:
            lines.append(",".join(item.to_csv()))
        return "\n".join(lines)
    
    def get_sheet_json(self, worksheet: str):
        items = self.get_sheet(worksheet)
        box = []
        for item in items:
            box.append(item.to_dict())
        frame = {
            "limit": self.get_frame_limit(),
            "used": self.get_frame_used(),
        }
        return json.dumps({"status":"OK", "frame": frame, "items": box}, ensure_ascii=False)
        
    def download_img(self, worksheet: str, id: str):
        item = self.get_item(worksheet, id)
        if item is None:
            raise Exception(f"Not found {id}.")

        sha_folder = self.gen_hash(self.owner)
        sha_name = self.gen_hash(worksheet + "/" + id + ":" + item.url)

        tmp_dir = Web.TMP_DIR + sha_folder + "/"
        os.makedirs(tmp_dir, exist_ok=True)

        ext = None
        for e, type in MIMETYPES.items():
            path = tmp_dir + sha_name + e
            if os.path.isfile(path):
                ext = e
                break
        if ext is None:
            # キャッシュが存在しない場合
            tmp_path = tmp_dir + sha_name
            self.download_from_origin(item, tmp_path)
            try:
                with Image.open(tmp_path) as im:
                    if im.size[0] > 2048 or im.size[1] > 2048:
                        raise Exception("Too large image.")
                    if im.format == "PNG":
                        ext = ".png"
                    if im.format == "JPEG":
                        ext = ".jpg"
                    if ext is None:
                        raise Exception("Unknown image format.")
            except Exception as ex:
                os.remove(tmp_path)
                raise ex
            shutil.move(tmp_path, tmp_dir + sha_name + ext)

        return tmp_dir, sha_name + ext, MIMETYPES[ext]
    
    def download_from_origin(self, item: Item, path):
        if item.get_drive_key():
            d = Drive(item.get_drive_key()).prepare()
            d.download(path)
            return
        if item.get_photos_key():
            raise Exception("Google Photos is unsupported.")
            #d = Photos(item.get_photos_key()).prepare()
            #d.download(path)
            return
        
        response = requests.get(item.url)
        response.raise_for_status()
        with open(path, "wb") as f:
            f.write(response.content)

    def delete_work_objects(self, worksheet: str):
        self.bucket.delete_work_objects(self.owner, self.key, worksheet)
    
    def delete_object(self, worksheet: str, id: str):
        self.bucket.delete_object(self.owner, self.key, worksheet, id)

    def upload_object(self, worksheet: str, id :str):
        count = self.get_frame_used()
        if count >= self.get_frame_limit():
            return False
        item = self.get_item(worksheet, id)
        if not item:
            return False
        tmp_dir, filename, _ = self.download_img(worksheet, item.id)
        with open(tmp_dir + "/" + filename, mode="rb") as f:
            self.bucket.upload(self.owner, self.key, worksheet, item.id, f)
        return True

    def goto(self, worksheet: str):
        goto = request.args.get("goto")
        if goto:
            return redirect(f"/manage/{self.key}/{worksheet}")
        return None
