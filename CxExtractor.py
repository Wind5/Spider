import requests
import re
from bs4 import BeautifulSoup
import io

def is_alphabet(uchar):
    if (u'\u0041' <= uchar<=u'\u005a') or (u'\u0061' <= uchar<=u'\u007a'):
        return True
    else:
        return False
def is_chinese(uchar):
    if u'\u4e00' <= uchar<=u'\u9fff':
        return True
    else:
        return False
class CxExtractor:
    """cx-extractor implemented in Python"""

    # __threshold = 186
    __text = []
    # __blocksWidth = 3
    __indexDistribution = []
    #web_language, true for en, false for zh-hans
    __lang = 0
    #num_of_a
    __num_a = 0
    #is_web_portal
    __web_portal = False

    def __init__(self, threshold=86, blocksWidth=3):
        self.__blocksWidth = blocksWidth
        self.__threshold = threshold

    def crawl(self, url):
        try:
            html = self.getHtml(url)
        except:
            print 'Failed to get the url'
            return False
        else:
            print 'Succeed to get the url'
        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all('a', href=re.compile('http'))
        self.__num_a = len(links)
        print 'num_a: ' + str(self.__num_a)
        for link in links:
            print link['href']
        div_content = soup.find('div', class_=re.compile('main-content'))
        if div_content is not None and len(div_content) > 0:
            html = str(div_content)
        else:
            div_content = soup.find('div', id=re.compile('main-content'))
            if div_content is not None and len(div_content) > 0:
                html = str(div_content)
        clear_page = self.filter_tags(html)
        # print 'clear_page: ' + clear_page[:15]
        content = self.getText(clear_page)
        # print 'content' + content
        res_text = self.clean_and_judge(content)
        return res_text

    def clean_and_judge(self, content, cn_threshold=10, en_threshold=6):
        s = content.decode('utf-8')
        if s is None or len(s) == 0:
            return None
        cn_ratio = 1.* sum([is_chinese(i) for i in s]) / len(s)
        self.__lang = cn_ratio < 0.3
        print 'language: ' + str(self.__lang) + '  cnratio: ' + str(cn_ratio)
        s = s.split('\n')
        result = [s[0]]
        for i in range(1, len(s) - 1):
            if self.__lang:
                if not (len(s[i].split(' ')) < en_threshold and len(s[i-1].split(' ')) < en_threshold and len(s[i+1].split(' ')) < en_threshold):
                    result.append(s[i] + '\n')
            else:
                if not (len(s[i]) < cn_threshold and len(s[i+1]) < cn_threshold and len(s[i-1]) < cn_threshold):
                    result.append(s[i] + '\n')
        result.append(s[-1] + '\n')
        print 'num of lines:' + str(len(result))
        if len(result) < 5 and self.__num_a > 150:
            return None
        else:
            return u''.join(result)



    def getText(self, content):
        if self.__text:
            self.__text = []
        lines = content.split('\n')
        for i in range(len(lines)):
            # lines[i] = lines[i].replace("\\n", "")
            if lines[i] == ' ' or lines[i] == '\n':
                lines[i] = ''
        del self.__indexDistribution[:]
        for i in range(0, len(lines) - self.__blocksWidth):
            wordsNum = 0
            for j in range(i, i + self.__blocksWidth):
                lines[j] = lines[j].replace("\\s", "")
                wordsNum += len(lines[j])
            self.__indexDistribution.append(wordsNum)
        start = -1
        end = -1
        boolstart = False
        boolend = False
        for i in range(len(self.__indexDistribution) - 1):
            print self.__indexDistribution[i]
            if(self.__indexDistribution[i] > self.__threshold and (not boolstart)):
                if (self.__indexDistribution[i + 1] != 0 or self.__indexDistribution[i + 2] != 0 or self.__indexDistribution[i + 3] != 0):
                    boolstart = True
                    start = i
                    print '-----start------\n'
                    if self.__indexDistribution[i] > 0:
                        for j in range(i, i + self.__blocksWidth):
                            if lines[j] > 0:
                                print lines[j] 
                    continue
            if (boolstart):
                if (self.__indexDistribution[i] == 0 or self.__indexDistribution[i + 1] == 0):
                    end = i
                    boolend = True
                    print '-----end------\n'
            tmp = []
            if(boolend):
                for ii in range(start, end + 1):
                    if(len(lines[ii]) < 5):
                        continue
                    tmp.append(lines[ii] + "\n")
                str = "".join(list(tmp))
                if ("Copyright" in str or "版权所有" in str):
                    continue
                self.__text.append(str)
                boolstart = boolend = False
        result = "".join(list(self.__text))
        return result

    def replaceCharEntity(self, htmlstr):
        CHAR_ENTITIES = {'nbsp': ' ', '160': ' ',
                         'lt': '<', '60': '<',
                         'gt': '>', '62': '>',
                         'amp': '&', '38': '&',
                         'quot': '"', '34': '"', }
        re_charEntity = re.compile(r'&#?(?P<name>\w+);')
        sz = re_charEntity.search(htmlstr)
        while sz:
            entity = sz.group()
            key = sz.group('name')
            try:
                htmlstr = re_charEntity.sub(CHAR_ENTITIES[key], htmlstr, 1)
                sz = re_charEntity.search(htmlstr)
            except KeyError:
                # 以空串代替
                htmlstr = re_charEntity.sub('', htmlstr, 1)
                sz = re_charEntity.search(htmlstr)
        return htmlstr

    def getHtml(self, url):
        response = requests.get(url)
        coding = response.encoding
        page = response.content
        print coding
        return page

    def readHtml(self, path, coding):
        page = open(path, encoding=coding)
        lines = page.readlines()
        s = ''
        for line in lines:
            s += line
        page.close()
        return s

    def filter_tags(self, htmlstr):
        re_nav = re.compile('<nav.+</nav>')
        re_cdata = re.compile('//<!\[CDATA\[.*//\]\]>', re.DOTALL)
        re_script = re.compile(
            '<\s*script[^>]*>.*?<\s*/\s*script\s*>', re.DOTALL | re.I)
        re_style = re.compile(
            '<\s*style[^>]*>.*?<\s*/\s*style\s*>', re.DOTALL | re.I)
        re_textarea = re.compile(
            '<\s*textarea[^>]*>.*?<\s*/\s*textarea\s*>', re.DOTALL | re.I)
        re_option = re.compile(
            '<\s*option[^>]*>.*?<\s*/\s*option\s*>', re.DOTALL | re.I)
        re_label = re.compile(
            '<\s*label[^>]*>.*?<\s*/\s*label\s*>', re.DOTALL | re.I)
        re_br = re.compile('<br\s*?/?>')
        re_h = re.compile('</?\w+.*?>', re.DOTALL)
        re_comment = re.compile('<!--.*?-->', re.DOTALL)
        re_space = re.compile(' +')
        s = re_cdata.sub('', htmlstr)
        s = re_nav.sub('', s)
        s = re_script.sub('', s)
        s = re_option.sub('', s)
        s = re_label.sub('', s)
        s = re_style.sub('', s)
        s = re_textarea.sub('', s)
        s = re_br.sub('', s)
        s = re_h.sub('', s)
        s = re_comment.sub('', s)
        s = re.sub('\\t', '', s)
        s = re.sub('\r', '', s)
        # s = re.sub(' ', '', s)
        s = re_space.sub(' ', s)
        s = self.replaceCharEntity(s)
        return s
