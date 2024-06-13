import os, sys, subprocess, traceback
from flask import Flask, render_template, request, send_from_directory, redirect, jsonify

from src.Config import Config
from src.Web import Web
from src.BucketImage import BucketImage


app = Flask(__name__)
web = Web(Config("private/photoframe.json"))

@app.after_request
def set_response_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/', methods=['GET'])
def get_index():
    return web.view_index()

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
        print("ERROR", ex, traceback.format_exc())
        return "FAIL\n" + str(ex), 404

@app.route('/img/<key>/<worksheet>/<id>', methods=['GET'])
def download_img(key, worksheet, id):
    try:
        tmp_dir, filename, mime = web.prepare(key).download_img(worksheet, id)
        return send_from_directory(tmp_dir, filename, mimetype=mime)
    except Exception as ex:
        print("ERROR", ex, traceback.format_exc())
        return "FAIL\n" + str(ex), 404

@app.route('/clear/<key>/<worksheet>', methods=['GET'])
def clear_my_dir(key, worksheet):
    try:
        web.prepare(key).clear_my_dir(worksheet)
        return "OK"
    except Exception as ex:
        return "FAIL\n" + str(ex), 404

##### 管理 #####
@app.route('/manage/<key>/<worksheet>/', methods=['GET'])
def manage_images(key, worksheet):
    action = request.args.get("action")
    format = request.args.get("format")

    message = None
    items = web.prepare(key).get_sheet(worksheet, None)
    if action == "update":
        web.update_bucket(worksheet, items)
        message = "更新しました"
    if format == "json":
        return [item.to_dict() for item in items]

    return web.view_manage(worksheet, items, message=message)

##### デバッグ #####
@app.route('/debug/ls', methods=['GET'])
def debug_ls():
    try:
        cp = subprocess.run(["ls", "/app/tmp/"], capture_output=True, text=True)
        return "OK\n" + str(cp.stdout)
    except Exception as ex:
        return "FAIL\n" + str(ex), 404

@app.route('/debug/df', methods=['GET'])
def debug_df():
    try:
        cp = subprocess.run(["df", "-h"], capture_output=True, text=True)
        return "OK\n" + str(cp.stdout)
    except Exception as ex:
        return "FAIL\n" + str(ex), 404

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)
