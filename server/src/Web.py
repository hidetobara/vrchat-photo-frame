import os,sys
from flask import Flask, render_template, request, send_from_directory, redirect, jsonify

from src.Config import Config
from src.Sheet import Sheet


class Web:

    def __init__(self, config: Config):
        self.config = config

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

    def get_sheet(self, key: str, worksheet="main"):
        try:
            sheet = Sheet(key)
            table = sheet.load(worksheet)
            lines = ["OK"]
            for value in table.values():
                lines.append(",".join(value.to_csv()))
            return "\n".join(lines)
        except Exception as ex:
            return "ERROR\n" + str(ex)

