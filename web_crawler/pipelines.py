# -*- coding: utf-8 -*-
import MySQLdb
import datetime
import hashlib
import json
import logging
import redis
from scrapy.http.request import Request
from scrapy.pipelines.images import ImagesPipeline
from scrapy.utils.python import to_bytes
from six import string_types
import time
import urllib
import urllib2

import settings
from web_crawler.settings import IMAGES_URL_PREX


# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
logger = logging.getLogger(__name__)
class WebTargetUpdatePipeline(object):
    try:
        conn = MySQLdb.connect(host=settings.MYSQL_HOST, user=settings.MYSQL_USER, passwd=settings.MYSQL_PWD, db="newsmetro", port=settings.MYSQL_PORT, charset="utf8")
    except MySQLdb.Error,e:
        logger.error("Mysql Error %d: %s" % (e.args[0], e.args[1]))
    redis_conn = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
    
    def process_item(self, item, spider):
        if "meta" in item and "target_id" in item["meta"] and item["meta"]["target_id"] != None and \
            "md5"in item["meta"] and item["meta"]["md5"] != None:
            self.updateInfo(item)
            self.saveNews(item)
        return item


    def updateInfo(self, resData):
        targetId = resData["meta"]["target_id"]
        pValue = (resData["meta"]["md5"], targetId)
        cur = self.conn.cursor()
        cur.execute('update target set md5 = %s where id=%s', pValue)
        self.conn.commit()

        cur = self.conn.cursor()
        cur.execute('select count(*) from target_mapping as tm where tm.target_id=%s', (targetId,))
        count = cur.fetchone()[0]
        jsonStr = json.dumps({"meta":resData["meta"],"data":resData["data"]},ensure_ascii=False).encode("utf8")
#         jsonMd5 = hashlib.md5(jsonStr).hexdigest()
        if count == 1:
            mValue = (jsonStr , resData["meta"]["md5"] , time.time()*1000, targetId)
            cur.execute('update target_mapping set items = %s , md5 = %s , update_time=%s where target_id=%s', mValue)
        elif count==0:
            mValue = (targetId, jsonStr , resData["meta"]["md5"] , time.time()*1000)
            cur.execute('insert into target_mapping(target_id,items,md5,update_time) values(%s,%s,%s,%s)', mValue)
        self.conn.commit()
        self.redis_conn.set('target:md5:'+str(targetId), resData["meta"]["md5"])


    def saveNews(self,resData):
        if resData["data"]==None or len(resData["data"])==0:
            return
        
        cur = self.conn.cursor()
#         prefix = self.hrefRex.search(resData["meta"]['url']).group(1)
        for i in resData["data"]:
            if "text" not in i or "href" not in i:
                continue
#             if(len(i['href'])<0):
#                 continue
#             if i['href'].find('http://') == -1 :
#                 i['href'] = prefix + i['href']

            sql = "select n.id as id from news as n where n.link='%s'" % (i['href'],)
            newsId = cur.execute(sql)
            if newsId!=None and newsId!=0:
                cur.execute('update news as n set n.title = %s,n.publish_time = %s where n.id=%s', (i['text'],time.time()*1000,newsId))
            else:
                cur.execute("insert into news(target_id,title,link,status,publish_time,create_time) \
                    values(%s,%s,%s,%s,%s,%s)",(resData["meta"]['target_id'],i['text'],i['href'],1,time.time()*1000,time.time()*1000))



class WebTargetTryPipeline(object):
    
    def process_item(self, item, spider):
        if "meta" in item and "try_key" in item["meta"] and item["meta"]["try_key"] != None:
            resObj = {"is_success":item['meta']['is_success'],"data":item["data"]}
            jsonObj = {"try_key":item["meta"]["try_key"],"res_str":json.dumps(resObj,ensure_ascii=False).encode("utf8")}
            params = urllib.urlencode(jsonObj)
            try:
                req = urllib2.Request("http://localhost:8080/newsmetro/acceptTryWeb.html", params)
                response = urllib2.urlopen(req)
                res = response.read()
                logger.info("tryweb callback try_key:%s response:%s"%(item["meta"]["try_key"],str(res)))
            except Exception as e:
                logger.error("tryweb callback failed try_key:%s reason:%s"%(item["meta"]["try_key"],str(e)))
        return item
    
    
class ImagesMonthlyPipeline(ImagesPipeline):
    def file_path(self, request, response=None, info=None):
        ## start of deprecation warning block (can be removed in the future)
        def _warn():
            from scrapy.exceptions import ScrapyDeprecationWarning
            import warnings
            warnings.warn('ImagesPipeline.image_key(url) and file_key(url) methods are deprecated, '
                          'please use file_path(request, response=None, info=None) instead',
                          category=ScrapyDeprecationWarning, stacklevel=1)

        # check if called from image_key or file_key with url as first argument
        if not isinstance(request, Request):
            _warn()
            url = request
        else:
            url = request.url

        # detect if file_key() or image_key() methods have been overridden
        if not hasattr(self.file_key, '_base'):
            _warn()
            return self.file_key(url)
        elif not hasattr(self.image_key, '_base'):
            _warn()
            return self.image_key(url)
        ## end of deprecation warning block

        image_guid = hashlib.sha1(to_bytes(url)).hexdigest()  # change to request.url after deprecation
        monthStr = datetime.datetime.now().strftime('%Y%m');
        return 'full/%s/%s.jpg' % (monthStr,image_guid)
    
class ImageUrlReplacePipeline(object):
    
    urlPathDict = {}
    def process_item(self, item, spider):
        if "images" in item and "data" in item:
            for imgInfo in item["images"]:
                self.urlPathDict[imgInfo["url"]] = imgInfo["path"]
            self.replace_img_url(item["data"])
        return item
    
    def replace_img_url(self,jsonObj):
        if not isinstance(jsonObj,dict) and not isinstance(jsonObj,list):
            return
        if isinstance(jsonObj,dict):
            for entry in jsonObj.iteritems():
                key = entry[0]
                value = entry[1]
                if isinstance(value,string_types) and value in self.urlPathDict :
                    path = self.urlPathDict[value]
                    newUrl = IMAGES_URL_PREX+path
                    jsonObj[key] = newUrl
                if isinstance(value,dict) or isinstance(value,list):
                    self.replace_img_url(value)
        if isinstance(jsonObj,list):
            for index in range(len(jsonObj)):
                value = jsonObj[index]
                if isinstance(value,string_types) and value in self.urlPathDict:
                    path = self.urlPathDict[value]
                    newUrl = IMAGES_URL_PREX+path
                    jsonObj[index] = newUrl
                if isinstance(value,dict) or isinstance(value,list):
                    self.replace_img_url(value)

class WebTargetTestPipeline(object):
    
    def process_item(self, item, spider):
        resObj = {"meta":item["meta"],"data":item["data"]}
        if "image_urls" in item:
            resObj["image_urls"] = item["image_urls"]
        if "images" in item:
            resObj["images"] = item["images"]
        logger.info("test info -------> "+json.dumps(resObj).encode("utf8"))
        return item
