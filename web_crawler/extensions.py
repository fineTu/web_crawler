#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Nov 9, 2016

@author: finetu
'''
import logging
from scrapy import signals


logger = logging.getLogger(__name__)
class ExceptionHandler(object):

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls()
        crawler.signals.connect(ext.spider_error, signal=signals.spider_error)
        return ext
    
    def spider_error(self, failure, response, spider):
        logger.info("Error on %s, traceback: %s",response.url, failure.getTraceback())
        