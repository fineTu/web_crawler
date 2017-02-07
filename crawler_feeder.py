#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Aug 12, 2016

@author: finetu
'''
import MySQLdb, MySQLdb.cursors 
import json
import logging
import redis

logger = logging.getLogger(__name__)
fh = logging.FileHandler("/var/log/web_crawler/crawler_feeder.log")
fm = logging.Formatter(fmt = "[%(asctime)s]-%(filename)s:%(lineno)s-%(levelname)s - %(message)s")
fh.setFormatter(fm)
logger.addHandler(fh)
logger.setLevel(logging.INFO)
redisConn = redis.Redis(host='127.0.0.1', port=6379)
try:
    mysqlConn = MySQLdb.connect(host="localhost", user="root", passwd="root", db="newsmetro", port=3306, charset="utf8",cursorclass = MySQLdb.cursors.DictCursor)
except MySQLdb.Error,e:
    logger.error("Mysql Error %d: %s" % (e.args[0], e.args[1]))
cur = mysqlConn.cursor()
cur.execute('select * from target where type=1 and status = 1;')
mysqlConn.commit()
resList = []
for t in cur:
    logger.info(t)
#     target = {'id': t[0], 'url': t[4], 'xpath': t[6], 'regex': t[7],'md5': t[9], 'status': t[11]}
    target = {'target_id':t["id"], 'url':t["url"], 'xpath':t["rel_xpath"], 'md5':t["md5"]}
    if t["xquery"] != None:
        target['xquery'] = t["xquery"]
    jsonStr = json.dumps(target)
    redisConn.rpush("web_spider:url_queue",jsonStr)
    logger.info(jsonStr)
cur.close()

    
    
