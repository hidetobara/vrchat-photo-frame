import unittest
from src.Config import Config

class TestConfig(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_load(self):
        instance = Config("tests/data/hello.json")
        self.assertEqual("hoge", instance.get("seed"))

    def test_put_get(self):
        instance = Config()
        instance.put("hoge", 1)
        instance.put("fuga", "abc")

        self.assertEqual(1, instance.get("hoge"))
        self.assertEqual("abc", instance.get("fuga"))
