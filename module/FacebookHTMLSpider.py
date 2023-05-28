#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Function: Facebook designated public page crawl post
# Note: Must log in
# Your Facebook account settings must be set to the following values：
# Facebook language: "中文(简体)" or "English (US)"
# Formats for dates, times and numbers: "中国(简体中文)" or "US (English)"
# Otherwise, the obtained creation time will be 0
# Author: 10935336
# Creation date: 2023-05-12
# Modified date: 2023-05-28


import json
import logging
import os
import re
import time
from datetime import datetime

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options


class FacebookHTMLSpider:
    def __init__(self):
        self.driver = ''
        self.options = ''
        self.authors_list = []
        self.account_list = []
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
        #self.options.add_argument('-headless')
        # Driver init
        self.driver = webdriver.Firefox(options=self.options)

    def load_authors(self, authors_list_path):
        try:
            with open(authors_list_path, 'r', encoding='utf-8') as r:
                self.authors_list = json.load(r)
        except Exception as error:
            logging.exception(f'{authors_list_path} read error: {error}')

    def load_account(self, account_list_path):
        try:
            with open(account_list_path, 'r', encoding='utf-8') as r:
                self.account_list = json.load(r)
        except Exception as error:
            logging.exception(f'{account_list_path} read error: {error}')

    def get_articles_list(self, retry_times=3):
        new_list = []
        current_time = int(datetime.now().timestamp())

        self.driver_init()

        def parse_time(time_str):
            """
            :param time_str: time_str
            :return: float timestamp; otherwise, return "0";
            """
            # get the current time
            now = time.localtime()
            # match the format of "M月D日HH:mm"
            match = re.search(r"(\d+?)月(\d+?)日(?:\s?(\d+?):(\d+?))?", time_str)
            if match:
                # get the month, day, hour and minute from the match
                month = int(match.group(1))
                day = int(match.group(2))
                hour = int(match.group(3)) if match.group(3) else 0
                minute = int(match.group(4)) if match.group(4) else 0
                # create a time struct with the same year as now and the matched values
                t = time.struct_time((now.tm_year, month, day, hour, minute, 0, 0, 0, 0))
                # return the timestamp
                return time.mktime(t)
            # match the format of "X天" or "Xd"
            match = re.search(r"(\d+)(天|d)", time_str)
            if match:
                # get the days from the match
                days = int(match.group(1))
                # subtract the days from the current timestamp
                return time.time() - days * 86400
            # match the format of "May 15 at 6:43 PM" or "May 15 at 18:43"
            match = re.search(r"(\w+) (\d+) at (\d+):(\d+) ?(AM|PM)?", time_str)
            if match:
                # get the month name, day, hour, minute and AM/PM from the match
                month_name = match.group(1)
                day = int(match.group(2))
                hour = int(match.group(3))
                minute = int(match.group(4))
                am_pm = match.group(5)
                # convert the month name to a number
                month_names = ["January", "February", "March", "April", "May", "June",
                               "July", "August", "September", "October", "November", "December"]
                month = month_names.index(month_name) + 1
                # adjust the hour according to AM/PM
                if am_pm == "PM" and hour < 12:
                    hour += 12
                elif am_pm == "AM" and hour == 12:
                    hour = 0
                # create a time struct with the same year as now and the matched values
                t = time.struct_time((now.tm_year, month, day, hour, minute, 0, 0, 0, 0))
                # return the timestamp
                return time.mktime(t)
            # match the format of "April 7"
            match = re.search(r"(\w+) (\d+)", time_str)
            if match:
                # get the month name and day from the match
                month_name = match.group(1)
                day = int(match.group(2))
                # convert the month name to a number
                month_names = ["January", "February", "March", "April", "May", "June",
                               "July", "August", "September", "October", "November", "December"]
                month = month_names.index(month_name) + 1
                # create a time struct with the same year as now and the matched values
                t = time.struct_time((now.tm_year, month, day, 0, 0, 0, 0, 0, 0))
                # return the timestamp
                return time.mktime(t)
            # match the format of "X小时" or "Xh"
            match = re.search(r"(\d+)(小时|h)", time_str)
            if match:
                # get the hours from the match
                hours = int(match.group(1))
                # subtract the hours from the current timestamp
                return time.time() - hours * 3600
            # match the format of "X分钟" or "Xm"
            match = re.search(r"(\d+)(分钟|m)", time_str)
            if match:
                # get the minutes from the match
                minutes = int(match.group(1))
                # subtract the minutes from the current timestamp
                return time.time() - minutes * 60
            # match the format of "YYYY年MM月DD日"
            match = re.search(r"(\d+)年(\d+)月(\d+)日", time_str)
            if match:
                # get the year, month and day from the match
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
                # create a time struct with the matched values
                t = time.struct_time((year, month, day, 0, 0, 0, 0, 0, 0))
                # return the timestamp
                return time.mktime(t)
            # otherwise, return "0"
            return "0"

        def link_process(link):
            """
            :param link: raw_facebook_link;
            :return: new_link, post_ID; otherwise, return None, "0";
            """
            # match the format A
            match = re.search(r"https://www.facebook.com/(\w+)/posts/(\d+)\?", link)
            if match:
                # get the page name and the post-ID from the match
                page = match.group(1)
                post_id = match.group(2)
                # join the page name and the post-ID with "/" to get the new link
                new_link = "https://www.facebook.com/" + page + "/posts/" + post_id
                # return the new link and the post-ID
                return new_link, post_id
            # match the format B
            match = re.search(r"https://www.facebook.com/permalink.php\?story_fbid=(\w+)&id=(\w+)", link)
            if match:
                # get the story fbid and the id from the match
                story_fbid = match.group(1)
                id = match.group(2)
                post_id = story_fbid + "_" + id
                # join the story fbid and the id with "/" to get the new link
                new_link = "https://www.facebook.com/permalink.php?story_fbid=" + story_fbid + "&id=" + id
                # return the new link and the story fbid as the post-ID
                return new_link, post_id
            # match the format C
            match = re.search(r"https://www.facebook.com/([\w\.]+)/photos/(a\.\d+/\d+)/", link)
            if match:
                # get the page name and the photo ID from the match
                page = match.group(1)
                photo_id = match.group(2)
                # join the page name and the photo ID with "/" to get the new link
                new_link = "https://www.facebook.com/" + page + "/photos/" + photo_id + "/"
                # return the new link and the photo ID as the post-ID
                return new_link, photo_id
            # match the format D
            match = re.search(r"https://www.facebook.com/watch/\?v=(\d+)", link)
            if match:
                # get the video ID from the match
                video_id = match.group(1)
                # join the video ID with "/" to get the new link
                new_link = "https://www.facebook.com/watch/?v=" + video_id
                # return the new link and the video ID as the post-ID
                return new_link, video_id
            # match the format E
            match = re.search(r"https://www.facebook.com/groups/(\d+)/\?multi_permalinks=(\d+)", link)
            if match:
                # get the group ID and the multi permalink from the match
                group_id = match.group(1)
                multi_permalink = match.group(2)
                # join the group ID and the multi permalink with "/" to get the new link
                new_link = "https://www.facebook.com/groups/" + group_id + "/?multi_permalinks=" + multi_permalink
                # join the group ID and the multi permalink with "_" to get the post-ID
                post_id = group_id + "_" + multi_permalink
                # return the new link and the post-ID
                return new_link, post_id
            # match the format F
            match = re.search(r"https://www.facebook.com/([\w\.]+)/posts/([\w-]+):(\w+)", link)
            if match:
                # get the page name, the first part and the second part of the post-ID from the match
                page = match.group(1)
                first_part = match.group(2)
                second_part = match.group(3)
                post_id = first_part + "_" + second_part
                # join the page name, first part and second part with "/" and ":" to get the new link
                new_link = "https://www.facebook.com/" + page + "/posts/" + first_part + ":" + second_part
                return new_link, post_id
            # match the format G
            match = re.search(r"https://www.facebook.com/([\w\.]+)/posts/([\w-]+)\?", link)
            if match:
                # get the page name and the post-ID from the match
                page = match.group(1)
                post_id = match.group(2)
                # join the page name and the post-ID with "/" to get the new link
                new_link = "https://www.facebook.com/" + page + "/posts/" + post_id
                # return the new link and the post-ID
                return new_link, post_id
            # otherwise, return None, "0"
            return None, "0"

        def facebook_login():
            login_url = "https://www.facebook.com/"

            for account in self.account_list:
                try:
                    username = account['username']
                    password = account['password']

                    self.driver.get(login_url)
                    self.driver.implicitly_wait(10)

                    element_email = self.driver.find_element(By.ID, 'email')
                    element_email.send_keys(username)

                    time.sleep(1)

                    element_pass = self.driver.find_element(By.ID, 'pass')
                    element_pass.send_keys(password)

                    login_button = self.driver.find_element(By.NAME, 'login')
                    login_button.click()

                except Exception as error:
                    logging.exception(f'Login Facebook failed: {error}')

        facebook_login()

        for retry in range(retry_times):
            try:
                for author in self.authors_list:
                    try:
                        author_id_l = author['author_id']
                        author_name_l = author['author_name']

                    except Exception as error:
                        logging.exception(f'Cannot find wanted value in authors_list: {error}')

                    self.driver.implicitly_wait(10)

                    url = "https://www.facebook.com/" + str(author_id_l)

                    self.driver.get(url)

                    time.sleep(5)

                    # scroll down twice
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                    time.sleep(5)

                    page_source = self.driver.page_source
                    soup = BeautifulSoup(page_source, "html.parser")
                    posts = soup.find_all('div', {'class': 'x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z'})

                    for post in posts:
                        text_div = post.find("div", {"class": "xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs x126k92a"})
                        if text_div is not None:
                            text = text_div.text
                            clean_text = re.sub(r'http\S+', '', text)
                        else:
                            clean_text = "The post appears to have no text\n此帖子无文本"

                        time_link_div = post.find("a", {
                            "class": "x1i10hfl xjbqb8w x6umtig x1b1mbwd xaqea5y xav7gou x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1heor9g xt0b8zv xo1l8bm"})
                        raw_facebook_link = time_link_div["href"]
                        clean_link, article_id = link_process(raw_facebook_link)

                        time_str = time_link_div["aria-label"]
                        timestamp = int(parse_time(time_str))

                        new_list.append(
                            {
                                "title": str(clean_text),
                                "article_id": str(article_id),
                                "author_name": author_name_l,
                                "author_id": author_id_l,
                                "channel_name": "Facebook",
                                "link": clean_link,
                                "creation_time": str(timestamp),
                                "snapshot_time": str(current_time)
                            }
                        )

                self.articles_json = json.dumps(new_list, ensure_ascii=False)
                # break on success
                if self.articles_json:
                    break

            except Exception as error:
                logging.exception(f"Error getting or parsing the response: {error}")
                self.articles_json = []

        # Make sure self.articles_json = [] after the number of retries is exceeded and still failed
        if not new_list:
            self.articles_json = []
            logging.warning(f"Max retries is exceeded in {self}")
            logging.warning(f"{self} is set to []")

        try:
            self.driver.close()
        except Exception:
            pass

        try:
            self.driver.quit()
            self.driver.quit()
        except Exception:
            pass

    def start(self, authors_list_path=None, account_list_path=None):
        if authors_list_path is None:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            authors_list_path = os.path.join(module_dir, '..', 'conf', 'facebookhtml_authors_list.json')
        if account_list_path is None:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            account_list_path = os.path.join(module_dir, '..', 'conf', 'facebookhtml_account_list.json')
        self.load_account(account_list_path)
        self.load_authors(authors_list_path)
        self.get_articles_list()


if __name__ == "__main__":
    fb = FacebookHTMLSpider()
    fb.start()
    print(fb.articles_json)
