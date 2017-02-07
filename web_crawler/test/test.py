#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Aug 7, 2016

@author: finetu
'''
from jinja2 import Template
import json
import xmltodict


xmlStr = \
"""
<info>
<item>
    <title>
       让你变穷的「时间贴现」
      </title><author>
       蛋奶
      </author>
</item>
<item><title>
       古埃及人告诉你如何应对强词夺理的上司
      </title><author>
       蛋奶
      </author>
</item>
</info>
"""
tempStr = \
"""
<div>
{% for it in data %}
<div>
  <span>
    <a href="{{it.href}}">{{it.title}}</a>
  </span>
  <span>
   {{it.author}}
  </span>
</div>
{% endfor %}
</div>
"""
tempStr0 = \
"""
{% for it in info.item %}
{{it.title}}
{%- endfor %}
"""
jsonStr = json.dumps(xmltodict.parse(xmlStr))
jsonObj = json.loads(jsonStr)
# template0 = Template(tempStr0)
# res = template0.render(jsonObj)
template1 = Template(tempStr)
res = template1.render(jsonObj)
print res
