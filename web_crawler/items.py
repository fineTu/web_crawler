# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.item import Field


class WebTargetRes(scrapy.Item):
    image_urls = Field()
    images = Field()
    data = Field()
    meta = Field()