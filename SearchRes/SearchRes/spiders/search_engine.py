# -*- coding: utf-8 -*-

import scrapy
import requests
from bs4 import BeautifulSoup
import re
from CxExtractor import CxExtractor
from urllib import urlencode
import os

class EngineSpider(scrapy.Spider):
  name = 'search_engine'
  allowed_domains = []
  # try all saved in cn
  __path = os.getcwd() + '/' # '/home/ChenJW/Project/Spider/SearchRes/'
  __pagenum = 0
  __num_of_done = 0
  __num_of_wanted = 1000
  __get_div = {'Baidu': (lambda soup: soup.find_all('div', [re.compile('result c-container '), re.compile('result-op c-container')])),
           'Bing': (lambda soup: soup.find_all('li', class_='b_algo'))}

  def start_requests(self):
    key = getattr(self, 'key', None)
    if key is None:
      return
    self.__path += key + '/'
    self.__pagenum = int(getattr(self, 'pagenum', 10))
    self.__num_of_wanted = int(getattr(self, 'num', 1000000))
    #Bing
    bing_url = "http://www.bing.com/search?" + urlencode({'q': key})
    yield scrapy.Request(bing_url, self.parse, cookies={"ENSEARCH": "BENVER=0"}, meta={'engine': 'Bing', 'page': 1})  #cn
    # yield scrapy.Request(bing_url, self.parse, cookies={"ENSEARCH": "BENVER=1"}, meta={'engine': 'Bing', 'page': 1})  #en

    #Baidu
    for pg in range(self.__pagenum):
      if self.__num_of_done >= self.__num_of_wanted:
        return
      cn_url = 'http://www.baidu.com/s?' + urlencode({'wd': key, 'pn': str(10 * pg), 'rsv_srlang': 'cn'})
      en_url = 'http://www.baidu.com/s?' + urlencode({'wd': key, 'pn': str(10 * pg), 'rsv_srlang': 'en'})
      yield scrapy.Request(cn_url, self.parse, meta={'engine': 'Baidu'})
      yield scrapy.Request(en_url, self.parse, meta={'engine': 'Baidu'})

  def parse(self, response):
    if self.__num_of_done >= self.__num_of_wanted:
        return
    soup = BeautifulSoup(response.body,"lxml")
    # div = soup.find('div',id='wrapper').find('div',id='wrapper_wrapper').find('div',id='container').find('div',id='content_left')
    if response.meta['engine'] == 'Bing' and response.meta['page'] < self.__pagenum:
      next_page = soup.find('a', title=["Next page", '下一页'])['href']
      yield response.follow(next_page, self.parse, cookies={"ENSEARCH": "BENVER=0"}, meta={'engine': 'Bing', 'page': response.meta['page'] + 1})
    for link in self.__get_div[response.meta['engine']](soup):
        if self.__num_of_done >= self.__num_of_wanted:
          return
        if response.meta['engine'] == 'Baidu':
          a = link.find('h3').find('a')
          yield scrapy.Request(a['href'], self.parse_content, meta={'filename': a.text, 'engine': response.meta['engine'], 'rank': str(link['id'])})
        elif response.meta['engine'] == 'Bing':
          a = link.find('h2').find('a')
          yield scrapy.Request(a['href'], self.parse_content, meta={'filename': a.text, 'engine': response.meta['engine'], 'rank': str(response.meta['page'])})

  def parse_content(self, response):
    if self.__num_of_done >= self.__num_of_wanted:
      return
    cx = CxExtractor(threshold=186)
    print response.url
    if cx.crawl(response.url, response.body, self.__path, response.meta['filename'], response.meta['engine'], response.meta['rank']) is not None:
      self.__num_of_done += 1