import json
import requests
from loguru import logger


class QB:
    def __init__(self):
        self.config: dict = {}
        self.url: str = ""
        self.username: str = ""
        self.password: str = ""
        self.categories: dict = {}
        self.load_file()
        self.session = requests.session()

    def load_file(self):
        try:
            with open("config.json", encoding="utf-8") as f:
                config = json.load(f)
            self.url = config.get("url")
            self.username = config.get("username")
            self.password = config.get("password")
            self.categories = config.get("categories")
        except FileNotFoundError:
            logger.error("file not exist")

    def login(self):
        url = self.url + "/api/v2/auth/login"
        data = {
            "username": self.username,
            "password": self.password
        }
        res = self.session.post(url, data)
        res.raise_for_status()
        if res.status_code == 200:
            logger.info("login success")
        else:
            logger.error("login failed")

    def get_maindata(self):
        url = self.url + "/api/v2/sync/maindata"
        params = {
            "rid": 0
        }
        res = self.session.get(url, params=params)
        res.raise_for_status()
        res_json = res.json()
        torrents = res_json["torrents"]
        for k, v in torrents.items():
            category = v["category"]
            if not category:
                tracker = v["tracker"]
                for _category, _trackers in self.categories.items():
                    for _tracker in _trackers:
                        if _tracker in tracker:
                            self.set_category(k, _category)
                # logger.debug(f"hash: {k}\ttracker: {v['tracker']}")

    def set_category(self, hashes, category):
        url = self.url + "/api/v2/torrents/setCategory"
        data = {
            "hashes": hashes,
            "category": category
        }
        res = self.session.post(url, data)
        res.raise_for_status()
        if res.status_code == 200:
            logger.info("set category success")
        else:
            logger.error("set category failed")


if __name__ == '__main__':
    q = QB()
    q.login()
    q.get_maindata()
