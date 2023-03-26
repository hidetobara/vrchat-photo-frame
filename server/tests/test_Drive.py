import unittest, json
from src.Drive import Item, Drive, Sheet


class TestWeb(unittest.TestCase):
    def test_drive(self):
        i = Item(["drive", "https://drive.google.com/file/d/15pwC4h22quaMrWwB6dVoj9bV_UpWr4y4/view?usp=sharing"])
        self.assertEqual("15pwC4h22quaMrWwB6dVoj9bV_UpWr4y4", i.get_drive_key())

    def test_photos(self):
        with self.assertRaises(Exception):
            i = Item("photos", "https://photos.app.goo.gl/crgAjtqeWCSJHWAi8")
            i.get_photos_key()

    def test_others(self):
        i = Item(["twitter", "https://pbs.twimg.com/media/Fq7KskrakAAdtWj?format=jpg", "abc"])
        self.assertTrue(i.is_valid())