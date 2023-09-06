import json
import requests
from loguru import logger


class QbittorrentBase:
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
        return res.json()

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

    def add_trackers(self, hashes, urls):
        url = self.url + "/api/v2/torrents/addTrackers"
        data = {
            "hash": hashes,
            "urls": urls
        }
        res = self.session.post(url, data)
        res.raise_for_status()
        if res.status_code == 200:
            logger.info("add trackers success")
        else:
            logger.error("add trackers failed")

    def remove_trackers(self, hashes, urls):
        url = self.url + "/api/v2/torrents/removeTrackers"
        data = {
            "hash": hashes,
            "urls": urls
        }
        res = self.session.post(url, data)
        res.raise_for_status()
        if res.status_code == 200:
            logger.info("remove trackers success")
        else:
            logger.error("remove trackers failed")

    def get_trackers(self, hashes):
        url = self.url + "/api/v2/torrents/trackers"
        params = {
            "hash": hashes
        }
        res = self.session.get(url, params=params)
        res.raise_for_status()
        return res.json()


class QbittorrentScripts(QbittorrentBase):
    def __init__(self):
        super().__init__()

    def add_new_trackers(self, old_tracker_domain, new_tracker_domain, delete_old=False):
        try:
            res = self.get_maindata()
            torrents = res["torrents"]
            for k, v in torrents.items():
                tracker = v["tracker"]
                if old_tracker_domain in tracker:
                    new_tracker = tracker.replace(old_tracker_domain, new_tracker_domain)
                    self.add_trackers(k, new_tracker)
                    if delete_old:
                        self.remove_trackers(k, tracker)
        except Exception as e:
            logger.error(f"add new trackers failed with error: {e}")

    def add_new_trackers_by_category(self, category, old_tracker_domain, new_tracker_domain):
        try:
            res = self.get_maindata()
            torrents = res["torrents"]
            for k, v in torrents.items():
                _category = v["category"]
                if _category != category:
                    continue
                trackers = self.get_trackers(k)
                for t in trackers:
                    if old_tracker_domain in t["url"]:
                        # check if new tracker has added
                        continue_flag = False
                        for tt in trackers:
                            if new_tracker_domain in tt["url"]:
                                continue_flag = True
                        if continue_flag:
                            continue
                        new_tracker = t["url"].replace(old_tracker_domain, new_tracker_domain)
                        self.add_trackers(k, new_tracker)

        except Exception as e:
            logger.error(f"add new trackers failed with error: {e}")

    def update_uncategorized_torrents(self):
        try:
            res = self.get_maindata()
            torrents = res["torrents"]
            for k, v in torrents.items():
                category = v["category"]
                if not category:
                    tracker = v["tracker"]
                    for _category, _trackers in self.categories.items():
                        for _tracker in _trackers:
                            if _tracker in tracker:
                                self.set_category(k, _category)
        except Exception as e:
            logger.error(f"update uncategorized torrents failed with error: {e}")


if __name__ == '__main__':
    q = QbittorrentScripts()
    q.login()
