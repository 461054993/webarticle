import requests
from urllib.request import urlopen
import re
import chardet
import numpy as np
import matplotlib.pylab as plt
from bs4 import BeautifulSoup


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
    L = [2*threshold] * line_num
    plt.plot(L, color="red", linewidth=0.5, linestyle="-")
    plt.show()


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

url = 'http://auto.163.com/17/0417/07/CI77IISM000884MM.html'
data = urlopen(url).read()
# 获取源代码之后找到网页编码方式 再获取
encoder = chardet.detect(data)

x = requests.get(url)
if encoder:
    x.encoding = encoder['encoding']
else:
    x.encoding = 'utf-8'    # utf-8 gb2312 utf-16

text = x.text

title = BeautifulSoup(x.text, 'html.parser').find('head').find('title').get_text()
print(title)

re1 = re.compile(r'<!--[\s\S]*?-->')               # .匹配除换行符外所有字符 有换行符出现 用\s\S
re2 = re.compile(r'<script.*?>[\s\S]*?</script>')  # re1 re2 re3 用来剔除非html标签的噪音
re3 = re.compile(r'<style.*?>[\s\S]*?</style>')    # 比如js脚本或者js注释
re4 = re.compile(r'<[\s\S]*?>')
re5 = re.compile(r'http:.*?(jpg|png|jpeg|JPEG)')
re_href = re.compile(r'<a.*?href=.*?>')

text, number = re.subn(re_href, '*', text)
text, number = re.subn(re1, '', text)
text, number = re.subn(re2, '', text)
text, number = re.subn(re3, '', text)
text, number = re.subn(re4, '', text)
text, number = re.subn(re5, '', text)
text = text.replace('\t', '').replace('&nbsp;', '').replace(' ', '')

lines = text.split('\n')
article = []
begin = end = 0                     # 正文开头行和结尾行
for i, line in enumerate(lines):
    if len(line) > 120 and line.count('*') < 5:             # 如果一段超过120个字 直接认为肯定是正文，这样保证article里面肯定不会空
        article.append(i)

if len(article) == 1:
    begin = end = article[0]
else:
    article = list(set(article))
    article.sort()
    begin = article[0]
    end = article[-1]

while True:
    if begin <= 2:
        break
    else:
        if lines[begin-1] == '':
            if lines[begin-2] == '':
                break
            else:
                if not if_adv(lines[begin-2]):
                    begin -= 2
                else:
                    break
        else:
            if if_adv(lines[begin-1]):
                break
            else:
                begin -= 1

while True:
    if end >= len(lines) - 2:
        break
    else:
        if lines[end+1] == '':
            if lines[end+2] == '':
                break
            else:
                if not if_adv(lines[end+2]):
                    end += 2
                else:
                    break
        else:
            if if_adv(lines[end+1]):
                break
            else:
                end += 1


# 对已经获得的正文进行重新审核 部分广告和正文之间可能混在一起
for k in range(begin, end+1):
    text = lines[k].replace('&ldquo;', '“').replace('&rdquo;', '”')
    if text.count('*') > 5 or len(text) < 10:
        if len(text) < 10:
            pass
        else:
            issues = text.split('*')
            text = ''
            for issue in issues:
                if len(issue) > 20:
                    text += issue
            print(text)
    else:
        print(text.replace('*', '').replace('\n', ''))
