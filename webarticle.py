import requests
from urllib.request import urlopen
import re
import chardet
import numpy as np
import matplotlib.pylab as plt
from argparse import ArgumentParser
import urllib
from bs4 import BeautifulSoup
import time

parser = ArgumentParser()
parser.add_argument('-k', '--keyword', help='输入搜索关键字，多个关键字以空格分割', type=str)
parser.add_argument('-u', '--url', help='输入指定url，只限一个', type=str)
parser.add_argument('-p', '--print', help='打印网页正文', action='store_true')
parser.add_argument('-s', '--store', help='保存网页正文,可以添加路径和参数 -s \'/home/local/xxx test1\' 或者采用默认方式 -s \'\'', type=str)
args = parser.parse_args()

class webarticle(object):

    def __init__(self):
        if args.keyword:
            
            self.keyword = re.sub(r'\s+', ' ', args.keyword)

            # 根据关键字从百度获取第一页的url
            baidu_url = 'http://www.baidu.com/s?wd=' + urllib.parse.quote(self.keyword)
            htmlpage = urllib.request.urlopen(baidu_url, timeout=5).read()
            soup = BeautifulSoup(htmlpage, 'html.parser', from_encoding='utf-8')

            content = soup.find('div', id='wrapper').find('div', id='wrapper_wrapper').find('div', id='container').\
                find('div', id='content_left')
            html_tags = content.find_all('div', class_='result c-container ')
            htmls = []
            for html_tag in html_tags:
                new = html_tag.find('h3', class_='t')
                htmls.append(str(new).split('}" href="')[1].split('" target="')[0])
            urls = self.GetRealUrl(htmls)

            # 目前只取第一个url
            self.url = urls[0]

        else:
            self.url = args.url

        self.begin = self.end = 0  # 正文开头行和结尾行
        self.encoder = self.get_url_chardet(self.url)
        self.req = requests.get(self.url)
        self.req.encoding = self.encoder
        self.text = self.req.text

        self.clean_text()
        self.get_web_article()

        if args.print:
            print(self.text)
        elif args.store:
            string = re.sub('\s+', ' ', args.store)
            if ' ' in string:
                temp = string.split(' ')
                self.store_article(temp[0], temp[1])
            else:
                print('store parameter error')
                self.store_article()
        else:
            self.store_article()

    def clean_text(self):
        re1 = re.compile(r'<!--[\s\S]*?-->')  # .匹配除换行符外所有字符 有换行符出现 用\s\S
        re2 = re.compile(r'<script.*?>[\s\S]*?</script>')  # re1 re2 re3 用来剔除非html标签的噪音
        re3 = re.compile(r'<style.*?>[\s\S]*?</style>')  # 比如js脚本或者js注释
        re4 = re.compile(r'<[\s\S]*?>')
        re_href = re.compile(r'<a.*?href=.*?>')

        # 将所有herf链接替换为*
        txt, number = re.subn(re_href, '*', self.text)
        txt, number = re.subn(re1, '', txt)
        txt, number = re.subn(re2, '', txt)
        txt, number = re.subn(re3, '', txt)
        txt, number = re.subn(re4, '', txt)
        self.text = txt.replace('\t', '').replace('&nbsp;', '').replace(' ', '')
    
    def get_web_article(self):

        lines = self.text.split('\n')
        article = []
        for i, line in enumerate(lines):
            if len(line) > 120:  # 如果一段超过120个字 直接认为肯定是正文，这样保证article里面肯定不会空
                article.append(i)

        if len(article) == 0:
            print('cannot get web article')
            exit(0)
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

        self.text = ''
        # 对已经获得的正文进行重新审核 部分广告和正文之间可能混在一起
        for k in range(self.begin, self.end + 1):
            txt = lines[k].replace('&ldquo;', '“').replace('&rdquo;', '”')
            if txt.count('*') > 5:
                issues = txt.split('*')
                for issue in issues:
                    if len(issue) > 20:
                        self.text += issue + '\n'
            else:
                self.text += txt.replace('*', '') + '\n'

    def store_article(self, path='', name=''):
        if path=='':
            if name=='':
                name = str(time.time()) + '.txt'
            else:
                name += '.txt'
            with open(name, 'w+') as f:
                f.write(self.text)
            f.close()
        else:
            if name=='':
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


    @staticmethod
    def show_lines(result):
        lines = result.split('\n')
        threshold = len(result) / len(lines)  # 设置字符阈值
        line_num = len(lines)
        line_length = []
        for i in range(line_num):
            line_length.append(len(lines[i]))

        X = np.arange(line_num) + 1
        Y = np.array(line_length)
        plt.bar(X, Y, width=0.35)
        L = [2 * threshold] * line_num
        plt.plot(L, color="red", linewidth=0.5, linestyle="-")
        plt.show()
                
w = webarticle()

