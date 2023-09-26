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
            logger.info(f"set category {category} success")
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

    def resume(self, hashes):
        url = self.url + "/api/v2/torrents/resume"
        data = {
            "hashes": hashes
        }
        res = self.session.post(url, data)
        res.raise_for_status()
        if res.status_code == 200:
            logger.info("resume torrents success")
        else:
            logger.error("resume torrents failed")

    def pause(self, hashes):
        url = self.url + "/api/v2/torrents/pause"
        data = {
            "hashes": hashes
        }
        res = self.session.post(url, data)
        res.raise_for_status()
        if res.status_code == 200:
            logger.info("pause torrents success")
        else:
            logger.error("pause torrents failed")


class QbittorrentScripts(QbittorrentBase):
    def __init__(self):
        super().__init__()
        self.login()

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

    def update_torrents_category(self):
        try:
            res = self.get_maindata()
            torrents = res["torrents"]
            for k, v in torrents.items():
                category = v["category"]
                if not category.startswith("opencd"):
                    continue
                self.set_category(k, "OpenCD")
        except Exception as e:
            logger.error(f"update torrents category failed with error: {e}")

    def update_uncategorized_torrents(self):
        try:
            res = self.get_maindata()
            torrents = res["torrents"]
            for k, v in torrents.items():
                category = v["category"]
                if category:
                    continue
                trackers = self.get_trackers(k)
                for t in trackers:
                    tracker = t['url']
                    if "http" not in tracker:
                        continue
                    for _category, _trackers in self.categories.items():
                        if any(_tracker in tracker for _tracker in _trackers):
                            self.set_category(k, _category)
                            break
        except Exception as e:
            logger.error(f"update uncategorized torrents failed with error: {e}")

    def resume_torrents_by_storage(self, storage=None):
        try:
            if not storage:
                logger.error("please input storage name")
                return
            res = self.get_maindata()
            torrents = res["torrents"]
            for k, v in torrents.items():
                save_path = v["save_path"]
                if save_path.startswith(f'{storage}:\\'):
                    self.resume(k)
        except Exception as e:
            logger.error(f"resume torrents by storage failed with error: {e}")

    def stop_torrents_by_storage(self, storage=None):
        try:
            if not storage:
                logger.error("please input storage name")
                return
            res = self.get_maindata()
            torrents = res["torrents"]
            for k, v in torrents.items():
                save_path = v["save_path"]
                if save_path.startswith(f'{storage}:\\'):
                    self.pause(k)
        except Exception as e:
            logger.error(f"stop torrents by storage failed with error: {e}")


if __name__ == '__main__':
    q = QbittorrentScripts()
    # q.stop_torrents_by_storage("E")
    # q.resume_torrents_by_storage("E")
    q.update_uncategorized_torrents()
    # q.update_torrents_category()
