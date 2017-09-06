import scrapy
import requests
from bs4 import BeautifulSoup
import re
from CxExtractor import CxExtractor

class DeepSpider(scrapy.Spider):
  name = 'deep'
  __path = '/home/ChenJW/Project/Spider/SearchRes/'
  allowed_domains = []

  def start_requests(self):
    url = getattr(self, 'url', None)
    print url
    if url is None:
      return
    self.allowed_domains.append(getattr(self, 'domain', url))
    self.__path += getattr(self, 'dirname', self.allowed_domains[0]) + '/'
    print self.allowed_domains[0]
    yield scrapy.Request(url, self.parse)


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