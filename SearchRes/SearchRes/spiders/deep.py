import scrapy
import requests
from bs4 import BeautifulSoup
import re
from CxExtractor import CxExtractor
import os
from urlparse import urlparse

class DeepSpider(scrapy.Spider):
  name = 'deep'
  __path = os.getcwd() + '/'
  allowed_domains = []

  def start_requests(self):
    url = getattr(self, 'url', None)
    print url
    if url is None:
      return
    self.allowed_domains.append(getattr(self, 'domain', self.get_hostname_from_url(url)))
    self.__path += getattr(self, 'dirname', self.allowed_domains[0].replace('/', '|')) + '/'
    print self.allowed_domains[0]
    yield scrapy.Request(url, self.parse)

  def get_hostname_from_url(self, url):
    return urlparse(url).netloc.replace('www.', '')

  def parse(self, response):
    soup = BeautifulSoup(response.body, 'html.parser')
    # links = soup.find_all('a', href=re.compile('http'))
    links = soup.find_all('a', href=True)
    num_a = len(links)
    url = response.url.encode('utf-8')
    print response.url
    cx = CxExtractor(threshold=36)
    print cx.crawl(response.url, response.body, self.__path, url)
    # print 'num_a: ' + str(num_a) 
    for link in links:
      print '    ' + link['href'].encode('utf-8')
      yield response.follow(link['href'], self.parse)