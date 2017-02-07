#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Sep 18, 2016

@author: finetu
'''

from bs4 import BeautifulSoup
import hashlib
import json
import logging
from scrapy.selector import Selector
import xmltodict
import zorba_api

from web_crawler.items import WebTargetRes
from web_crawler.scrapyredis.spiders import RedisSpider


logger = logging.getLogger(__name__)
class TestSpider(RedisSpider):
    """Spider that reads urls from redis queue (myspider:start_urls)."""
    handle_httpstatus_list = [302,403,404,500]
    name = 'test_spider'
    redis_key = 'test_spider:url_queue'
    zorbaStore = zorba_api.InMemoryStore_getInstance()
    zorba = zorba_api.Zorba_getInstance(zorbaStore)
    
    def __init__(self, *args, **kwargs):
        
        super(TestSpider, self).__init__(*args, **kwargs)
    
    
    def parse(self, response):
        if response.status != 200 :
            logger.info(response.url+" crawl failure! status:"+str(response.status))
        if (not response.meta.has_key('xpath')) :
            logger.info(response.url+"can not find xpath in response.meta: "+str(response.meta))
            return
        webTargetRes = WebTargetRes()
       
        webTargetRes["meta"] = {}
        webTargetRes["meta"]["url"] = response.url
        if response.meta.has_key('target_id'):
            webTargetRes["meta"]["id"] = response.meta['target_id']
        if response.meta.has_key('tryKey'):
            webTargetRes["meta"]["tryKey"] = response.meta['tryKey']
        
        if not response.meta.has_key('xquery'):
            logger.info(response.url+"can not find xquery in response.meta: "+str(response.meta))
            return
        
        sel = Selector(response)
        resBody = sel.xpath(response.meta['xpath']).extract()
        if len(resBody) == 0:
            logger.info(response.url+",xpath:"+response.meta['xpath']+" no elements found on this xpath.")
            return
        resBody = resBody[0]
        xquery = response.meta['xquery']
        print xquery
        jsonObj = self.genJsonByXquery(resBody.encode("utf8"),xquery.encode("utf8"))
        webTargetRes['data'] = jsonObj['data']
        
        jsonStr = json.dumps(jsonObj)
        md5 = hashlib.md5(jsonStr).hexdigest()
        webTargetRes["meta"]["md5"] = md5
        yield webTargetRes
    
    def genJsonByXquery(self,resBody,xquery):
        soup = BeautifulSoup(resBody,"lxml")
        prettyStr = soup.prettify().encode("utf8")
        
        dataManager = self.zorba.getXmlDataManager()
        docIter = dataManager.parseXML(prettyStr)
        docIter.open();
        
        doc = zorba_api.Item_createEmptyItem()
        docIter.next(doc)
        docIter.close()
        docIter.destroy()
        
        docManager = dataManager.getDocumentManager()
        docManager.put("response", doc)
        xquery = self.zorba.compileQuery(xquery)
        dynCtx = xquery.getDynamicContext();
        dynCtx.setContextItem(doc);
        xmlStr = xquery.execute()
        docManager.remove("response")
        
        xmlStr = xmlStr.replace("<?xml version=\"1.0\" encoding=\"UTF-8\"?>","").strip()
        xmlStr = "<data>"+xmlStr+"</data>"
        return self.toJsonObj(xmlStr)
    
    def toJsonObj(self,xmlStr):
        jsonStr = json.dumps(xmltodict.parse(xmlStr))
        return json.loads(jsonStr)
    

    def make_request_from_data(self, data):
        if not data.has_key("url"):
            logger.error("Unexpected data from '%s': %r", self.redis_key, data)
            return None
        url = data['url']
        if '://' not in url:
            logger.error("Unexpected URL from '%s': %r", self.redis_key, data)
        request = self.make_requests_from_url(url)
        data.pop("url")
        request.meta.update(data)
        request.replace(dont_filter=True)
        return request
        
