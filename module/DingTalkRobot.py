#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Function: push to dingtalk
# Author: 10935336
# Creation date: 2023-05-06
# Modified date: 2023-05-11


import json
import logging
import os
from datetime import datetime

from dingtalkchatbot.chatbot import DingtalkChatbot


def load_dingtalk_bot_conf(dingtalk_bot_conf_path=None):
    if dingtalk_bot_conf_path is None:
        module_dir = os.path.dirname(os.path.abspath(__file__))
        dingtalk_bot_conf_path = os.path.join(module_dir, '..', 'conf', 'dingtalk_bot_conf.json')

    try:
        with open(dingtalk_bot_conf_path, 'r', encoding='utf-8') as r:
            dingtalk_bot_conf_json = json.load(r)
            return dingtalk_bot_conf_json
    except Exception as error:
        logging.exception(f'{dingtalk_bot_conf_path} read error: {error}')


def push_new_articles_to_dingtalk(new_articles, dingtalk_bot_conf_path=None):
    dingtalk_bot_conf_json = load_dingtalk_bot_conf(dingtalk_bot_conf_path)

    # push
    try:
        if dingtalk_bot_conf_json:
            for bot in dingtalk_bot_conf_json:
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


def push_summary_to_dingtalk(articles_summary, dingtalk_bot_conf_path=None):
    dingtalk_bot_conf_json = load_dingtalk_bot_conf(dingtalk_bot_conf_path)

    # push
    try:
        if dingtalk_bot_conf_json:
            for bot in dingtalk_bot_conf_json:
                webhook = bot['webhook']
                secret = bot['secret']

                dingtalk_bot = DingtalkChatbot(webhook, secret=secret)

                logging.info(f"Now pushing summary to: {bot['name']}")

                msgs = []
                for team_name in articles_summary:

                    start_time_obj = datetime.fromtimestamp(int(articles_summary['time']['start_time']))
                    start_time = start_time_obj.strftime('%Y-%m-%d %H:%M:%S')

                    end_time_obj = datetime.fromtimestamp(int(articles_summary['time']['end_time']))
                    end_time = end_time_obj.strftime('%Y-%m-%d %H:%M:%S')

                    if team_name != "time":
                        msg = f"从 {start_time} \n到 {end_time}\n"
                        msg += f"【{team_name}】在以下渠道\n"
                        for clannel_name in articles_summary[team_name]:
                            if clannel_name != "total":
                                msg += f"{clannel_name} 发布 {articles_summary[team_name][clannel_name]} 篇资讯\n"
                        msg += f"总共发送 {articles_summary[team_name]['total']} 篇资讯"
                        msgs.append(msg)

                for msg in msgs:
                    # DingTalk is now limited to sending 20 messages per minute,
                    # if it exceeds, it will be sent to the waiting queue
                    dingtalk_bot.send_text(msg=msg, is_at_all=False)


    except Exception as error:
        logging.exception(f'Push to DingTalk error: {error}')

if __name__ == "__main__":
    new_articles = [{'title': '\nTest message\n测试信息', 'article_id': '1', 'author_name': 'test-test', 'author_id': 'test', 'channel_name': 'Test', 'link': 'https://example.com', 'creation_time': '1685356491', 'snapshot_time': '1685357308'}]
    push_new_articles_to_dingtalk(new_articles)