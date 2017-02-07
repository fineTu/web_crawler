#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Sep 18, 2016

@author: finetu
'''
import json
import redis


xqueryStr = """
for $_postDiv in doc('response')//div[@class='items']/div[contains(@class,'item-container')]
      let 
        $_postTitle := {data($_postDiv//h2[@class='item-headline']/a)},
        $_postHref := {data($_postDiv//h2[@class='item-headline']/a/@href)},
        $_imgSrc := {data($_postDiv//figure/@data-url)}
      return
        <data>
        <title>{$_postTitle}</title>
        <href>{$_postHref}</href>
        <img>{$_imgSrc}</img>
        </data>
"""
jsonDict = {}
jsonDict["url"]="http://www.ftchinese.com/channel/china.html"
# jsonDict["url"]="http://www.google.com/"
jsonDict["xpath"]="//div[@class='list-inner']"
jsonDict["xquery"]=xqueryStr
jsonDict["try_key"]="123"
print jsonDict
redisConn = redis.Redis(host='127.0.0.1', port=6379)
redisConn.rpush("web_spider:url_queue",json.dumps(jsonDict))