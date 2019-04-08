import time

import toml
from loguru import logger

from .boilerkey import BoilerKey
from .purdue_api import PurdueApi


class AutoReg:
    def __init__(self, config_path, notification_callback):
        with open(config_path) as f:
            config = toml.load(f)

        self._validate_config(config)
        self.config = config
        self.api = PurdueApi(self.config['username'], None)
        self.notify = notification_callback if notification_callback else lambda x: x

    def _validate_config(self, config):
        pass

    def display_current_selection(self):
        for i, class_collection in enumerate(self.config['tracked_crns']):

            print(f"--- Class collection {i}:")
            for class_ in class_collection:
                res = self.fetch_class_info(class_)
                print(res['title'])
                print(res['restrictions'])
                print(f"Capacity: {res['seats_capacity']}")
                print(f"Free: {res['seats_remaining']}")

                if res['seats_remaining'] > 0:
                    logger.warning(f"Class {class_} is currently available")

                print()

    def fetch_class_info(self, crn):
        res = self.api.getSectionDataByCRN(self.config['semester_id'], crn)
        return res

    def start(self):
        self.display_current_selection()
        self._start_update_loop()

    def _start_update_loop(self):
        while True:
            for class_collection in self.config['tracked_crns']:
                available, space = self._check_class_collection(class_collection)
                if available:
                    logger.info("Class collection available to register ", class_collection)
                    logger.info("Spaces: ", space)
                else:
                    pass

            time.sleep(self.config['update_freq'])

    def _check_class_collection(self, class_collection):
        available = True
        space = {}
        for class_ in class_collection:
            res = self.fetch_class_info(class_)
            if res['seats_remaining'] <= 0:
                available = False
                space[class_] = res['seats_remaining']
        
        return available, space


