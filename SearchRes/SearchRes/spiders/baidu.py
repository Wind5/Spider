import scrapy
import requests
from bs4 import BeautifulSoup
import re
from CxExtractor import CxExtractor

class BaiduSpider(scrapy.Spider):
  name = 'baidu'
  # try all saved in cn
  __path = '/home/ChenJW/Project/Spider/SearchRes/'
  __num_of_done = 0
  __num_of_wanted = 1000

  def start_requests(self):
    key = getattr(self, 'key', None)
    self.__num_of_wanted = int(getattr(self, 'num', 10))
    pagenum = 100
    pagenum = int(getattr(self, 'pagenum', None))
    for pg in range(pagenum):
      if self.__num_of_done >= self.__num_of_wanted:
        return
      cn_url = requests.get('http://www.baidu.com/s?', params={'wd': key, 'pn': str(10 * pg), 'rsv_srlang': 'cn'}).url
      en_url = requests.get('http://www.baidu.com/s?', params={'wd': key, 'pn': str(10 * pg), 'rsv_srlang': 'en'}).url
      yield scrapy.Request(cn_url, self.parse, meta = {'engine': 'baidu'})
      yield scrapy.Request(en_url, self.parse, meta = {'engine': 'baidu'})

  def parse(self, response):
    if self.__num_of_done >= self.__num_of_wanted:
        return
    #print html
    soup = BeautifulSoup(response.body,"lxml")
    div = soup.find('div',id='wrapper').find('div',id='wrapper_wrapper').find('div',id='container').find('div',id='content_left')
    print type(div.find('h3'))
    for link in div.find_all('div', [re.compile('result c-container '), re.compile('result-op c-container')]):
        if self.__num_of_done >= self.__num_of_wanted:
          return
        a = link.find('h3').find('a')
        # print a.text
        print a['href']
        yield scrapy.Request(a['href'], self.parse_content, meta={'filename': a.text, 'engine': response.meta['engine'], 'rank': str(link['id'])})

  def parse_content(self, response):
    if self.__num_of_done >= self.__num_of_wanted:
      return
    cx = CxExtractor(threshold=186)
    if cx.crawl(response.url, response.body, self.__path, response.meta['filename'], response.meta['engine'], response.meta['rank']) is not None:
      self.__num_of_done += 1