import os,sys
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

@app.route('/sheet', methods=['GET'])
def get_sheet():
    return web.get_sheet(request.args.get('key', ''), request.args.get('worksheet', 'main'))

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=8080)
