import os, sys, hashlib
import requests
from flask import Flask, render_template, request, send_from_directory, redirect, jsonify

from src.Config import Config
from src.Web import Web

MIMETYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif"}

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
        cells = os.path.splitext(name)
        ext = cells[1]
        mimetype = MIMETYPES[ext]
        tmp_path = "/tmp/" + sha_name + ext
        if not os.path.isfile(tmp_path):
            item = web.get_item(key, worksheet, name)
            if item is None:
                raise Exception(f"Not found {name}")
            response = requests.get(item.url)
            with open(tmp_path, "wb") as f:
                f.write(response.content)
        return send_from_directory("/tmp", sha_name + ext, mimetype=f"image/{mimetype}")
    except Exception as ex:
        return str(ex), 404


if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=8080)
