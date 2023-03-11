import os, sys, subprocess
from flask import Flask, render_template, request, send_from_directory, redirect, jsonify

from src.Config import Config
from src.Web import Web


app = Flask(__name__)
c = Config("private/photoframe.json")
web = Web(c)

@app.context_processor
def utility_processor():
    return dict(get_locale=web.get_locale)

@app.route('/', methods=['GET'])
def get_index():
    return web.get_index()

@app.route('/sheet/<key>/<worksheet>.csv', methods=['GET'])
def get_sheet_csv(key, worksheet):
    try:
        return "OK\n" + web.prepare(key).get_sheet(worksheet, "csv")
    except Exception as ex:
        return "FAIL\n" + str(ex), 404

@app.route('/sheet/<key>/<worksheet>.json', methods=['GET'])
def get_sheet_json(key, worksheet):
    try:
        return "OK\n" + web.prepare(key).get_sheet(worksheet, "json")
    except Exception as ex:
        return "FAIL\n" + str(ex), 404

@app.route('/img/<key>/<worksheet>/<name>', methods=['GET'])
def download_img(key, worksheet, name):
    try:
        tmp_dir, filename, mime = web.prepare(key).download_img(worksheet, name)
        return send_from_directory(tmp_dir, filename, mimetype=mime)
    except Exception as ex:
        return "FAIL\n" + str(ex), 404

@app.route('/clear/<key>/<worksheet>', methods=['GET'])
def clear_my_dir(key, worksheet):
    try:
        web.prepare(key).clear_my_dir(worksheet)
        return "OK"
    except Exception as ex:
        return "FAIL\n" + str(ex), 404

@app.route('/debug/df', methods=['GET'])
def debug_df():
    try:
        cp = subprocess.run("df -h", capture_output=True)
        return "OK\n" + str(cp.stdout)
    except Exception as ex:
        return "FAIL\n" + str(ex), 404

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=8080)
