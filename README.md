[English](#english) | [简体中文](#%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87)

<br>
<br>

# English

Due to legal risks, the crawling module has been removed. Only the main program is provided. The function of the main program is only to aggregate the information returned by each module. It does not include any crawling function. Please implement the specific crawling module yourself.

This program is an open source program, and users assume the risks of using it. The author is not responsible for any legal disputes or losses caused by using this program.

The sample Youtube module is crawled using the officially provided API.

## Introduce

This is a software that can get the latest updated articles from multiple authors on multiple websites at the same time and push them to the chat through multiple robots.
Modular design so you can add website or push by yourself.

Note on memory usage: Due to the strict risk control of some sites, some sites use Selenium + Firefox, which can occupy up to 600MB or more memory.
Other sites generally use Requests + Beautiful Soup 4.

<br>

The following sites are currently supported:

| Name                                  | Module                        | Crawl method            | Note                                           |
| ------------------------------------- | ----------------------------- | ----------------------- | ---------------------------------------------- |
| Youtube                               | YoutubeSpider.py              | Requests + Official API | Need to apply for YouTube Data API v3          |

<br>

Currently supports pushing to:

| Name          | Push method    | Module           | Library                                                            |
| ------------- | -------------- | ---------------- | ------------------------------------------------------------------ |
| DingTalk 钉钉 | DingTalk Robot | DingTalkRobot.py | [DingtalkChatbot](https://github.com/zhuifengshen/DingtalkChatbot) |

<br>

## How to use

- Clone or download this repository;

- Install Python 3.11 or later, install Firefox, execute `pip install -r requirements.txt`;

- Open the `conf` folder;

- Find the author list of the website you want to crawl, the author list file is named in this way `<lowercase module name, remove spider>_authors_list.json`
  For example, the author list of `YoutubeSpider.py` is `youtube_authors_list.json`;

- Fill in the author name and ID in the author list according to the sample format, the number is not limited;

- Fill in `spider_list.json` This is the list of websites you want to crawl.
  For example, if you want to crawl Youtube, fill in the module name of youtube `YoutubeSpider` in `spider_id`, `object_name` can be filled in freely, but cannot be repeated;

- Fill in the push key.
  For example, DingTalk needs to fill in `webhook`, `secret` and `name` in `dingtalk_bot_key.json`;

- Depending on how often you want to get the latest articles, schedule `python3 main.py` with an external timer such as crontab or Windows Task Scheduler;


## Website module extension method

Create your module in the `module` folder and create a class within the module with the same name as the file name.

- Implement reading of author ID and name from `conf/<lowercase module name, remove spider>_authors_list.json` (other values are also acceptable, name standardization is considered).

- The implementation can be read in `self.articles_json` after executing `self.start()`
   A list of articles stored with `self.articles_json = json.dumps(foobar, ensure_ascii=False)`, where the timestamp is an int timestamp, and all fields are `str`. The format is as follows:

```
[
     {
         "title": "title",
         "article_id": "Article ID",
         "author_name": "author name",
         "author_id": "authorID",
         "channel_name": "website name",
         "link": "link",
         "creation_time": "Creation timestamp",
         "snapshot_time": "Crawling timestamp"
     },
     {
         "title": "title",
         "article_id": "Article ID",
         "author_name": "author name",
         "author_id": "authorID",
         "channel_name": "website name",
         "link": "link",
         "creation_time": "Creation timestamp",
         "snapshot_time": "Crawling timestamp"
     }
]
```
If execution fails, an empty list [] needs to be returned.

The main program will read spider_list.json and then read the corresponding file name/class name from the spider_id field, then import the class, execute object_name.start() after instantiation, and then obtain the article list from object_name.articles_json.



<br>
<br>
<br>
<br>

# 简体中文

因法律风险，爬取模块已移除。仅提供主程序，主程序功能仅仅是聚合各个模块返回的信息，不包含任何爬取功能，具体爬取模块请自行实现。

本程序为开源程序，使用者自行承担使用风险。作者对因使用本程序造成的任何法律纠纷或损失概不负责。

示例 Youtube 模块使用官方提供的 API 爬取。


## 介绍

这是一个可以同时从多个网站多位作者获取最新更新的文章并通过多个机器人推送到聊天的软件。相当于订阅作者的动态。

采用模块化设计，所以你可以自行增加站点或推送。

<br>
<br>

目前支持以下站点：

| 站点名称       | 模块                          | 抓取方式                | 注意事项                             |
| -------------- | ----------------------------- | ----------------------- | -------------------------------- |
| Youtube        | YoutubeSpider.py              | Requests + Official API | 需要申请官方 YouTube Data API v3 |

<br>

目前支持推送到：

| 名称          | 推送方式       | 模块             | 库                                                                 |
| ------------- | -------------- | ---------------- | ------------------------------------------------------------------ |
| DingTalk 钉钉 | DingTalk Robot | DingTalkRobot.py | [DingtalkChatbot](https://github.com/zhuifengshen/DingtalkChatbot) |

<br>

## 使用方法

- 克隆或下载此仓库；

- 安装 Python 3.11 或更高版本，安装 Firefox，执行 `pip install -r requirements.txt`；

- 打开 `conf` 文件夹；

- 找到你想抓取的网站的作者列表 ，作者列表文件按此方式命名 `<小写模块名称，去掉spider>_authors_list.json`
  例如 `YoutubeSpider.py` 的作者列表为 `youtube_authors_list.json`；

- 在作者列表中按示例格式填入作者名称和 ID，个数不限；

- 填写 `spider_list.json` 这是你要爬取的网站列表。
  例如如果你想要爬取 Youtube 就在`spider_id`中填写 Youtube 的模块名称`YoutubeSpider`，`object_name`可以随意填写，但不能重复；

- 填写推送密钥。
  例如钉钉需要在 `dingtalk_bot_key.json` 中填入`webhook`和`secret`和`name`；

- 取决你你多久想获取一次最新文章，使用外部计时器定时执行 `python3 main.py` 例如 crontab 或 Window 任务计划程序；

<br>

## 推送内容

#### 新文章推送

默认情况下会以以下格式推送（硬编码在 Robot 模块中）

```
【author_name】发布资讯

渠道：channel_name （硬编码在模块中）

标题：title

链接：link

发布时间：creation_time（%Y-%m-%d %H:%M:%S）

本次推送共 foo 条，当前第 bar 条
截取于 snapshot_time（%Y-%m-%d %H:%M:%S）
```

```
【创伤小组-成员A】发布资讯

渠道：内部通讯

标题：白金会员于 xx 坐标受到伤害

链接：https://example.com

发布时间：2077-05-13 20:00:53

本次推送共 2 条，当前第 1 条
截取于 2077-05-13 20:00:53
```

推送频率取决于你多久执行一次本程序。

#### 汇总推送

默认情况下还会按以下格式在指定时间推送汇总：

```
从 time_judgment()中指定的时间减去 24 小时
到 time_judgment()中指定的时间
【team_name】在以下渠道
channel_name 发布 foo 篇资讯
channel_name 发布 bat 篇资讯
总共发送 foo + bar 篇资讯
```

```
从 2077-05-12 20:00:53
到 2077-05-13 20:00:53
【创伤小组】在以下渠道
内部通讯 发布 100 篇资讯
某某平台 发布 20 篇资讯
某某平台 发布 30 篇资讯
总共发送 150 篇资讯
```

team_name 是从 author_name 中提取的。
如果多位作者属于同一个团体，则可以按照 `团体名-作者名` 的形式填写 author_name。
如果 author_name 中不含有 `-` 则 team_name 等于 author_name。

推送时间由 `main.py` 中的 time_judgment() 控制

```
    # If the current time is around 20 o'clock for 20 minutes
    if time_judgment(target_time_hour=20, time_range=timedelta(minutes=20)):
        # get articles_summary
        articles_summary = get_articles_summary(all_current_articles_lists)
        # push summary to dingtalk
        logging.info(f'articles summary: {articles_summary}')
        push_summary_to_dingtalk(articles_summary)
```

在 `main.py` 中找到此代码，意味在 20 点的前后 15 分钟内，如果执行本程序，则会进行汇总推送。
若要修改时间，修改此行代码即可，如 18 点的前后 30 分钟内：

```
    if time_judgment(target_time_hour=18, time_range=timedelta(minutes=30)):
```

<br>

## 网站模块扩展方式

在 `module` 文件夹内创建你的模块，在模块内创建和文件名同名的类。

- 实现从 `conf/<小写模块名称，去掉spider>_authors_list.json` 读取作者 ID 和名字（其他值也行，名称标准化考虑）。

- 实现执行 `self.start()` 后可以在 `self.articles_json` 内读取到
  以 `self.articles_json = json.dumps(foobar, ensure_ascii=False)` 储存的文章列表，其中时间戳为 int 时间戳，所有字段均为 `str`，格式如下：

```
[
    {
        "title": "标题",
        "article_id": "文章ID",
        "author_name": "作者名",
        "author_id": "作者ID",
        "channel_name": "网站名",
        "link": "链接",
        "creation_time": "创建时间戳",
        "snapshot_time": "爬取时间戳"
    },
    {
        "title": "标题",
        "article_id": "文章ID",
        "author_name": "作者名",
        "author_id": "作者ID",
        "channel_name": "网站名",
        "link": "链接",
        "creation_time": "创建时间戳",
        "snapshot_time": "爬取时间戳"
    }
]
```
如果执行失败，则需要返回空列表 []。

主程序会读取 spider_list.json 然后从 spider_id 字段读取相应文件名/类名，然后导入类，实例化后执行 object_name.start() 然后从 object_name.articles_json 获取文章列表。


<br>

## 推送模块扩展方式

还没写。

<br>

#### 钉钉推送

参考官方文档 https://open.dingtalk.com/document/robots/custom-robot-access

创建 Webhook 地址，安全设置选择加签，获取加签密钥。

打开 `dingtalk_bot_key.json` 填入

```
[
  {
    "webhook": "https://oapi.dingtalk.com/robot/send?access_token=foobar",
    "secret": "SECfoobar",
    "name": "文章推送机器人"
  }
]
```

#### 创建定时任务

安装 Python 3.11 或更高版本，安装 Firefox，执行 `pip install -r requirements.txt`

以 Linux 系统为例，创建 `/etc/cron.d/ArticleScraperBot` 并写入

```
# 每 30 分钟获取一次最新文章
*/30 * * * * user python3 /path-to-spider/main.py

```

将 user 替换为你的实际用户。

注意，此文件必须以换行符结尾，不要删掉最后的空行。

## 网站注意事项

#### Youtube

###### 获取 API Key

Youtube 抓取使用官方 API - YouTube Data API v3。

首先访问 https://console.cloud.google.com/apis/api/youtube.googleapis.com 登录你的 Google 账号。

点击启用 YouTube Data API v3，然后点击左侧凭据，创建凭据。

API 限制选择"限制密钥"，然后选择"YouTube Data API v3"，然后记录 API Key。

此 API 为免费，默认情况下每天配额 10000 次，不必担心收费。

###### 获取频道 ID

如果用户有自定义主页，如 `YouTube` 的主页是 `https://www.youtube.com/@YouTube`，

你可以访问此网站 https://commentpicker.com/youtube-channel-id.php 获取频道 ID，`UCBR8-60-B28hp2BmDPdntcQ` 即为频道 ID。

或者你也可以在浏览器控制台中执行 `ytInitialData.metadata.channelMetadataRenderer.externalId` 即可获得频道 ID。
