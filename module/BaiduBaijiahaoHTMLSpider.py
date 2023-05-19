#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Function: Baidu baijiahao designated authors crawl articles
# Note: This is fetched in HTML, different from the other fetched in json,
# in some cases, the other may not be able to crawl
# Author: 10935336
# Creation date: 2023-05-07
# Modified date: 2023-05-19


import json
import logging
import os
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options


class BaiduBaijiahaoHTMLSpider:
    def __init__(self):
        self.driver = ''
        self.options = ''
        self.authors_list = []
        self.articles_json = ''

    def driver_init(self):
        # Driver setting
        self.options = Options()
        # disable automatic notice
        self.options.set_preference("dom.webdriver.enabled", False)
        self.options.set_preference('useAutomationExtension', False)
        # disable json viewer
        self.options.set_preference("devtools.jsonview.enabled", False)
        # headless mode
        self.options.add_argument('-headless')
        # Driver init
        self.driver = webdriver.Firefox(options=self.options)

    def load_authors(self, authors_list_path):
        try:
            with open(authors_list_path, 'r', encoding='utf-8') as r:
                self.authors_list = json.load(r)
        except Exception as error:
            logging.exception(f'{authors_list_path} read error: {error}')

    def get_articles_list(self, retry_times=3):
        new_list = []
        current_time = int(datetime.now().timestamp())

        self.driver_init()

        for retry in range(retry_times):
            try:
                for author in self.authors_list:
                    try:
                        author_id_l = author['author_id']
                        author_name_l = author['author_name']

                    except Exception as error:
                        logging.exception(f'Cannot find wanted value in authors_list: {error}')

                    self.driver.implicitly_wait(10)

                    url = "https://author.baidu.com/home/" + str(author_id_l)

                    self.driver.get(url)

                    # click "文章" button
                    self.driver.find_element(By.XPATH, '//div[text()="文章"]').click()

                    # scroll down
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                    articles_element = self.driver.find_elements(By.CSS_SELECTOR, "div.sfi-article.real-show-log")

                    for element in articles_element:
                        creation_time = int(element.get_attribute("created_at"))

                        new_list.append(
                            {
                                "title": element.get_attribute("shoubai_c_articleid"),
                                "article_id": element.get_attribute("title"),
                                "author_name": author_name_l,
                                "author_id": author_id_l,
                                "channel_name": "百度百家号",
                                "link": element.get_attribute("url"),
                                "creation_time": str(creation_time),
                                "snapshot_time": str(current_time)
                            }
                        )

                self.articles_json = json.dumps(new_list, ensure_ascii=False)
                # break on success
                if self.articles_json:
                    break

            except Exception as error:
                logging.exception(f"Error on getting or parsing the response: {error}")
                self.articles_json = []

        # Make sure self.articles_json = [] after the number of retries is exceeded and still failed
        if not new_list:
            self.articles_json = []
            logging.warning(f"Max retries is exceeded in {self}")
            logging.warning(f"{self} is set to []")

        try:
            self.driver.close()
        except:
            pass

        try:
            self.driver.quit()
            self.driver.quit()
        except:
            pass

    def start(self, authors_list_path=None):
        if authors_list_path is None:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            authors_list_path = os.path.join(module_dir, '..', 'conf', 'baidubaijiahaohtml_authors_list.json')
        self.load_authors(authors_list_path)
        self.get_articles_list()


if __name__ == "__main__":
    bjh = BaiduBaijiahaoHTMLSpider()
    bjh.start()
    print(bjh.articles_json)
