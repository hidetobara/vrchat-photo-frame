import os, sys, subprocess, traceback, json
from flask import Flask, render_template, request, send_from_directory, redirect, jsonify

from src.Config import Config
from src.Web import Web
from src.BucketImage import BucketImage

# Drive読み取りで必要か？
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/app/private/sync-frame-runner.json"

app = Flask(__name__)
web = Web(Config("private/syncframe.json"))

@app.after_request
def set_response_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/', methods=['GET'])
def get_index():
    return web.view_index()

@app.route('/sheet/<key>/<worksheet>.json', methods=['GET'])
def get_sheet_json(key, worksheet):
    try:
        return web.prepare(key).get_sheet_json(worksheet)
    except Exception as ex:
        print("ERROR", ex, traceback.format_exc())
        return json.dumps({"status": "FAIL", "reason": str(ex)})

@app.route('/img/<key>/<worksheet>/<id>', methods=['GET'])
def download_img(key, worksheet, id):
    try:
        tmp_dir, filename, mime = web.prepare(key).download_img(worksheet, id)
        return send_from_directory(tmp_dir, filename, mimetype=mime)
    except Exception as ex:
        print("ERROR", ex, traceback.format_exc())
        return "FAIL\n" + str(ex), 404

@app.route('/delete/<key>/<worksheet>', methods=['GET'])
def delete_work_objects(key, worksheet):
    try:
        web.prepare(key).delete_work_objects(worksheet)
        return "OK"
    except Exception as ex:
        return "FAIL\n" + str(ex), 404

@app.route('/delete/<key>/<worksheet>/<id>', methods=['GET'])
def delete_object(key, worksheet, id):
    try:
        web.prepare(key).delete_object(worksheet, id)
        if url := web.goto(worksheet):
            return url
        return "OK"
    except Exception as ex:
        return "FAIL\n" + ex.__class__.__name__ + "\n" + str(ex), 404

@app.route('/upload/<key>/<worksheet>/<id>', methods=['GET'])
def upload_object(key, worksheet, id):
    try:
        web.prepare(key).upload_object(worksheet, id)
        if url := web.goto(worksheet):
            return url
        return "OK"
    except Exception as ex:
        return "FAIL\n" + ex.__class__.__name__ + "\n" + str(ex), 404

##### 管理 #####
@app.route('/manage/<key>/<worksheet>/', methods=['GET'])
def manage_images(key, worksheet):
    message = request.args.get("message")
    items = web.prepare(key).get_sheet(worksheet)
    return web.view_manage(key, worksheet, items, message=message)

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
