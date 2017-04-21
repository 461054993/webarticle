import requests
from urllib.request import urlopen
import re
import matplotlib.pylab as plt
import urllib
import time
from bs4 import BeautifulSoup


class webarticle(object):
    def __init__(self, url='', keyword='', num=1):

        self.url = url
        self.keyword = keyword
        self.title = ''
        self.text = ''

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

        try:
            self.req = requests.get(self.url, timeout=5)
            self.req.encoding = self.req.headers['content-type'].split('=')[1]
            self.text = self.req.text
        except:
            self.text = ''
            print('parser error, cannot get text, url:', self.url)
            return

        if '百度' in self.title or \
                        '爱奇艺' in self.title or \
                        '优酷' in self.title or \
                        '腾讯视频' in self.title or \
                        len(self.text) < 1000 or \
                        self.req.status_code != 200:
            self.text = ''
            print('web content error, cannot get article, url:', self.url)
            return

        self.title = re.findall(r'<title>(.*?)</title>', self.text)[0]

        self.clean_text()

        lines = self.text.split('\n')
        article = []
        for i, line in enumerate(lines):

            if len(line) > 120 and \
                    len(re.findall(r'\W', line)) / len(line) < 0.2 and \
                    len(re.findall(r'[a-zA-Z]', line)) / len(line) < 0.2:

                # 如果一段超过120个字 直接认为肯定是正文，这样保证article里面肯定不会空
                article.append(i)

        begin = end = 0  # 正文开头行和结尾行

        if len(article) == 0:
            print('cannot get web article, url:', self.url)
            self.text = ''
            return
        elif len(article) == 1:
            begin = end = article[0]
        else:
            article.sort()
            begin = article[0]
            end = article[-1]

        while True:
            if begin <= 2:
                break
            else:
                if lines[begin - 1] == '':
                    if lines[begin - 2] == '':
                        break
                    else:
                        if not self.if_adv(lines[begin - 2]):
                            begin -= 2
                        else:
                            break
                else:
                    if self.if_adv(lines[begin - 1]):
                        break
                    else:
                        begin -= 1

        while True:
            if end >= len(lines) - 2:
                break
            else:
                if lines[end + 1] == '':
                    if lines[end + 2] == '':
                        break
                    else:
                        if not self.if_adv(lines[end + 2]):
                            end += 2
                        else:
                            break
                else:
                    if self.if_adv(lines[end + 1]):
                        break
                    else:
                        end += 1

        # 对已经获得的正文进行重新审核 部分广告和正文之间可能混在一起
        self.text = ''
        for k in range(begin, end + 1):
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

        if self.text != '':
            dic = {}
            dic['title'] = self.title
            dic['text'] = self.text
            return dic

    def get_url_from_net(self, keyword='', num=1):

        page = num // 10  # url总共页数

        if self.keyword == '':
            self.keyword = keyword

        re_html = re.compile(r'href="(.*?)"')  # 提取百度返回的网页

        # 根据关键字从百度获取url
        realurls = []

        if page > 0:
            # url翻页的形式 http://www.baidu.com/s?wd=keyword&pn=(page-1)*10

            for i in range(page + 1):

                print(i)

                baidu_url = 'http://www.baidu.com/s?wd=' + urllib.parse.quote(self.keyword) + '&pn=' + str(i) + '0'
                htmlpage = urllib.request.urlopen(baidu_url, timeout=5).read()
                soup = BeautifulSoup(htmlpage, 'html.parser', from_encoding='utf-8')

                content = soup.find('div', id='wrapper').find('div', id='wrapper_wrapper').find('div',
                                                                                                id='container').find(
                    'div', id='content_left')
                html_tags = content.find_all('div', class_='result c-container ')
                htmls = []
                for html_tag in html_tags:
                    new = html_tag.find('h3', class_='t')
                    new_url = re_html.findall(str(new))[0]
                    print(new.get_text())
                    if '百度' in new.get_text():
                        print('百度文库一类的,不能用 url:', new_url)
                        continue
                    htmls.append(new_url)

                if i == page:
                    num -= page * 10
                    realurls.extend(self.GetRealUrl(htmls)[0:num])
                else:
                    realurls.extend(self.GetRealUrl(htmls))

        else:
            baidu_url = 'http://www.baidu.com/s?wd=' + urllib.parse.quote(self.keyword)
            htmlpage = urllib.request.urlopen(baidu_url, timeout=5).read()
            soup = BeautifulSoup(htmlpage, 'html.parser', from_encoding='utf-8')

            content = soup.find('div', id='wrapper').find('div', id='wrapper_wrapper').find('div', id='container'). \
                find('div', id='content_left')
            html_tags = content.find_all('div', class_='result c-container ')
            htmls = []
            for html_tag in html_tags:
                new = html_tag.find('h3', class_='t')
                new_url = re_html.findall(str(new))[0]
                if '百度' in new.get_text():
                    print('百度文库一类的,不能用 url:', new_url)
                    continue
                htmls.append(new_url)

            realurls.extend(self.GetRealUrl(htmls))

        return realurls

    def store_article(self, path='', name=''):
        if self.text == '':
            return
        else:
            print('find article, url:', self.url)

        if path == '':
            if name == '':
                name = str(time.time()) + '.txt'
            else:
                name += '.txt'
            with open(name, 'w+', encoding='utf-8') as f:
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
