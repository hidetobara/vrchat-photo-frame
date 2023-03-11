import unittest, json
from src.Web import Web
from src.Config import Config


class TestWeb(unittest.TestCase):
    @property
    def KEY(self):
        return "1HdYaxkIsX88SFNo3ZrFgHlH4gpzfHBY2e4sAwniANR0"

    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_get_item(self):
        c = Config("tests/data/hello.json")
        web = Web(c)

        self.assertIsNotNone(web.prepare(self.KEY).get_item("test", "orchid"))
        self.assertIsNone(web.prepare(self.KEY).get_item("test", "aaaaa"))

    def test_get_sheet(self):
        c = Config("tests/data/hello.json")
        web = Web(c).testing()

        items = json.loads(web.prepare(self.KEY).get_sheet("test", "json"))
        self.assertTrue("name" in items[0])
        self.assertTrue("url" in items[0])
        self.assertTrue("title" in items[0])

    def test_download_img(self):
        c = Config("tests/data/hello.json")
        web = Web(c).testing()

        o = web.prepare(self.KEY).download_img("test", "orchid")
        self.assertEqual("image/jpeg", o[2])

        with self.assertRaises(Exception):
            o = web.prepare(self.KEY).download_img("test", "aaaaa")
        with self.assertRaises(Exception):
            o = web.prepare(self.KEY).download_img("aaaaa", "orchid")

    def test_clear(self):
        c = Config("tests/data/hello.json")
        web = Web(c).testing()
        self.assertTrue(web.prepare(self.KEY).clear_my_dir("test"))
