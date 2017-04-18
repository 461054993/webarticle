import requests
from urllib.request import urlopen
import re
import chardet
import numpy as np
import matplotlib.pylab as plt
import urllib
import time
from bs4 import BeautifulSoup


class webarticle(object):

    def __init__(self, url='', keyword='', num=1):

        self.url = url
        self.keyword = keyword
        self.keyword_url_num = num

        self.begin = self.end = 0  # 正文开头行和结尾行

        if url != '':
            self.get_web_article()
        elif keyword != '':
            urls = self.get_url_from_net(self.keyword, num)
            for url in urls:
                self.url = url
                self.get_web_article()
                self.store_article()

    def clean_text(self):
        re1 = re.compile(r'<!--[\s\S]*?-->')  # .匹配除换行符外所有字符 有换行符出现 用\s\S
        re2 = re.compile(r'<script.*?>[\s\S]*?</script>')  # re1 re2 re3 用来剔除非html标签的噪音
        re3 = re.compile(r'<style.*?>[\s\S]*?</style>')  # 比如js脚本或者js注释
        re4 = re.compile(r'<[\s\S]*?>')
        re5 = re.compile(r'http:.*?(jpg|png|jpeg|JPEG)')
        re_href = re.compile(r'<a.*?href=.*?>')

        txt = re.sub(re_href, '*', self.text)
        txt1 = re.sub(re1, '', txt)
        txt2 = re.sub(re2, '', txt1)
        txt3 = re.sub(re3, '', txt2)
        txt4 = re.sub(re4, '', txt3)
        txt5 = re.sub(re5, '', txt4)
        self.text = txt5.replace('\t', '').replace('&nbsp;', '').replace(' ', '')

    def get_web_article(self, out_url=''):

        if out_url != '':
            self.url = out_url

        self.encoder = self.get_url_chardet(self.url)
        try:
            self.req = requests.get(self.url)
            self.req.encoding = self.encoder
            self.text = self.req.text
        except:
            print('parser error, cannot get text, url:', self.url)
            return

        if '百度贴吧' in self.text or '发表于' in self.text or '百度经验' in self.text or '百度文库' in self.text or len(
                self.text) < 1000:
            print('web content error, cannot get article, url:', self.url)
            return

        self.clean_text()

        lines = self.text.split('\n')
        article = []
        for i, line in enumerate(lines):
            if len(line) > 120 and line.count('*') < 5:  # 如果一段超过120个字 直接认为肯定是正文，这样保证article里面肯定不会空
                article.append(i)

        if len(article) == 0:
            print('cannot get web article, url:', self.url)
            self.text = ''
            return

        elif len(article) == 1:
            self.begin = self.end = article[0]
        else:
            article.sort()
            self.begin = article[0]
            self.end = article[-1]

        while True:
            if self.begin <= 2:
                break
            else:
                if lines[self.begin - 1] == '':
                    if lines[self.begin - 2] == '':
                        break
                    else:
                        if not self.if_adv(lines[self.begin - 2]):
                            self.begin -= 2
                        else:
                            break
                else:
                    if self.if_adv(lines[self.begin - 1]):
                        break
                    else:
                        self.begin -= 1

        while True:
            if self.end >= len(lines) - 2:
                break
            else:
                if lines[self.end + 1] == '':
                    if lines[self.end + 2] == '':
                        break
                    else:
                        if not self.if_adv(lines[self.end + 2]):
                            self.end += 2
                        else:
                            break
                else:
                    if self.if_adv(lines[self.end + 1]):
                        break
                    else:
                        self.end += 1

        # 对已经获得的正文进行重新审核 部分广告和正文之间可能混在一起
        self.text = ''
        for k in range(self.begin, self.end + 1):
            txt = lines[k].replace('&ldquo;', '“').replace('&rdquo;', '”')
            if txt.count('*') > 5 or len(txt) < 10:
                if len(txt) < 10:
                    pass
                else:
                    issues = txt.split('*')
                    for issue in issues:
                        if len(issue) > 20:
                            self.text += issue + '\n'
            else:
                self.text += txt.replace('*', '') + '\n'

    def get_url_from_net(self, keyword='', num=1):

        if self.keyword == '':
            self.keyword = keyword

        self.keyword = re.sub(r'\s+', ' ', self.keyword)

        # 根据关键字从百度获取第一页的url
        baidu_url = 'http://www.baidu.com/s?wd=' + urllib.parse.quote(self.keyword)
        htmlpage = urllib.request.urlopen(baidu_url, timeout=5).read()
        soup = BeautifulSoup(htmlpage, 'html.parser', from_encoding='utf-8')

        content = soup.find('div', id='wrapper').find('div', id='wrapper_wrapper').find('div', id='container'). \
            find('div', id='content_left')
        html_tags = content.find_all('div', class_='result c-container ')
        htmls = []
        for html_tag in html_tags:
            new = html_tag.find('h3', class_='t')
            htmls.append(str(new).split('}" href="')[1].split('" target="')[0])
        urls = self.GetRealUrl(htmls)
        realurls = []
        for url in urls:
            try:
                response = urllib.request.urlopen(url)
                realurl = response.geturl()
                requests.get(realurl, timeout=2)
                realurls.append(realurl)
            except:
                pass

        return realurls[0:num]

    def store_article(self, path='', name=''):
        if len(self.text) < 200:
            print('content is little, url:', self.url)
            return

        if path == '':
            if name == '':
                name = str(time.time()) + '.txt'
            else:
                name += '.txt'
            with open(name, 'w+') as f:
                f.write(self.text)
            f.close()
        else:
            if name == '':
                name = path + str(time.time()) + '.txt'
            else:
                name = path + name + '.txt'
            with open(name, 'w+') as f:
                f.write(self.text)
            f.close()

    @staticmethod
    def GetRealUrl(urls):
        realurls = []
        for url in urls:
            try:
                response = urllib.request.urlopen(url)
                realurl = response.geturl()
                requests.get(realurl, timeout=2)
                realurls.append(realurl)
            except:
                pass
        return realurls

    @staticmethod
    def get_url_chardet(url):

        data = urlopen(url).read()
        # 获取源代码之后找到网页编码方式 再获取
        encoder = chardet.detect(data)

        return encoder['encoding']

    @staticmethod
    def if_adv(line):
        if len(line) > 40:
            return False
        else:
            if line == '':
                return False
            else:
                if '*' in line[:6] or len(line) < 4:
                    return True
                else:
                    return False

if __name__ == "__main__":
    w = webarticle()
    w.get_web_article('http://www.yjbys.com/gongwuyuan/show-506089.html')
    print(w.text)
