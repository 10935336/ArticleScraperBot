import json
import logging
from datetime import datetime
from dingtalkchatbot.chatbot import DingtalkChatbot



def push_to_dingtalk(new_articles, dingtalk_bot_key=r".\conf\dingtalk_bot_key.json"):

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
