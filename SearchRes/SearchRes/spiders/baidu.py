import scrapy
import requests
from bs4 import BeautifulSoup
import re
from CxExtractor import CxExtractor

class BaiduSpider(scrapy.Spider):
  name = 'baidu'
  __path = { 'cn': '/home/ChenJW/Project/Spider/SearchRes/cn_res/', 'en': '/home/ChenJW/Project/Spider/SearchRes/en_res/'}

  def start_requests(self):
    key = getattr(self, 'key', None)
    pagenum = 5
    # pagenum = int(getattr(self, 'pagenum', None))
    for pg in range(pagenum):
      cn_url = requests.get('http://www.baidu.com/s?', params={'wd': key, 'pn': str(10 * pg), 'rsv_srlang': 'cn'}).url
      en_url = requests.get('http://www.baidu.com/s?', params={'wd': key, 'pn': str(10 * pg), 'rsv_srlang': 'en'}).url
      yield scrapy.Request(cn_url, self.parse)
      yield scrapy.Request(en_url, self.parse)

  def parse(self, response):
    html = response.body
    #print html
    soup = BeautifulSoup(html,"lxml")
    linkpattern = re.compile('href=\"(.+?)\"')
    div = soup.find('div',id='wrapper').find('div',id='wrapper_wrapper').find('div',id='container').find('div',id='content_left')
    print type(div.find('h3'))
    for link in div.find_all('div', [re.compile('result c-container '), re.compile('result-op c-container')]):
        a = link.find('h3').find('a')
        print a.text + ': ' + a['href']
        yield scrapy.Request(a['href'], self.parse_content, meta={'filename': a.text})

  def parse_content(self, response):
    cx = CxExtractor(threshold=186)
    cx.crawl(response.body, self.__path, response.meta['filename'])