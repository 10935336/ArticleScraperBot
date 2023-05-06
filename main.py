#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Function: Obtain and compare the list of old and new articles, and push the latest articles
# Author: 10935336
# Creation date: 2023-04-20
# Modified date: 2023-05-06

import importlib
import json
import logging
import os
from datetime import datetime


def load_spiders_list(spiders_list_path=r".\conf\spider_list.json"):
    try:
        with open(spiders_list_path, 'r', encoding='utf-8') as r:
            spiders_list = json.load(r)
            r.close()
            return spiders_list
    except Exception as error:
        logging.exception(f'{spiders_list_path} read error: {error}')


def spiders_init(spiders_list):
    try:
        objects_list = []

        for spider in spiders_list:
            try:
                spider_id_l = spider['spider_id']
                object_name_l = spider['object_name']
            except Exception as error:
                logging.exception(f'Cannot find wanted value in spiders_list: {error}')

            # dynamic load module
            try:
                # module dir
                module = importlib.import_module('module.' + spider_id_l)
            except Exception as error:
                logging.exception(f'Cannot load module: {error}')

            # instantiating the object
            try:
                spider_class = getattr(module, spider_id_l)
                globals()[object_name_l] = spider_class()
                objects_list.append(globals()[object_name_l])
            except Exception as error:
                logging.exception(f'Instantiating the object error: {error}')

        return objects_list
    except Exception as error:
        logging.exception(f'Unexpected error 1: {error}')


def get_all_articles_list(objects_list):
    all_list = []
    try:
        for object_ in objects_list:
            logging.info(f"Now loading {object_}")
            object_.start()
            if object_.articles_json:
                all_list.append(json.loads(object_.articles_json))
    except Exception as error:
        logging.exception(f'Unexpected error 2: {error}')

    return json.dumps(all_list, ensure_ascii=False)


def get_new_articles(objects_list, previous_articles_file_path='previous_articles.json'):
    """
    Get new articles from the given list of articles and save the new articles list to a file.

    :return: List of new articles found in the given objects_list.
    """

    try:
        # Convert a JSON string to a Python list
        current_articles_lists = json.loads(get_all_articles_list(objects_list))

        # If the previous_articles_file_path file exists, read the JSON string in the file as json list
        if os.path.exists(previous_articles_file_path):
            try:
                with open(previous_articles_file_path, 'r', encoding='utf-8') as f:
                    previous_articles_lists = json.load(f)
                    previous_authors_ids = set()

                    for current_article_list in previous_articles_lists:
                        for current_article in current_article_list:
                            previous_authors_ids.add(current_article['author_id'])

            except json.JSONDecodeError as error:
                logging.exception(f'JSON decode error: {error}')
                previous_articles_lists = []
                previous_authors_ids = set()

        else:
            previous_articles_lists = []
            previous_authors_ids = set()

        # 15 days
        time_threshold = 15 * 24 * 60 * 60

        new_articles = []

        # Loop through each article in the current article list
        for current_article_list in current_articles_lists:
            for current_article in current_article_list:
                is_new = True

                # If the author id is new, skip this article,
                # and effectively avoid misjudgment when the last acquisition fails or the next acquisition fails
                if current_article['author_id'] not in previous_authors_ids:
                    continue

                # Skip when the difference between creation_time and snapshot_time exceeds the value of time_threshold
                # and skip time diff judgment for articles with creation_time == 0
                # further avoid misjudgment
                if current_article['creation_time'] != 0:
                    time_diff = int(current_article['snapshot_time']) - int(current_article['creation_time'])
                    if time_diff > time_threshold:
                        is_new = False

                # Use the article_id field of the article as a unique identifier
                # to find whether it exists in the last obtained article list
                for previous_articles_lists_list in previous_articles_lists:
                    for previous_article in previous_articles_lists_list:
                        if current_article['article_id'] == previous_article['article_id']:
                            is_new = False
                            break
                    if not is_new:
                        break

                # If the current article does not exist in the last obtained article list,
                # add it to the new article list
                if is_new:
                    new_articles.append(current_article)

        # Save the current article list to the previous_articles_file_path file for comparison at the next execution
        with open(previous_articles_file_path, 'w', encoding='utf-8') as f:
            json.dump(current_articles_lists, f, ensure_ascii=False)

    except FileNotFoundError as error:
        new_articles = []
        logging.exception(f'File not found: {error}')
    except Exception as error:
        new_articles = []
        logging.exception(f'Unexpected error 3: {error}')

    return new_articles


def push_to_dingtalk(new_articles, dingtalk_bot_key=r".\conf\dingtalk_bot_key.json"):
    from dingtalkchatbot.chatbot import DingtalkChatbot

    # load dingtalk_bot_key
    try:
        with open(dingtalk_bot_key, 'r', encoding='utf-8') as r:
            dingtalk_bot_key_json = json.load(r)
    except Exception as error:
        logging.exception(f'{dingtalk_bot_key} read error: {error}')

    # push
    try:
        if dingtalk_bot_key_json:
            for bot in dingtalk_bot_key_json:
                webhook = bot['webhook']
                secret = bot['secret']

                dingtalk_bot = DingtalkChatbot(webhook, secret=secret)

                logging.info(f"Now pushing articles to: {bot['name']}")

                if new_articles:
                    for i, article in enumerate(new_articles):
                        author_name = article['author_name']
                        channel_name = article['channel_name']
                        title = article['title']
                        link = article['link']

                        snapshot_time_obj = datetime.fromtimestamp(int(article['snapshot_time']))
                        snapshot_time = snapshot_time_obj.strftime('%Y-%m-%d %H:%M:%S')

                        creation_time_obj = datetime.fromtimestamp(int(article['creation_time']))
                        creation_time = creation_time_obj.strftime('%Y-%m-%d %H:%M:%S')

                        msg = '【' + author_name + '】发布资讯' \
                              + '\n\n渠道：' + channel_name \
                              + '\n\n标题：' + title \
                              + '\n\n链接：' + link \
                              + '\n\n发布时间：' + creation_time \
                              + '\n\n本次推送共 ' + str(len(new_articles)) + ' 条' \
                              + '，当前第 ' + str(i + 1) + ' 条' \
                              + '\n截取于 ' + snapshot_time

                        # DingTalk is now limited to sending 20 messages per minute,
                        # if it exceeds, it will be sent to the waiting queue
                        dingtalk_bot.send_text(msg=msg, is_at_all=False)

    except Exception as error:
        logging.exception(f'Push to DingTalk error: {error}')


def get_new_articles_and_push_to_dingtalk(spiders_list_path=r".\conf\spider_list.json",
                                          dingtalk_bot_key=r".\conf\dingtalk_bot_key.json"):
    objects_list = spiders_init(load_spiders_list(spiders_list_path))
    new_articles = get_new_articles(objects_list)

    logging.info(f"new articles: {new_articles}")

    push_to_dingtalk(new_articles, dingtalk_bot_key)


if __name__ == "__main__":
    # log
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%m/%d/%Y %H:%M:%S"

    logging.basicConfig(filename='spider.log', level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT,
                        encoding='utf-8')

    get_new_articles_and_push_to_dingtalk()
