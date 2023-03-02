import os, sys, hashlib, shutil
import requests
from flask import Flask, render_template, request, send_from_directory, redirect, jsonify
from PIL import Image

from src.Config import Config
from src.Web import Web

MIMETYPES = {".png": "image/png", ".jpg": "image/jpeg"}

app = Flask(__name__)
c = Config("private/photoframe.json")
web = Web(c)

@app.context_processor
def utility_processor():
    return dict(get_locale=web.get_locale)

@app.route('/', methods=['GET'])
def get_index():
    return web.get_index()

@app.route('/sheet', methods=['GET'])
def get_sheet():
    return web.get_sheet(request.args.get('key', ''), request.args.get('worksheet', 'main'))

@app.route('/img/<key>/<worksheet>/<name>')
def download_img(key, worksheet, name):
    try:
        sha_name = hashlib.sha256((key + "/" + worksheet + "/" + name).encode("utf-8")).hexdigest()
        ext = None
        for e, type in MIMETYPES.items():
            path = "/tmp/" + sha_name + e
            if os.path.isfile(path):
                ext = e
                break
        if ext is None:
            item = web.get_item(key, worksheet, name)
            if item is None:
                raise Exception(f"Not found {name}")
            response = requests.get(item.url)
            response.raise_for_status()
            tmp_path = "/tmp/" + sha_name
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
            shutil.move(tmp_path, "/tmp/" + sha_name + ext)        

        return send_from_directory("/tmp", sha_name + ext, mimetype=MIMETYPES[ext])
    except Exception as ex:
        return str(ex), 404


if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=8080)
