#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Function: Douyin designated authors crawl videos
# Note: risk control is very strict
# Author: 10935336
# Creation date: 2023-04-23
# Modified date: 2023-06-06

import json
import logging
import os
import re
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service


class DouyinSpider:
    def __init__(self):
        self.driver = ''
        self.options = ''
        self.authors_list = []
        self.videos_json = ''
        self.articles_json = ''

    def driver_init(self):
        # Driver setting
        self.options = Options()
        # Disable automatic notice
        self.options.set_preference("dom.webdriver.enabled", False)
        self.options.set_preference('useAutomationExtension', False)
        # Disable json viewer
        self.options.set_preference("devtools.jsonview.enabled", False)
        # Headless mode
        self.options.add_argument('-headless')
        # Driver init
        self.driver = webdriver.Firefox(options=self.options, service=Service(log_path=os.devnull))

    def load_authors(self, authors_list_path):
        try:
            with open(authors_list_path, 'r', encoding='utf-8') as r:
                self.authors_list = json.load(r)
        except Exception as error:
            logging.exception(f'{authors_list_path} read error: {error}')

    def get_videos_list(self, retry_times=3):
        new_list = []
        current_time = int(time.time())

        for retry in range(retry_times):
            try:
                self.driver_init()
                for author in self.authors_list:
                    # read author
                    try:
                        author_id_l = author['author_id']
                        author_name_l = author['author_name']
                    except Exception as error:
                        logging.exception(f'Cannot find wanted value in authors_list: {error}')

                    url = "https://www.douyin.com/user/" + author_id_l

                    # do not use this, this will let you wait forever
                    # self.driver.implicitly_wait(5)

                    self.driver.get(url=url)

                    time.sleep(5)

                    # Close the login popup
                    try:
                        self.driver.find_element(By.CSS_SELECTOR, 'div.dy-account-close').click()
                    except:
                        pass

                    # scroll down
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                    elements = self.driver.find_elements(By.XPATH, '//a[@class="B3AsdZT9 chmb2GX8"]')
                    for element in elements:
                        # Skip top pinning
                        try:
                            if element.find_element(By.XPATH, './/span[@class="SlSbcMqT cAbnSEfo"]'):
                                continue
                        except:
                            pass

                        title_element = element.find_element(By.XPATH, './/p[@class="__0w4MvO"]')
                        title = title_element.text
                        link = element.get_attribute('href')

                        article_id_match = re.search(r'/(video|note)/(\d+)', link)
                        if article_id_match:
                            article_id = article_id_match.group(2)
                        else:
                            article_id = None

                        new_list.append(
                            {
                                "title": title,
                                "article_id": article_id,
                                "author_name": author_name_l,
                                "author_id": author_id_l,
                                "channel_name": "抖音",
                                "link": link,
                                "creation_time": "0",
                                "snapshot_time": str(current_time)
                            }
                        )

                self.videos_json = json.dumps(new_list, ensure_ascii=False)
                # break on success
                if self.videos_json:
                    break

            except Exception as error:
                logging.exception(f"Error getting or parsing the response: {error}")
                self.videos_json = []

        # Make sure self.articles_json = [] after the number of retries is exceeded and still failed
        if not new_list:
            self.videos_json = []
            logging.warning(f"Max retries is exceeded in {self}")
            logging.warning(f"{self} is set to []")

        # Make sure selenium exits, but doesn't always work
        try:
            self.driver.close()
        except Exception as error:
            pass

        try:
            self.driver.quit()
        except Exception as error:
            pass

    def videos_list_to_articles_list(self):
        # well douyin has no article for now, lazy to do special handling
        self.articles_json = self.videos_json

    def start(self, authors_list_path=None):
        if authors_list_path is None:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            authors_list_path = os.path.join(module_dir, '..', 'conf', 'douyin_authors_list.json')
        self.load_authors(authors_list_path)
        self.get_videos_list()
        self.videos_list_to_articles_list()


if __name__ == "__main__":
    dy = DouyinSpider()
    dy.start()
    print(dy.articles_json)
