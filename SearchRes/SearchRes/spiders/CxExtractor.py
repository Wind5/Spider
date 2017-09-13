import requests
import re
from bs4 import BeautifulSoup
import io, os

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
    #is_web_portal
    __web_portal = False

    def __init__(self, threshold=86, blocksWidth=3):
        self.__blocksWidth = blocksWidth
        self.__threshold = threshold

    def crawl(self, url, html, path, filename, engine=None, rank=None):
        if 'sina' in url:
        	res_text = self.crawl_sina(html)
        elif 'ifeng' in url:
            res_text = self.crawl_ifeng(html)
        else:
	        clear_page = self.filter_tags(html)
	        self.infer_lang(clear_page)
	        content = self.getText(clear_page)
	        res_text = self.clean_and_judge(content)
        self.__lang = 'en' if self.__lang else 'cn'
        if res_text is not None and len(res_text) > 0:
            if engine is not None:
                info = url.decode('utf-8') + u'\n' + engine.decode('utf-8') + u'\n' + rank.decode('utf-8') + u'\n'
            else:
                info = url.decode('utf-8') + u'\n'
            path += self.__lang + '/'
            print path
            if os.path.exists(path) is False:
                os.makedirs(path)
            filename = path.decode('utf-8') + filename.replace(u'/', u'|') + u'.txt'
            with io.open(filename, 'w') as f:
                f.write(info + res_text)
            return True
        else:
            return False

    def crawl_sina(self, html):
        self.__lang = False
        s = re.findall(re.compile('<!-- 原始正文start -->.*<!-- 原始正文end -->', re.DOTALL), html)
        if len(s) > 0:
            soup = BeautifulSoup(s[0], 'html.parser')
            [t.extract() for t in soup.find_all('script')]
            return soup.text
        soup = BeautifulSoup(html, 'html.parser')
        try:
            div_content = soup.find('div', id='artibody')
            if div_content.find('div', id=re.compile('ad')) is not None:
                div_content = soup.find('div', id='artibody').find('div')
        except:
            return None
        if div_content is None:
            return None
        [s.extract() for s in div_content.find_all('script')]
        return div_content.text

    def crawl_ifeng(self, html):
        self.__lang = False
        s = re.findall(re.compile('<!--mainContent begin-->.*<!--mainContent end-->', re.DOTALL), html)
        if len(s) > 0:
            soup = BeautifulSoup(s[0], 'html.parser')
            [t.extract() for t in soup.find_all('script')]
            return soup.text
        soup = BeautifulSoup(html, 'html.parser')
        try:
            div_content = soup.find('div', id='main_content')
        except:
            return None
        if div_content is None:
            return None
        [s.extract() for s in div_content.find_all('script')]
        return div_content.text

    def infer_lang(self, content):
    	if type(content) is not unicode:
	        try:
	            s = content.decode('utf-8')
	        except:
	            s = unicode(content, errors='ignore')
        if s is None or len(s) == 0:
            return None
        cn_ratio = 1.* sum([is_chinese(i) for i in s]) / len(s)
        self.__lang = cn_ratio < 0.2
        print 'language: ' + str(self.__lang) + '  cnratio: ' + str(cn_ratio)

    def clean_and_judge(self, content, cn_threshold=10, en_threshold=6):
    	if type(content) is not unicode:
	        try:
	            s = content.decode('utf-8')
	        except:
	            return None
        if s is None or len(s) == 0:
            return None
        s = s.split('\n')
        result = []
        for ts in s:
            if (self.__lang and len(ts.split(' ')) > en_threshold) or (not self.__lang and len(ts) > cn_threshold):
                result.append(ts + '\n')
        # print 'num of lines:' + str(len(result))
        if len(result) < 3:
            return None
        else:
            return u''.join(result)



    def getText(self, content):
        self.__threshold = 120 if self.__lang else 150
        if self.__text:
            self.__text = []
        lines = content.split('\n')
        for i in range(len(lines)):
            # lines[i] = lines[i].replace("\\n", "")
            if len(re.sub(' +', '', lines[i])) == 0 or lines[i] == '\n':
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
            if(self.__indexDistribution[i] > self.__threshold and (not boolstart)):
                if (self.__indexDistribution[i + 1] != 0 or self.__indexDistribution[i + 2] != 0 or self.__indexDistribution[i + 3] != 0):
                    boolstart = True
                    start = i
                    continue
            if (boolstart):
                if (self.__indexDistribution[i] == 0 or self.__indexDistribution[i + 1] == 0):
                    end = i
                    boolend = True
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
        re_doctype = re.compile(
            '<!DOCTYPE.+?>', re.DOTALL | re.I)
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
        s = re_doctype.sub('', s)
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
