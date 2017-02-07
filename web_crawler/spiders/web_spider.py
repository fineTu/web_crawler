#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Aug 5, 2016

@author: finetu
'''

from bs4 import BeautifulSoup
import hashlib
import json
import logging
import re
from scrapy.selector import Selector
from six import string_types
import xmltodict
import zorba_api

from web_crawler.items import WebTargetRes
from web_crawler.scrapyredis.spiders import RedisSpider


logger = logging.getLogger(__name__)
class WebSpider(RedisSpider):
    """Spider that reads urls from redis queue (myspider:start_urls)."""
    handle_httpstatus_list = [302,403,404,500]
    name = 'web_spider'
    redis_key = 'web_spider:url_queue'
    zorbaStore = zorba_api.InMemoryStore_getInstance()
    zorba = zorba_api.Zorba_getInstance(zorbaStore)
    hrefRex = re.compile(r'(https?://.*?/)')
    imgRex = re.compile(r'.+(jpg|JPG|png|PNG)$')
    image_urls = []
    httpDomain = ""
    def __init__(self, *args, **kwargs):
        
        super(WebSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        try:
            self.image_urls = []
            self.httpDomain = ""
            if response.status != 200 :
                logger.info(response.url+" crawl failure! status:"+str(response.status))
                return
            if (not response.meta.has_key('xpath')) :
                logger.info(response.url+"can not find xpath in response.meta: "+str(response.meta))
                return
            webTargetRes = WebTargetRes()
           
            webTargetRes["meta"] = {}
            webTargetRes["meta"]["url"] = response.url
            self.httpDomain = self.hrefRex.search(response.url).group(1)
            if response.meta.has_key('target_id'):
                webTargetRes["meta"]["target_id"] = response.meta['target_id']
            if response.meta.has_key('try_key'):
                webTargetRes["meta"]["try_key"] = response.meta['try_key']
            
            if response.meta.has_key('xquery'):
                sel = Selector(response)
                resBody = sel.xpath(response.meta['xpath']).extract()
                if len(resBody) == 0:
                    logger.info(response.url+",xpath:"+response.meta['xpath']+" no elements found on this xpath.")
                    return
                resBody = resBody[0]
                xquery = response.meta['xquery']
                jsonObj = self.genJsonByXquery(resBody.encode("utf8"),xquery.encode("utf8"))
                webTargetRes["image_urls"] = self.image_urls
                webTargetRes['data'] = jsonObj['data']
                jsonStr = json.dumps(jsonObj)
                md5 = hashlib.md5(jsonStr).hexdigest()
                webTargetRes["meta"]["md5"] = md5
            else:
                sel = Selector(response)
                news_list = sel.xpath(response.meta['xpath']+'//a')
                 
                items = []
                for news in news_list:
                    item = {}
                    titleStr = ""
                    names =  news.xpath('text()').extract()
                    if len(names) == 0:
                        continue
                    title = news.xpath('text()').extract()[0]
                    link = news.xpath('@href').extract()[0]
                    item['text'] = title.strip()
                    item['href'] = link.strip()
                    titleStr += title.strip()
                    items.append(item)
                 
                webTargetRes["data"] = items
                md5 = hashlib.md5(titleStr).hexdigest()
                webTargetRes["meta"]["md5"] = md5
                self.validate(webTargetRes)
            
            webTargetRes['meta']['is_success'] = True
            yield webTargetRes
        except Exception as e:
            logger.error("Exception in parse: %s", str(e))
            meta = response.meta
            webTargetRes = WebTargetRes()
            webTargetRes["meta"] = {}
            webTargetRes["meta"]["url"] = meta["url"]
            if meta.has_key('target_id'):
                webTargetRes["meta"]["target_id"] = meta['target_id']
            if meta.has_key('try_key'):
                webTargetRes["meta"]["try_key"] = meta['try_key']
            webTargetRes["meta"]["is_success"] = False
            webTargetRes["data"] = {"msg":str(e)}
            
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
        
        try:
            docManager = dataManager.getDocumentManager()
            docManager.put("response", doc)
            xquery = self.zorba.compileQuery(xquery)
            dynCtx = xquery.getDynamicContext();
            dynCtx.setContextItem(doc);
            xmlStr = xquery.execute()
        finally:
            docManager.remove("response")   
        xmlStr = xmlStr.replace("<?xml version=\"1.0\" encoding=\"UTF-8\"?>","").strip()
        xmlStr = "<data>"+xmlStr+"</data>"
        jsonObj = self.toJsonObj(xmlStr)["data"]
        self.append_image_urls(jsonObj)
        return jsonObj
        


    
    def toJsonObj(self,xmlStr):
        jsonStr = json.dumps(xmltodict.parse(xmlStr))
        return json.loads(jsonStr)
    
    def validate(self,webTargetRes):
        prefix = self.hrefRex.search(webTargetRes["meta"]['url']).group(1)
#         linkMap = {}
        
        for i in webTargetRes["data"]:
            if i['text']==None or i['text'].strip()=="" or i['href']==None or i['href'].strip()=="" :
                continue
            i["text"] = i["text"].encode("utf8")
            i["href"] = i["href"].encode("utf8")
            if i['href'].find('http://') == -1 :
                i['href'] = prefix + i['href']

#             if not linkMap.has_key(i['href']) or len(linkMap[i['href']]) < len(i['text']):
#                 linkMap[i['href']] = i['text'].replace('\"','\\\"').strip()
#         
#         jsonObj = []
#         for i in items:
#             if not linkMap.has_key(i["href"]):
#                 continue
#             jsonObj.append({"href":i["href"],"text":linkMap[i['href']]})
#             linkMap[i['href']] = None
#         
#         jsonStr = json.dumps(jsonObj)
#         return webTargetRes
    
#     def parse(self, response):
#         if response.status != 200 :
#             logger.info(response.url+" crawl failure! status:"+str(response.status))
#         if (not response.meta.has_key('xpath')) :
#             logger.info(response.url+"can not find xpath in response.meta: "+str(response.meta))
#         webTargetRes = WebTargetRes()
#        
#         webTargetRes["target"] = {}
#         webTargetRes["target"]["url"] = response.url
#         if response.meta.has_key('target_id'):
#             webTargetRes["target"]["id"] = response.meta['target_id']
#         if response.meta.has_key('tryKey'):
#             webTargetRes["tryKey"] = response.meta['tryKey']
#         sel = Selector(response)
#         news_list = sel.xpath(response.meta['xpath']+'//a')
#         
#         items = []
#         for news in news_list:
#             item = {}
#             titleStr = ""
#             names =  news.xpath('text()').extract()
#             if len(names) == 0:
#                 continue
#             title = news.xpath('text()').extract()[0]
#             link = news.xpath('@href').extract()[0]
#             item['text'] = title.strip()
#             item['href'] = link.strip()
#             titleStr += title.strip()
#             logger.info(title.encode('utf-8'))
#             items.append(item)
#         
#         webTargetRes["linkList"] = items
#         md5 = hashlib.md5(titleStr).hexdigest()
#         webTargetRes["md5"] = md5
#         yield webTargetRes

    def append_image_urls(self,jsonObj):
        if not isinstance(jsonObj,dict) and not isinstance(jsonObj,list):
            return
        if isinstance(jsonObj,dict):
            for entry in jsonObj.iteritems():
                key = entry[0]
                value = entry[1]
                if isinstance(value,string_types) and self.imgRex.search(value)!=None:
                    oldUrl = self.convert_url(value,self.httpDomain)
                    self.image_urls.append(oldUrl)
#                     hascode = hashlib.sha1(self.to_bytes(oldUrl)).hexdigest()
#                     newUrl = IMAGES_URL_PREX+hascode+".jpg"
                    jsonObj[key] = oldUrl
                if isinstance(value,dict) or isinstance(value,list):
                    self.append_image_urls(value)
        if isinstance(jsonObj,list):
            for index in range(len(jsonObj)):
                value = jsonObj[index]
                if isinstance(value,string_types) and self.imgRex.search(value)!=None:
                    oldUrl = self.convert_url(value,self.httpDomain)
                    self.image_urls.append(oldUrl) 
#                     hascode = hashlib.sha1(self.to_bytes(oldUrl)).hexdigest()
#                     newUrl = IMAGES_URL_PREX+hascode+".jpg"
                    jsonObj[index] = oldUrl
                if isinstance(value,dict) or isinstance(value,list):
                    self.append_image_urls(value)
                
#     def to_bytes(self,text, encoding=None, errors='strict'):
#         if isinstance(text, bytes):
#             return text
#         if not isinstance(text, string_types):
#             raise TypeError('to_bytes must receive a unicode, str or bytes '
#                             'object, got %s' % type(text).__name__)
#         if encoding is None:
#             encoding = 'utf-8'
#         return text.encode(encoding, errors)       
    
    def convert_url(self,url,httpDomain):
        if url.startswith("http"):
            return url
        elif url.startswith("//"):
            return "http:"+url
        else:
            return httpDomain+url
        
    def make_request_from_data(self, data):
        if not data.has_key("url"):
            logger.error("Unexpected URL from '%s': %r", self.redis_key, data)
        url = data['url']
        if '://' not in url:
            logger.error("Unexpected URL from '%s': %r", self.redis_key, data)
            
        request = self.make_requests_from_url(url)
#         data.pop("url")
        request.meta.update(data)
        request.replace(dont_filter=True)
        request.callback = self.parse
        request.errback = lambda err: self.handle_request_failure(err, request.meta)
        return request

    def handle_request_failure(self,err,meta):
        logger.warning("download failed: %s ", str(err))
        
        webTargetRes = WebTargetRes()
        webTargetRes["meta"] = {}
        webTargetRes["meta"]["url"] = meta["url"]
        if meta.has_key('target_id'):
            webTargetRes["meta"]["target_id"] = meta['target_id']
        if meta.has_key('try_key'):
            webTargetRes["meta"]["try_key"] = meta['try_key']
        webTargetRes["meta"]["is_success"] = False
        webTargetRes["data"] = {"msg":str(err).strip()}

        yield webTargetRes
        