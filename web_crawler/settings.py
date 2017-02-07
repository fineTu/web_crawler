# -*- coding: utf-8 -*-

# Scrapy settings for web_crawler project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#


BOT_NAME = 'web_crawler'

SPIDER_MODULES = ['web_crawler.spiders']
NEWSPIDER_MODULE = 'web_crawler.spiders'

# SPIDER_MIDDLEWARES = {
#     "web_crawler.middleware.SpiderExceptionHandler" : 1,
# }

DOWNLOADER_MIDDLEWARES = {
    'web_crawler.middleware.WebkitDownloader': 1,
}

ITEM_PIPELINES = {
#     'scrapy.pipelines.images.ImagesPipeline': 98,
    'web_crawler.pipelines.ImagesMonthlyPipeline':98,
    'web_crawler.pipelines.ImageUrlReplacePipeline':99,
    'web_crawler.pipelines.WebTargetUpdatePipeline': 100,
    'web_crawler.pipelines.WebTargetTryPipeline': 101,
    'web_crawler.pipelines.WebTargetTestPipeline':999,
}

IMAGES_STORE = '/opt/images'


USER_AGENT = "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36"

LOG_LEVEL = 'INFO'
LOG_FILE = '/var/log/web_crawler/web_spider.log'
LOG_STDOUT = True
#SCHEDULER = 'web_crawler.scrapyredis.scheduler.Scheduler'
#DUPEFILTER_CLASS = 'web_crawler.scrapyredis.dupefilter.RFPDupeFilter'
#SCHEDULER_QUEUE_CLASS = 'web_crawler.scrapyredis.queue.SpiderQueue'
# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'web_crawler (+http://www.yourdomain.com)'

#product
# MYSQL_HOST = '127.0.0.1'
# MYSQL_PORT = 3306
# MYSQL_USER = 'webmoudel'
# MYSQL_PWD = 'newsMetro01'
#  
# REDIS_HOST = '127.0.0.1'
# REDIS_PORT = 6379
# IMAGES_URL_PREX = 'http://182.92.148.29/images/'
#develop
MYSQL_HOST = '127.0.0.1'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PWD = 'root'
 
REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379
IMAGES_URL_PREX = 'http://localhost/images/'