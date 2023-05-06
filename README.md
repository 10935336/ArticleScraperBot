[English](#english) | [简体中文](#%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87)

<br>

# English

## introduce

This is a software that can get the latest updated articles from multiple authors on multiple websites at the same time and push them to the chat through multiple robots.
Modular design so you can add website or push by yourself.

The following sites are currently supported: 

| Name                                  | Module                        |
| ------------------------------------- | ----------------------------- |
| Baidu Baijiahao 百度百家号            | BaiduBaijiahaoSpider.py       |
| Baidu Tieba 百度贴吧                  | BaiduTiebaSpider.py           |
| Bilibili 哔哩哔哩                     | BilibiliSpider.py             |
| Douyin(not tiktok) 抖音               | DouyinSpider.py               |
| NetEase News SelfMedia 网易新闻网易号 | NetEaseNewsSelfMediaSpider.py |
| Sohu News SelfMedia 搜狐新闻搜狐号    | SohuNewsSelfMediaSpider.py    |
| Tencent News SelfMedia 腾讯新闻企鹅号 | TencentNewsSelfMediaSpider.py |
| Sina Weibo 新浪微博                   | SinaWeiboSpider.py            |

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
  For example, the author list of `BilibiliSpider.py` is `bilibili_authors_list.json`;

- Fill in the author name and ID in the author list according to the sample format, the number is not limited;

- Fill in `spider_list.json` This is the list of websites you want to crawl. 
  For example, if you want to crawl bilibili, fill in the module name of bilibili `BilibiliSpider` in `spider_id`, `object_name` can be filled in freely, but cannot be repeated;

- Fill in the push key. 
  For example, DingTalk needs to fill in `webhook`, `secret` and `name` in `dingtalk_bot_key.json`;

- Depending on how often you want to get the latest articles, schedule `python3 -m main.py` with an external timer such as crontab or Windows Task Scheduler;


<br>
<br>
<br>
<br>

# 简体中文

## 介绍

这是一个可以同时从多个网站多位作者获取最新更新的文章并通过多个机器人推送到聊天的软件。相当于订阅作者的动态。
采用模块化设计，所以你可以自行增加站点或推送。

目前支持以下站点:

| 网站名称       | 模块                          |
| -------------- | ----------------------------- |
| 百度百家号     | BaiduBaijiahaoSpider.py       |
| 百度贴吧       | BaiduTiebaSpider.py           |
| 哔哩哔哩       | BilibiliSpider.py             |
| 抖音           | DouyinSpider.py               |
| 网易新闻网易号 | NetEaseNewsSelfMediaSpider.py |
| 搜狐新闻搜狐号 | SohuNewsSelfMediaSpider.py    |
| 腾讯新闻企鹅号 | TencentNewsSelfMediaSpider.py |
| 新浪微博       | SinaWeiboSpider.py            |


<br>

目前支持推送到:

| 名称          | 推送方式       | 模块             | 库                                                                 |
| ------------- | -------------- | ---------------- | ------------------------------------------------------------------ |
| DingTalk 钉钉 | DingTalk Robot | DingTalkRobot.py | [DingtalkChatbot](https://github.com/zhuifengshen/DingtalkChatbot) |

<br>

## 使用方法

- 克隆或下载此仓库；

- 安装 Python 3.11 或更高版本，安装 Firefox，执行 `pip install -r requirements.txt`；

- 打开 `conf` 文件夹；

- 找到你想抓取的网站的作者列表 ，作者列表文件按此方式命名 `<小写模块名称，去掉spider>_authors_list.json` 
  例如 `BilibiliSpider.py` 的作者列表为 `bilibili_authors_list.json`；

- 在作者列表中按示例格式填入作者名称和 ID，个数不限；

- 填写 `spider_list.json` 这是你要爬取的网站列表。
  例如如果你想要爬取bilibili 就在`spider_id`中填写bilibili的模块名称`BilibiliSpider`，`object_name`可以随意填写，但不能重复；

- 填写推送密钥。
  例如钉钉需要在 `dingtalk_bot_key.json` 中填入`webhook`和`secret`和`name`；

- 取决你你多久想获取一次最新文章，使用外部计时器定时执行 `python3 -m main.py` 例如 crontab 或 Window 任务计划程序；

<br>

## 网站模块扩展方式

在 `module` 文件夹内创建你的模块，在模块内创建和文件名同名的类。

- 实现从 `conf/<小写模块名称，去掉spider>_authors_list.json` 读取作者 ID 和名字。

- 实现执行 `self.start()` 后可以在 `self.articles_json` 内读取到
以 `self.articles_json = json.dumps(foobar, ensure_ascii=False)` 储存的文章列表，所有字段均为 `str`，格式如下：

```
[
    {
        "title": "标题", 
        "article_id": "文章ID", 
        "author_id": "作者ID", 
        "author_name": "作者名", 
        "channel_name": "网站名", 
        "link": "链接", 
        "creation_time": "创建时间戳", 
        "snapshot_time": "爬取时间戳"
    }, 
    {
        "title": "标题", 
        "article_id": "文章ID", 
        "author_id": "作者ID", 
        "author_name": "作者名", 
        "channel_name": "网站名", 
        "link": "链接", 
        "creation_time": "创建时间戳", 
        "snapshot_time": "爬取时间戳"
    }
]
```

<br>

## 推送模块扩展方式
还没写。

<br>

## 使用例子

假如我想爬取哔哩哔哩用户“陈睿”和新浪微博用户“新浪科技”和“新浪新闻”的文章并推送到钉钉。

#### 哔哩哔哩

首先通过搜索等方式打开作者主页：
```
https://space.bilibili.com/208259?spm_id_from=333.337.0.0
```
其中 `208259` 为用户 ID

<br>

然后打开 `bilibili_authors_list.json` 填入:

```
[
  {
    "author_id": "208259",
    "author_name": "陈睿-自定义名称"
  }
]
```

<br>

#### 新浪微博

首先通过搜索等方式打开作者主页：

新浪科技：
```
https://m.weibo.cn/u/1642634100?uid=1642634100&t=&luicode=10000011&lfid=100103type%3D3%26q%3D%E6%96%B0%E6%B5%AA%26t%3D
```
其中 `1642634100` 为用户 ID。

<br>

新浪新闻：

如果用户有特殊主页，如`新浪新闻`的主页是`https://weibo.com/sinapapers`，此时打开浏览器控制台，切换为手机模式，刷新页面即可拿到`https://m.weibo.cn/u/2028810631`

<br>

然后打开 `sinaweibo_authors_list.json` 填入:

```
[
  {
    "author_id": "1642634100",
    "author_name": "新浪科技"
  }，
  {
    "author_id": "2028810631",
    "author_name": "新浪新闻"
  }
]
```

#### 爬取站点

打开 `spider_list.json` 填入 
```
[
  {
    "spider_id": "BilibiliSpider",
    "object_name": "bb"
  },
  {
    "spider_id": "SinaWeiboSpider",
    "object_name": "wb"
  }
]
```

#### 钉钉推送

安装官方文档 https://open.dingtalk.com/document/robots/custom-robot-access

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
*/30 * * * * user python3 -m /path-to-spider/main.py

```

将 user 替换为你的实际用户。

注意，此文件必须以换行符结尾，不要删掉最后的空行。



