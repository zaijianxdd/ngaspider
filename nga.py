import requests
from bs4 import BeautifulSoup
import jieba
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import os
from datetime import datetime
import time
import pymysql
from peewee import *
import pandas as pd
import jieba.analyse

articlePath = 'articlePath.txt'
contentPath = 'content.txt'
urlTitle = 'https://bbs.nga.cn/thread.php?fid=521&page=%s&order_by=postdatedesc'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36'
}
cookie = "Hm_lvt_01c4614f24e14020e036f4c3597aa059=1681733684; ngacn0comUserInfo=TheBigBrother%09TheBigBrother%0939%0939%09%0910%090%094%090%090%09; ngaPassportUid=65049272; ngaPassportUrlencodedUname=TheBigBrother; ngaPassportCid=X9g9cekmfnqd49nh1qaivsmplagst3isvvvr8i37; Hm_lpvt_01c4614f24e14020e036f4c3597aa059=1682869937; ngacn0comUserInfoCheck=1ec0188df9cdc4aaf4e3fc8032b45935; ngacn0comInfoCheckTime=1682871405; lastvisit=1682871607; lastpath=/thread.php?fid=521; bbsmisccookies=%7B%22uisetting%22%3A%7B0%3A1%2C1%3A1683179491%7D%2C%22pv_count_for_insad%22%3A%7B0%3A-355%2C1%3A1682873551%7D%2C%22insad_views%22%3A%7B0%3A3%2C1%3A1682873551%7D%7D"
cookie_dict = {i.split("=")[0]: i.split("=")[-1] for i in cookie.split("; ")}

if os.path.exists(articlePath):
    os.remove(articlePath)


# 获取文章列表url
def get_article_urls():
    urlList = []
    file = open(articlePath, 'a', encoding='utf-8')
    for page in range(1, 40):
        url = urlTitle % page
        # 把cookie转换为字典形式
        r = requests.get(url, headers=headers, cookies=cookie_dict)
        # r = open('articleTitle.html', 'r', encoding='gbk').read()
        soup = BeautifulSoup(r.text, 'lxml')
        titles = ''
        for each in soup.find_all('tbody'):
            title = each.find('a', class_='topic').get_text(strip=True)
            aurl = each.find('a', class_='topic').get('href')
            count = each.find('a', class_='replies').get_text()
            uid = each.find('a', class_='author').get('href').split("uid=")[1]
            tid = aurl.split("tid=")[1]
            createTime = float(each.find('span', class_='silver postdate').get_text(strip=True))
            articleDict = {"title": title, "tid": tid, "createTime": createTime, "uid": uid}
            file.write(str(articleDict))
            file.write('\n')
            urlList.append(['https://bbs.nga.cn' + aurl + "&page=%s", count])
            # 超过一周
            if datetime.now().timestamp() - createTime > 60 * 60 * 24 * 7 * 1000:
                pass
    file.close()
    return urlList


# file = open('topic.txt', 'a', encoding='utf-8')
# file.write(titles)
# file.close()


# 获取文章内容
def get_article_content(url, c):
    pages = int(c / 20) + 1
    for i in range(1, pages + 1):
        # r = open('articleContent.html', 'r', encoding='gbk').read()
        r = requests.get(url % i, headers=headers, cookies=cookie_dict)
        soup = BeautifulSoup(r.text, 'lxml')
        tid = url.split("tid=")[1].split('&page=%s')[0]
        table = soup.find_all(class_='forumbox postbox')
        for comment in table:
            commentStr = comment.find(class_='postcontent ubbcode').get_text()
            uid = comment.find(class_='author b').get('href').split("uid=")[1]
            createTime = comment.find(class_='postInfo').find('span').get_text()
            timeArray = time.strptime(createTime, "%Y-%m-%d %H:%M")
            createTime = time.mktime(timeArray)
            try:
                if '[quote]' in commentStr:
                    commentStr = commentStr[commentStr.index('[/quote]') + 8:len(commentStr)]
                if '[b]' in commentStr:
                    commentStr = commentStr[commentStr.index('[/b]') + 4:len(commentStr)]
            except ValueError:
                continue
            commentDict = {"createTime": createTime, "uid": uid, "tid": tid, "content": commentStr}
            file.write(str(commentDict))
            file.write('\n')


# nga为数据库名，并需安装mysql库
db = MySQLDatabase("nga", **{'charset': 'utf8', 'use_unicode': True, 'host': '192.168.2.101', 'user': 'root',
                             'password': 'root'})


# 基类
class BaseModel(Model):
    class Meta:
        database = db


# 表类  articleDict = {"title": title, "tid": tid, "createTime": createTime, "uid": uid}

class Article(BaseModel):
    tid = IntegerField(primary_key=True)
    uid = IntegerField()
    title = CharField()
    createTime = FloatField()

    class Meta:
        # 表名
        table_name = 'article'


# commentDict = {"createTime": createTime, "uid": uid, "tid": tid, "content": commentStr}
class Comment(BaseModel):
    cid = AutoField(primary_key=True)
    tid = IntegerField()
    uid = IntegerField()
    content = TextField()
    createTime = FloatField()

    class Meta:
        # 表名
        table_name = 'comment'


# 创建表
def create_table(table):
    if not table.table_exists():
        table.create_table()


# 删除表
def drop_table(table):
    if table.table_exists():
        table.drop_table()


def set_article():
    rows = [

    ]
    path = 'articlePath.txt'
    file = open(path, 'r', encoding='utf-8')
    lines = file.readlines()
    for line in lines:
        rows.append(eval(line))
    Article.insert_many(rows, fields=None).execute()
    file.close()
    t = Article.select()
    for i in t:
        print(i.title)


def set_comment():
    rows = [

    ]
    path = 'content.txt'
    file = open(path, 'r', encoding='utf-8')
    lines = file.readlines()
    for line in lines:
        rows.append(eval(line))
    Comment.insert_many(rows, fields=None).execute()
    file.close()
    t = Comment.select()
    for i in t:
        print(i.content)


# insert_many() 插入多行，rows为元组或字典列表，fields为需要插入的字段名list列表
# commentDict = {"createTime": createTime, "uid": uid, "tid": tid, "content": commentStr}
def init_database():
    create_table(Article)
    create_table(Comment)
    set_article()
    set_comment()


def generate_word_cloud():
    jieba.load_userdict('user_dict.txt')
    path = "comment_202305062359.txt"

    word = open(path, 'r', encoding='utf-8').read()
    stop_word = ['ac', 'img', 'jpg', 'mon', '202305', 'a2', 'medium', '就是', '不是', '这个']
    # mask = np.array(image.open("logo.jpg"))
    # word = " ".join(jieba.lcut(word))
    w_dict = {}
    t = jieba.analyse.extract_tags(word, topK=200, withWeight=True, allowPOS=())
    for w in t:
        w_dict[w[0]] = w[1]
    wordcloud = WordCloud(background_color="white", width=1000, stopwords=stop_word,
                          height=860, margin=2, font_path="simhei.ttf").generate_from_frequencies(w_dict).to_file(
        'nga.png')


if __name__ == '__main__':
    # 爬取数据
    urls = get_article_urls()
    print('开始获取评论 共有%s条文章' % len(urls))
    file = open(contentPath, 'a', encoding='utf-8')

    for url in urls:
        get_article_content(url[0], int(url[1]))
    print('获取完成')
    file.close()
    # 持久化
    init_database()
    generate_word_cloud()
