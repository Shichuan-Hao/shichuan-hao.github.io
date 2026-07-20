---
title: "ElasticSearch 高级查询语法Query DSL实战【耗时整理‖cunlove.cn】"
description: "主讲老师:Fox 有道云笔记地址:https://note.youdao.com/s/8WkK3m2H 1. ES高级查询Query DSL ES中提供了一种强大的检索数据方式,这种检索方式称之为Query DSL(Domain Specified Language 领域专用语言) , Query DSL是利用Rest API传递JSON格式的请求体(RequestBody)数据与ES进行交..."
author: hsc
date: 2026-10-13 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', 'Redis', 'Kafka', 'RocketMQ', 'Netty', 'ElasticSearch', 'ShardingSphere', 'ES', '实战']
toc: true
---

> 本文整理自《四、分布式专题》课程笔记，共 60 页。

主讲老师:Fox
有道云笔记地址:https://note.youdao.com/s/8WkK3m2H
1. ES高级查询Query DSL
ES中提供了一种强大的检索数据方式,这种检索方式称之为Query DSL(Domain Specified Language
领域专用语言) , Query DSL是利用Rest API传递JSON格式的请求体(RequestBody)数据与ES进行交
互,这种方式的丰富查询语法让ES检索变得更强大,更简洁。
官方文档: https://www.elastic.co/guide/en/elasticsearch/reference/8.14/query-dsl.html
基本语法:
1 GET /<index_name>/_search {json请求体数据}
示例数据准备

1 DELETE /employee
2 PUT /employee
3 {
4 "settings": {
5 "number_of_shards": 1,
6 "number_of_replicas": 1
7 },
8 "mappings": {
9 "properties": {
10 "name": {
11 "type": "keyword"
12 },
13 "sex": {
14 "type": "integer"
15 },
16 "age": {
17 "type": "integer"
18 },
19 "address": {
20 "type": "text",
21 "analyzer": "ik_max_word",
22 "fields": {
23 "keyword": {
24 "type": "keyword"
25 }
26 }
27 },
28 "remark": {
29 "type": "text",
30 "analyzer": "ik_smart",
31 "fields": {
32 "keyword": {
33 "type": "keyword"
34 }
35 }
36 }
37 }
38 }
39 }

40
41 POST /employee/_bulk
42 {"index":{"_index":"employee","_id":"1"}}
43 {"name":"张三","sex":1,"age":25,"address":"广州天河公园","remark":"java developer"}
44 {"index":{"_index":"employee","_id":"2"}}
45 {"name":"李四","sex":1,"age":28,"address":"广州荔湾大厦","remark":"java assistant"}
46 {"index":{"_index":"employee","_id":"3"}}
47 {"name":"王五","sex":0,"age":26,"address":"广州白云山公园","remark":"php developer"}
48 {"index":{"_index":"employee","_id":"4"}}
49 {"name":"赵六","sex":0,"age":22,"address":"长沙橘子洲","remark":"python assistant"}
50 {"index":{"_index":"employee","_id":"5"}}
51 {"name":"张龙","sex":0,"age":19,"address":"长沙麓谷企业广场","remark":"java architect
assistant"}
52 {"index":{"_index":"employee","_id":"6"}}
53 {"name":"赵虎","sex":1,"age":32,"address":"长沙麓谷兴工国际产业园","remark":"java
architect"}
54
55
56
1.1 match_all ——匹配所有文档
match_all查询是一个特殊的查询类型,它用于匹配索引中的所有文档,而不考虑任何特定的查询条
件。
基本语法
1 GET /<your-index-name>/_search
2 {
3 "query": {
4 "match_all": {}
5 }
6 }
7
高级用法
例如,如果您想要返回索引中的前10个文档,并且按照文档的评分进行排序,您可以使用以下查询:

1 GET /<your-index-name>/_search
2 {
3 "query": {
4 "match_all": {}
5 },
6 "size": 10,
7 "sort": [
8 {"_score": {"order": "desc"}}
9 ]
10 }
11
_source的用法

1
2 #不查看源数据,仅查看元字段
3
4 GET /<your-index-name>/_search
5 {
6 "query": {
7 "match_all": {}
8 },
9 "_source": false
10 }
11
12 # 返回指定字段
13 GET /<your-index-name>/_search
14 {
15 "query": {
16 "match_all": {}
17 },
18 "_source": ["field1","field2"]
19 }
20
21 #只看以obj.开头的字段
22 GET /<your-index-name>/_search
23 {
24 "query": {
25 "match_all": {}
26 },
27 "_source": "obj.*"
28 }
29
30
示例
size返回指定条数

1 GET /employee/_search
2 {
3 "query": {
4 "match_all": {}
5 },
6 "size": 3
7 }
8
9
from&size分页查询
1 GET /employee/_search
2 {
3 "query": {
4 "match_all": {}
5 },
6 "from": 0,
7 "size": 5
8 }
9
10
sort指定字段排序

1 # 根据age排序
2 GET /employee/_search
3 {
4 "query": {
5 "match_all": {}
6 },
7 "sort": [
8 {
9 "age": "desc"
10 }
11 ]
12 }
13
14 # 排序的同时进行分页
15 GET /employee/_search
16 {
17 "query": {
18 "match_all": {}
19 },
20 "sort": [
21 {
22 "age": "desc"
23 }
24 ],
25 "from": 2,
26 "size": 5
27 }
28
29
_source返回源数据

1 GET /employee/_search
2 {
3 "query": {
4 "match_all": {}
5 },
6 "_source": ["name","address"]
7 }
8
1.2 精确匹配
精确匹配是指的是搜索内容不经过文本分析直接用于文本匹配,这个过程类似于数据库的SQL查询,
搜索的对象大多是索引的非text类型字段。此类检索主要应用于结构化数据,如ID、状态和标签等。
term——单字段精确匹配查询
term检索主要应用于单字段精准匹配的场景。在实战过程中,需要避免将term检索应用于text类型的检
索。进一步说,term检索针对的是非text类型,用于text类型时并不会报错,但检索结果一般会达不到
预期。
基本语法
在Elasticsearch 8.x中,term查询用于执行精确匹配查询,它适用于未经过分词处理的keyword字段类
型。term查询的基本语法如下:

1
2 GET /{index_name}/_search
3 {
4 "query": {
5 "term": {
6 "{field.keyword}": {
7 "value": "your_exact_value"
8 }
9 }
10 }
11 }
12
13
这里的{index_name}是你要查询的索引名称,{field.keyword}是你要匹配的字段名称,.keyword后缀表
示该字段是一个keyword类型,用于存储精确匹配的数据。"value"是你要精确匹配的值。
示例
对bool,日期,数字,结构化的文本可以利用term做精确匹配
1 # 查询姓名为张三的员工信息
2 GET /employee/_search
3 {
4 "query": {
5 "term": {
6 "name": {
7 "value": "张三"
8 }
9 }
10 }
11 }
12
注意:最好不要在term查询的字段中使用text字段,因为text字段会被分词,这样做既没有意义,还很
有可能什么也查不到。

1 # 思考: 查询广州白云是否有数据,为什么?
2 GET /employee/_search
3 {
4 "query":{
5 "term": {
6 "address": {
7 "value": "广州白云"
8 }
9 }
10 }
11 }
12
13 # 采用term精确查询, 查询字段映射类型为keyword
14 GET /employee/_search
15 {
16 "query":{
17 "term": {
18 "address.keyword": {
19 "value": "广州白云山公园"
20 }
21 }
22 }
23 }
24
25
term处理多值字段(数组)时,term查询是包含,不是等于。

1 POST /people/_bulk
2 {"index":{"_id":1}}
3 {"name":"小明","interest":["跑步","篮球"]}
4 {"index":{"_id":2}}
5 {"name":"小红","interest":["跳舞","画画"]}
6 {"index":{"_id":3}}
7 {"name":"小丽","interest":["跳舞","唱歌","跑步"]}
8
9 POST /people/_search
10 {
11 "query": {
12 "term": {
13 "interest.keyword": {
14 "value": "跑步"
15 }
16 }
17 }
18 }
19
20
21
在ES中,Term查询,对输入不做分词。会将输入作为一个整体,在倒排索引中查找准确的词项,并且
使用相关度算分公式为每个包含该词项的文档进行相关度算分。
可以通过 Constant Score 将查询转换成一个 Filtering,避免算分,并利用缓存,提高性能。
将Query 转成 Filter,忽略TF-IDF计算,避免相关性算分的开销
Filter可以有效利用缓存

1 GET /employee/_search
2 {
3 "query": {
4 "constant_score": {
5 "filter": {
6 "term": {
7 "address.keyword": "广州白云山公园"
8 }
9 }
10 }
11 }
12 }
terms——多值精确匹配
terms检索主要应用于多值精准匹配场景,它允许用户在单个查询中指定多个词条来进行精确匹配。这
种查询方式适合从文档中查找包含多个特定值的字段,例如筛选出具有多个特定标签或状态的项目。
而terms检索是针对未分析的字段进行精确匹配的,因此它在处理关键词、数字、日期等结构化数据时
表现良好。
基本语法
在Elasticsearch 8.x中,进行多字段精确匹配时,可以使用terms查询。terms查询允许你指定一个字
段,并匹配该字段中的多个精确值。
基本语法如下:

1
2 GET /<index_name>/_search
3 {
4 "query": {
5 "terms": {
6 "<field_name>": [
7 "value1",
8 "value2",
9 "value3",
10 ...
11 ]
12 }
13 }
14 }
15
16
<index_name> 是你想要查询的索引名称。
<field_name> 是你想要对其执行terms查询的字段名。
方括号内的值列表是你希望在查询中匹配的字段值。
示例
1 POST /employee/_search
2 {
3 "query": {
4 "terms": {
5 "remark.keyword": ["java assistant", "java architect"]
6 }
7 }
8 }
9
10
range——范围查询

range检索是Elasticsearch中一种针对指定字段值在给定范围内的文档的检索类型。这种查询适合对数
字、日期或其他可排序数据类型的字段进行范围筛选。range检索支持多种比较操作符,如大于(gt)、
大于等于(gte)、小于(lt)和小于等于(lte)等,可以实现灵活的区间查询。
基本语法
在Elasticsearch 8.x版本中,range查询的基本语法如下:
1 GET /<index_name>/_search
2 {
3 "query": {
4 "range": {
5 "<field_name>": {
6 "gte": <lower_bound>,
7 "lte": <upper_bound>,
8 "gt": <greater_than_bound>,
9 "lt": <less_than_bound>
10 }
11 }
12 }
13 }
14
15
<index_name> 是你想要查询的索引名称。
<field_name> 是你想要对其执行range查询的字段名。
gte 表示大于或等于(Greater Than or Equal)。
lte 表示小于或等于(Less Than or Equal)。
gt 表示严格大于(Greater Than)。
lt 表示严格小于(Less Than)。
<lower_bound>, <upper_bound>, <greater_than_bound>, <less_than_bound> 是指定的数值边
界。
示例
查询年龄在25到28的员工

1 POST /employee/_search
2 {
3 "query": {
4 "range": {
5 "age": {
6 "gte": 25,
7 "lte": 28
8 }
9 }
10 }
11 }
12
日期范围查询
1) 生成测试数据
假设我们正在创建一个笔记应用,每条笔记都有一个创建日期。

1 PUT /notes
2 {
3 "settings": {
4 "number_of_shards": 1,
5 "number_of_replicas": 0
6 },
7 "mappings": {
8 "properties": {
9 "title": {"type": "text"},
10 "content": {"type": "text"},
11 "created_at": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"}
12 }
13 }
14 }
15
16 POST /notes/_bulk
17 {"index":{"_id":"1"}}
18 {"title":"Note 1","content":"This is the first note.","created_at":"2023-07-01
12:00:00"}
19 {"index":{"_id":"2"}}
20 {"title":"Note 2","content":"This is the second note.","created_at":"2023-07-05
15:30:00"}
21 {"index":{"_id":"3"}}
22 {"title":"Note 3","content":"This is the third note.","created_at":"2023-07-10
08:45:00"}
23 {"index":{"_id":"4"}}
24 {"title":"Note 4","content":"This is the fourth note.","created_at":"2023-07-15
20:15:00"}
25
26
2)使用range查询来查找在特定日期范围内的笔记。
假设我们想找出在2023年7月5日和2023年7月10日之间的所有笔记。

1 POST /notes/_search
2 {
3 "query": {
4 "range": {
5 "created_at": {
6 "gte": "2023-07-05 00:00:00",
7 "lte": "2023-07-10 23:59:59"
8 }
9 }
10 }
11 }
12
13
Elasticsearch支持日期数学表达式,允许在查询和聚合中使用相对时间点。以下是一些常见的日期数
学表达式的示例和解释:
now:当前时间点。
now-1d:从当前时间点向前推1天的时间点。
now-1w:从当前时间点向前推1周的时间点。
now-1M:从当前时间点向前推1个月的时间点。
now-1y:从当前时间点向前推1年的时间点。
now+1h:从当前时间点向后推1小时的时间点。

1 POST /product/_bulk
2 {"index":{"_id":1}}
3 {"price":100,"date":"2023-01-01","productId":"XHDK-1293"}
4 {"index":{"_id":2}}
5 {"price":200,"date":"2022-01-01","productId":"KDKE-5421"}
6
7
8 # 返回所有在当前时间点前两年内的产品文档。
9 GET /product/_search
10 {
11 "query": {
12 "range": {
13 "date": {
14 "gte": "now-2y"
15 }
16 }
17 }
18 }
19
exists——是否存在查询
exists检索在Elasticsearch中用于筛选具有特定字段值的文档。这种查询类型适用于检查文档中是否存
在某个字段,或者该字段是否包含非空值。通过使用exists检索,你可以有效地过滤掉缺少关键信息的
文档,从而专注于包含所需数据的结果。应用场景包括但不限于数据完整性检查、查询特定属性的文
档以及对可选字段进行筛选等。
基本语法

1
2 GET /<index_name>/_search
3 {
4 "query": {
5 "exists": {
6 "field": "missing_field"
7 }
8 }
9 }
10
11
示例
查询索引库中存在remark字段的文档
1
2 GET /employee/_search
3 {
4 "query": {
5 "exists":
6 {
7 "field": "remark"
8 }
9 }
10 }
11
ids——根据一组id查询
IDs检索也是一种常用的Elasticsearch查询方法,它允许我们基于给定的ID组快速召回相关数据,从而
实现高效的文档检索。
基本语法
在Elasticsearch 8.x中,ids查询用于返回具有指定ID列表的文档。这个查询是检索特定文档的有效方
式,特别是当你已经知道具体的文档ID时。
基本语法如下:

1
2 GET /<index_name>/_search
3 {
4 "query": {
5 "ids": {
6 "values": ["id1", "id2", "id3", ...]
7 }
8 }
9 }
10
11
示例
1 GET /employee/_search
2 {
3 "query": {
4 "ids": {
5 "values": [1,2]
6 }
7 }
8 }
9
10
11
prefix——前缀匹配
prefix会对分词后的term进行前缀搜索。
它不会对要搜索的字符串分词,传入的前缀就是想要查找的前缀
默认状态下,前缀查询不做相关性分数计算,它只是将所有匹配的文档返回,然后赋予所有相关分数值为1。
prefix的原理:
需要遍历所有倒排索引,并比较每个词项是否以所搜索的前缀开头。
基本语法
在Elasticsearch 8.x中,prefix查询用于搜索那些在指定字段中以特定前缀开始的文档。这种查询通常
用于自动补全或搜索功能,其中用户输入的搜索词可能是更长文本的一部分。
基本语法如下:

1 GET /<index_name>/_search
2 {
3 "query": {
4 "prefix": {
5 "your_field_name": {
6 "value": "your_prefix_string"
7 }
8 }
9 }
10 }
11
12
13
需要注意的是,这种查询方式仅适用于关键字类型(keyword)的字段。
示例

1 # 思考:能否查到数据?
2 GET /employee/_search
3 {
4 "query": {
5 "prefix": {
6 "address": {
7 "value": "广州白云山"
8 }
9 }
10 }
11 }
12
13 GET /employee/_search
14 {
15 "query": {
16 "prefix": {
17 "address.keyword": {
18 "value": "广州白云山"
19 }
20 }
21 }
22 }
23
24
wildcard——通配符匹配
wildcard检索是Elasticsearch中一种支持通配符匹配的查询类型,它允许在检索时使用通配符表达式来
匹配文档的字段值。通配符包括两种。
星号(*):表示零或多个字符,可用于匹配任意长度的字符串。
问号(?):表示一个字符,用于匹配任意单个字符。
wildcard检索适用于对部分已知内容的文本字段进行模糊检索。例如,在文件名或产品型号等具有一定
规律的字段中,使用通配符检索可以方便地找到满足特定模式的文档。
请注意,通配符查询可能会导致较高的计算负担,因此在实际应用中应谨慎使用,尤其是在涉及大量
文档的情况下。
基本语法
基本语法如下:

1
2 GET /<index_name>/_search
3 {
4 "query": {
5 "wildcard": {
6 "your_field_name": {
7 "value": "your_search_pattern"
8 }
9 }
10 }
11 }
12
13
14
示例
1
2 GET /employee/_search
3 {
4 "query": {
5 "wildcard": {
6 "address.keyword": {
7 "value": "*州*公园"
8 }
9 }
10 }
11 }
12
13
regexp——正则匹配查询
regexp检索是一种基于正则表达式的检索方法。虽然该检索方式的功能强大,但建议在非必要情况下
避免使用,以保持查询性能的高效和稳定。
基本语法

在Elasticsearch 8.x中,regexp 查询用于在字段中执行正则表达式匹配。这个查询可以用来搜索满足
特定模式的文本,并且比 wildcard 查询更加灵活和强大。
基本语法如下:
1 GET /<index_name>/_search
2 {
3 "query": {
4 "regexp": {
5 "your_field_name": {
6 "value": "your_search_pattern"
7 }
8 }
9 }
10 }
11
12
13
示例
1
2 GET /employee/_search
3 {
4 "query": {
5 "regexp": {
6 "remark": {
7 "value": "java.*"
8 }
9 }
10 }
11 }
12
13
.* 表示在java后可以跟随任意数量的任意字符
fuzzy——支持编辑距离的模糊查询

fuzzy检索是一种强大的搜索功能,它能够在用户输入内容存在拼写错误或上下文不一致时,仍然返回
与搜索词相似的文档。通过使用编辑距离算法来度量输入词与文档中词条的相似程度,模糊查询在保
证搜索结果相关性的同时,有效地提高了搜索容错能力。
编辑距离是指从一个单词转换到另一个单词需要编辑单字符的次数。如中文集团到中威集团编辑距
离就是1,只需要修改一个字符;如果fuzziness值在这里设置成2,会把编辑距离为2的东东集团也
查出来。
基本语法
基本语法如下:
1 GET /<index_name>/_search
2 {
3 "query": {
4 "fuzzy": {
5 "your_field": {
6 "value": "search_term",
7 "fuzziness": "AUTO",
8 "prefix_length": 1
9 }
10 }
11 }
12 }
13
14
15
fuzziness参数用于编辑距离的设置,其默认值为AUTO,支持的数值为[0,1,2]。如果值设置越界会报错。
prefix_length: 搜索词的前缀长度,在此长度内不会应用模糊匹配。默认是0,即整个词都会被模糊匹配。
示例

1 GET /employee/_search
2 {
3 "query": {
4 "fuzzy": {
5 "address": {
6 "value": "白运山",
7 "fuzziness": 1
8 }
9 }
10 }
11 }
12
13
14
term set——用于解决多值字段中的文档匹配问题
terms set检索是Elasticsearch中一种功能强大的检索类型,主要用于解决多值字段中的文档匹配问
题,在处理具有多个属性、分类或标签的复杂数据时非常有用。
从应用场景来说,terms set检索在处理多值字段和特定匹配条件时具有很大的优势。它适用于标签系
统、搜索引擎、电子商务系统、文档管理系统和技能匹配等场景。
基本语法
terms_set可以检索至少匹配一定数量给定词项的文档,其中匹配的数量可以是固定值,也可以是基于
另一个字段的动态值
基本语法如下:

1 GET /<index_name>/_search
2 {
3 "query": {
4 "terms_set": {
5 "<field_name>": {
6 "terms": ["<term1>", "<term2>", ...],
7 "minimum_should_match_field": "<minimum_should_match_field_name>" or
8 "minimum_should_match_script": {
9 "source": "<script>"
10 }
11 }
12 }
13 }
14 }
15
16
<field_name>: 指定要查询的字段名,这个字段通常是一个多值字段。
terms: 提供一组词项,用于在指定字段中进行匹配。
minimum_should_match_field: 指定一个包含匹配数量的字段名,其值应用作要匹配的最少术语数,以便返回文
档。
minimum_should_match_script: 提供一个自定义脚本,用于动态计算匹配数量。如果需要动态设置匹配所需的术
语数,这个参数将非常有用。
示例
假设我们有一个电影数据库,其中每部电影都有多个标签。现在,我们希望找到同时具有一定数量的
给定标签的电影。
测试数据

1 PUT /movies
2 {
3 "mappings": {
4 "properties": {
5 "title": {
6 "type": "text"
7 },
8 "tags": {
9 "type": "keyword"
10 },
11 "tags_count": {
12 "type": "integer"
13 }
14 }
15 }
16 }
17
18 POST /movies/_bulk
19 {"index":{"_id":1}}
20 {"title":"电影1", "tags":["喜剧","动作","科幻"], "tags_count":3}
21 {"index":{"_id":2}}
22 {"title":"电影2", "tags":["喜剧","爱情","家庭"], "tags_count":3}
23 {"index":{"_id":3}}
24 {"title":"电影3", "tags":["动作","科幻","家庭"], "tags_count":3}
25
26
27
使用固定数量的term进行匹配

1 GET /movies/_search
2 {
3 "query": {
4 "terms_set": {
5 "tags": {
6 "terms": [
7 "喜剧",
8 "动作",
9 "科幻"
10 ],
11 "minimum_should_match": 2
12 }
13 }
14 }
15 }
16
17 GET /movies/_search
18 {
19 "query": {
20 "terms_set": {
21 "tags": {
22 "terms": [
23 "喜剧",
24 "动作",
25 "科幻"
26 ],
27 "minimum_should_match_script": {
28 "source": "2"
29 }
30 }
31 }
32 }
33 }
34
35
36
37
使用动态计算的term数量进行匹配

1
2 GET /movies/_search
3 {
4 "query": {
5 "terms_set": {
6 "tags": {
7 "terms": [
8 "喜剧",
9 "动作",
10 "科幻"
11 ],
12 "minimum_should_match_field": "tags_count"
13 }
14 }
15 }
16 }
17
18
19 GET /movies/_search
20 {
21 "query": {
22 "terms_set": {
23 "tags": {
24 "terms": [
25 "喜剧",
26 "动作",
27 "科幻"
28 ],
29 "minimum_should_match_script": {
30 "source": "doc['tags_count'].value*0.7"
31 }
32 }
33 }
34 }
35 }
36

1.3 全文检索
全文检索查询旨在基于相关性搜索和匹配文本数据。这些查询会对输入的文本进行分析,将其拆分为
词项(单个单词),并执行诸如分词、词干处理和标准化等操作。此类检索主要应用于非结构化文本
数据,如文章和评论等。
match——分词查询
match查询是一种全文搜索查询,它使用分析器将查询字符串分解成单独的词条,并在倒排索引中搜索
这些词条。match查询适用于文本字段,并且可以通过多种参数来调整搜索行为。
对于match查询,其底层逻辑的概述:
1.分词:首先,输入的查询文本会被分词器进行分词。分词器会将文本拆分成一个个词项(terms),
如单词、短语或特定字符。分词器通常根据特定的语言规则和配置进行操作。
2.匹配计算:一旦查询被分词,ES将根据查询的类型和参数计算文档与查询的匹配度。对于match查
询,ES将比较查询的词项与倒排索引中的词项,并计算文档的相关性得分。相关性得分衡量了文档与
查询的匹配程度。
3.结果返回:根据相关性得分,ES将返回最匹配的文档作为搜索结果。搜索结果通常按照相关性得分
进行排序,以便最相关的文档排在前面。
基本语法
一个基本的match查询的结构如下:
1 GET /<index_name>/_search
2 {
3 "query": {
4 "match": {
5 "<field_name>": "<query_string>"
6 }
7 }
8 }
9
<index_name> 是你要搜索的索引名称。
<field_name> 是你要在其中搜索的字段名称。
<query_string> 是你要搜索的文本字符串。
示例

1 #分词后or的效果
2 GET /employee/_search
3 {
4 "query": {
5 "match": {
6 "address": "广州白云山公园"
7 }
8 }
9 }
10
11 # 分词后 and的效果
12 GET /employee/_search
13 {
14 "query": {
15 "match": {
16 "address": {
17 "query": "广州白云山公园",
18 "operator": "and"
19 }
20 }
21 }
22 }
23
24
在match中的应用: 当operator参数设置为or时,minnum_should_match参数用来控制匹配的分词的
最少数量。

1 # 最少匹配广州,公园两个词
2 GET /employee/_search
3 {
4 "query": {
5 "match": {
6 "address": {
7 "query": "广州公园",
8 "minimum_should_match": 2
9 }
10 }
11 }
12 }
13
14
multi_match——多字段查询
multi_match查询在Elasticsearch中用于在多个字段上执行相同的搜索操作。它可以接受一个查询字符
串,并在指定的字段集合中搜索这个字符串。multi_match查询提供了灵活的匹配类型和操作符选项,
以便根据不同的搜索需求调整搜索行为。
基本语法
一个基本的multi_match查询的结构如下:
1 GET /<index_name>/_search
2 {
3 "query": {
4 "multi_match": {
5 "query": "<query_string>",
6 "fields": ["<field1>", "<field2>", ...]
7 }
8 }
9 }
10
<index_name> 是你要搜索的索引名称。
<query_string> 是你要在多个字段中搜索的字符串。

<field1>, <field2>, ... 是你要搜索的字段列表。
示例
1 GET /employee/_search
2 {
3 "query": {
4 "multi_match": {
5 "query": "长沙java",
6 "fields": [
7 "address",
8 "remark"
9 ]
10 }
11 }
12 }
match_phrase短语查询
match_phrase查询在Elasticsearch中用于执行短语搜索,它不仅匹配整个短语,而且还考虑了短语中
各个词的顺序和位置。这种查询类型对于搜索精确短语非常有用,尤其是在用户输入的查询与文档中
的文本表达方式需要严格匹配时。
基本语法
一个基本的match_phrase查询的结构如下:
1 GET /<index_name>/_search
2 {
3 "query": {
4 "match_phrase": {
5 "<field_name>": {
6 "query": "<phrase>"
7 }
8 }
9 }
10 }
11
<index_name> 是你要搜索的索引名称。

<field_name> 是你要在其中搜索短语的字段名称。
<phrase> 是你要搜索的短语。
match_phrase查询还支持一个可选的slop参数,用于指定短语中词之间可以出现的最大位移数量。默
认值为0,意味着短语中的词必须严格按照顺序出现。如果设置了非零的slop值,则允许短语中的某些
词在一定范围内错位。
示例
1 GET /employee/_search
2 {
3 "query": {
4 "match_phrase": {
5 "address": "广州白云山"
6 }
7 }
8 }
9
10
11 GET /employee/_search
12 {
13 "query": {
14 "match_phrase": {
15 "address": "广州白云"
16 }
17 }
18 }
19
20
思考:为什么查询广州白云山有数据,广州白云没有数据?
分析原因:
先查看广州白云山公园分词结果,可以知道广州和白云不是相邻的词条,中间会隔一个白云山,而
match_phrase匹配的是相邻的词条,所以查询广州白云山有结果,但查询广州白云没有结果。

1 POST _analyze
2 {
3 "analyzer":"ik_max_word",
4 "text":"广州白云山"
5 }
6 #结果
7 {
8 "tokens" : [
9 {
10 "token" : "广州",
11 "start_offset" : 0,
12 "end_offset" : 2,
13 "type" : "CN_WORD",
14 "position" : 0
15 },
16 {
17 "token" : "白云山",
18 "start_offset" : 2,
19 "end_offset" : 5,
20 "type" : "CN_WORD",
21 "position" : 1
22 },
23 {
24 "token" : "白云",
25 "start_offset" : 2,
26 "end_offset" : 4,
27 "type" : "CN_WORD",
28 "position" : 2
29 },
30 {
31 "token" : "云山",
32 "start_offset" : 3,
33 "end_offset" : 5,
34 "type" : "CN_WORD",
35 "position" : 3
36 }
37 ]
38 }

39
如何解决词条间隔的问题?可以借助slop参数,slop参数告诉match_phrase查询词条能够相隔多远时
仍然将文档视为匹配。
1 #广州云山分词后相隔为2,可以匹配到结果
2 GET /employee/_search
3 {
4 "query": {
5 "match_phrase": {
6 "address": {
7 "query": "广州云山",
8 "slop": 2
9 }
10 }
11 }
12 }
13
14
query_string——支持与或非表达式的查询
query_string查询是一种灵活的查询类型,它允许使用Lucene查询语法来构建复杂的搜索查询。这种查
询类型支持多种逻辑运算符,包括与(AND)、或(OR)和非(NOT),以及通配符、模糊搜索和正
则表达式等功能。query_string查询可以在单个或多个字段上进行搜索,并且可以处理复杂的查询逻
辑。
应用场景包括高级搜索、数据分析和报表等,适合处理需满足特定需求、要求支持与或非表达式的复
杂查询任务,通常用于专业领域或需要高级查询功能的应用中。
基本语法
query_string查询的基本语法结构如下:

1 GET /<index_name>/_search
2 {
3 "query": {
4 "query_string": {
5 "query": "<your_query_string>",
6 "default_field": "<field_name>"
7 }
8 }
9 }
<your_query_string> 是查询逻辑,可以包含上述提到的逻辑运算符和通配符等
<field_name> 是默认搜索字段,如果省略则会搜索所有可索引字段。
示例
未指定字段查询
1 # AND 要求大写
2 GET /employee/_search
3 {
4 "query": {
5 "query_string": {
6 "query": "赵六 AND 橘子洲"
7 }
8 }
9 }
指定单个字段查询

1
2 GET /employee/_search
3 {
4 "query": {
5 "query_string": {
6 "default_field": "address",
7 "query": "白云山 OR 橘子洲"
8 }
9 }
10 }
注意: 查询字段分词就将查询条件分词查询,查询字段不分词将查询条件不分词查询
指定多个字段查询
1 GET /employee/_search
2 {
3 "query": {
4 "query_string": {
5 "fields": ["name","address"],
6 "query": "张三 OR (广州 AND 王五)"
7 }
8 }
9 }
10
simple_query_string
类似Query String,但是会忽略错误的语法,同时只支持部分查询语法,不支持AND OR NOT,会当作
字符串处理。支持部分逻辑:
+ 替代AND
| 替代OR
- 替代NOT
在生产环境中推荐使用 simple_query_string 而不是 query_string 主要是因为
simple_query_string 提供了更宽松的语法,能够容忍一定程度的输入错误,而不会导致整个
查询失败。

基本语法
simple_query_string 查询的基本语法结构通常如下所示:
1 GET /<index_name>/_search
2 {
3 "query": {
4 "simple_query_string": {
5 "query": "<query_string>",
6 "fields": ["<field1>", "<field2>", ...],
7 "default_operator": "OR" // 或 "AND"
8 }
9 }
10 }
其中 <query_string> 是要搜索的查询表达式,<field1>, <field2>, ... 是搜索可以在其中进行的字段列
表,default_operator 定义了查询字符串中未指定操作符时的默认逻辑运算符,可以是 "OR" 或
"AND"。
示例

1 #simple_query_string 默认的operator是OR
2 GET /employee/_search
3 {
4 "query": {
5 "simple_query_string": {
6 "fields": ["name","address"],
7 "query": "广州公园",
8 "default_operator": "AND"
9 }
10 }
11 }
12
13 GET /employee/_search
14 {
15 "query": {
16 "simple_query_string": {
17 "fields": ["name","address"],
18 "query": "广州 + 公园"
19 }
20 }
21 }
小结
精确匹配与全文检索的本质区别主要表现在两个方面:
精确不对待检索文本进行分词处理,而是将整个文本视为一个完整的词条进行匹配。
全文检索则需要对文本进行分词处理。在分词后,每个词条将单独进行检索,并通过布尔逻辑(如与、或、非
等)进行组合检索,以找到最相关的结果。
1.4 bool query布尔查询
布尔查询可以按照布尔逻辑条件组织多条查询语句,只有符合整个布尔条件的文档才会被搜索出来。
在布尔条件中,可以包含两种不同的上下文。
1. 搜索上下文(query context):使用搜索上下文时,Elasticsearch需要计算每个文档与搜索条件的相关度得分,这
个得分的计算需使用一套复杂的计算公式,有一定的性能开销,带文本分析的全文检索的查询语句很适合放在搜
索上下文中。

2. 过滤上下文(filter context):使用过滤上下文时,Elasticsearch只需要判断搜索条件跟文档数据是否匹配,例如
使用Term query判断一个值是否跟搜索内容一致,使用Range query判断某数据是否位于某个区间等。过滤上下
文的查询不需要进行相关度得分计算,还可以使用缓存加快响应速度,很多术语级查询语句都适合放在过滤上下
文中。
布尔查询一共支持4种组合类型:
类型 说明
可包含多个查询条件,每个条件均满足的文档才
must 能被搜索到,每次查询需要计算相关度得分,属
于搜索上下文
可包含多个查询条件,不存在must和fiter条件
时,至少要满足多个查询条件中的一个,文档才
should
能被搜索到,否则需满足的条件数量不受限制,匹
配到的查询越多相关度越高,也属于搜索上下文
可包含多个过滤条件,每个条件均满足的文档才
filter 能被搜索到,每个过滤条件不计算相关度得分,
结果在一定条件下会被缓存, 属于过滤上下文
可包含多个过滤条件,每个条件均不满足的文档
才能被搜索到,每个过滤条件不计算相关度得
must_not
分,结果在一定条件下会被缓存, 属于过滤上下
文
示例

1 PUT /books
2 {
3 "settings": {
4 "number_of_replicas": 1,
5 "number_of_shards": 1
6 },
7 "mappings": {
8 "properties": {
9 "id": {
10 "type": "long"
11 },
12 "title": {
13 "type": "text",
14 "analyzer": "ik_max_word"
15 },
16 "language": {
17 "type": "keyword"
18 },
19 "author": {
20 "type": "keyword"
21 },
22 "price": {
23 "type": "double"
24 },
25 "publish_time": {
26 "type": "date",
27 "format": "yyyy-MM-dd"
28 },
29 "description": {
30 "type": "text",
31 "analyzer": "ik_max_word"
32 }
33 }
34 }
35 }
36
37 POST /_bulk
38 {"index":{"_index":"books","_id":"1"}}

39 {"id":"1", "title":"Java编程思想", "language":"java", "author":"Bruce Eckel",
"price":70.20, "publish_time":"2007-10-01", "description":"Java学习必读经典,殿堂级著作!
赢得了全球程序员的广泛赞誉。"}
40 {"index":{"_index":"books","_id":"2"}}
41 {"id":"2","title":"Java程序性能优化","language":"java","author":"葛一
鸣","price":46.5,"publish_time":"2012-08-01","description":"让你的Java程序更快、更稳定。
深入剖析软件设计层面、代码层面、JVM虚拟机层面的优化方法"}
42 {"index":{"_index":"books","_id":"3"}}
43 {"id":"3","title":"Python科学计算","language":"python","author":"张若
愚","price":81.4,"publish_time":"2016-05-01","description":"零基础学python,光盘中作者独
家整合开发winPython运行环境,涵盖了Python各个扩展库"}
44 {"index":{"_index":"books","_id":"4"}}
45 {"id":"4", "title":"Python基础教程", "language":"python", "author":"Helant",
"price":54.50, "publish_time":"2014-03-01", "description":"经典的Python入门教程,层次鲜
明,结构严谨,内容翔实"}
46 {"index":{"_index":"books","_id":"5"}}
47 {"id":"5","title":"JavaScript高级程序设计","language":"javascript","author":"Nicholas
C. Zakas","price":66.4,"publish_time":"2012-10-01","description":"JavaScript技术经典名
著"}
48
49
50 GET /books/_search
51 {
52 "query": {
53 "bool": {
54 "must": [
55 {
56 "match": {
57 "title": "java编程"
58 }
59 },{
60 "match": {
61 "description": "性能优化"
62 }
63 }
64 ]
65 }
66 }
67 }
68
69 GET /books/_search
70 {
71 "query": {

72 "bool": {
73 "should": [
74 {
75 "match": {
76 "title": "java编程"
77 }
78 },{
79 "match": {
80 "description": "性能优化"
81 }
82 }
83 ],
84 "minimum_should_match": 1
85 }
86 }
87 }
88 GET /books/_search
89 {
90 "query": {
91 "bool": {
92 "filter": [
93 {
94 "term": {
95 "language": "java"
96 }
97 },
98 {
99 "range": {
100 "publish_time": {
101 "gte": "2010-08-01"
102 }
103 }
104 }
105 ]
106 }
107 }
108 }
1.5 highlight高亮

highlight 关键字: 可以让符合条件的文档中的关键词高亮。
highlight相关属性:
pre_tags 前缀标签
post_tags 后缀标签
tags_schema 设置为styled可以使用内置高亮样式
require_field_match 多字段高亮需要设置为false
示例

1 #指定ik分词器
2 PUT /products
3 {
4 "settings" : {
5 "index" : {
6 "analysis.analyzer.default.type": "ik_max_word"
7 }
8 }
9 }
10
11 PUT /products/_doc/1
12 {
13 "proId" : "2",
14 "name" : "牛仔男外套",
15 "desc" : "牛仔外套男装春季衣服男春装夹克修身休闲男生潮牌工装潮流头号青年春秋棒球服男 7705浅
蓝常规 XL",
16 "timestamp" : 1576313264451,
17 "createTime" : "2019-12-13 12:56:56"
18 }
19
20 PUT /products/_doc/2
21 {
22 "proId" : "6",
23 "name" : "HLA海澜之家牛仔裤男",
24 "desc" : "HLA海澜之家牛仔裤男2019时尚有型舒适HKNAD3E109A 牛仔蓝(A9)175/82A(32)",
25 "timestamp" : 1576314265571,
26 "createTime" : "2019-12-18 15:56:56"
27 }
28
29 GET /products/_search
30 {
31 "query": {
32 "term": {
33 "name": {
34 "value": "牛仔"
35 }
36 }
37 },
38 "highlight": {
39 "fields": {

40 "*":{}
41 }
42 }
43 }
自定义高亮html标签
可以在highlight中使用pre_tags和post_tags
1 GET /products/_search
2 {
3 "query": {
4 "multi_match": {
5 "fields": ["name","desc"],
6 "query": "牛仔"
7 }
8 },
9 "highlight": {
10 "post_tags": ["</span>"],
11 "pre_tags": ["<span style='color:red'>"],
12 "fields": {
13 "*":{}
14 }
15 }
16 }
多字段高亮

1
2 GET /products/_search
3 {
4 "query": {
5 "term": {
6 "name": {
7 "value": "牛仔"
8 }
9 }
10 },
11 "highlight": {
12 "pre_tags": ["<font color='red'>"],
13 "post_tags": ["<font/>"],
14 "require_field_match": "false",
15 "fields": {
16 "name": {},
17 "desc": {}
18 }
19 }
20 }
21
require_field_match: 该设置控制是否需要所有指定的高亮字段都匹配搜索查询,才能应用高亮。当设置为false
时,只要任意一个字段匹配,该文档的匹配部分就会被高亮。如果设置为true,则所有指定的字段都必须匹配查
询条件。
1.6 地理空间位置查询
地理空间位置查询是数据库和搜索系统中的一个重要特性,特别是在地理信息系统(GIS)和位置服务
中。它允许用户基于地理位置信息来搜索和过滤数据。在Elasticsearch这样的全文搜索引擎中,地理
空间位置查询被广泛应用,例如在旅行、房地产、物流和零售等行业,用于提供基于位置的搜索功
能。
在Elasticsearch中,地理空间数据通常存储在geo_point字段类型中。这种字段类型可以存储纬度和经
度坐标,用于表示地球上的一个点。
以下是一个使用geo_distance查询的例子,它会找到距离特定点一定距离内的所有文档。
1)确保索引中有一个geo_point字段,例如location。

1 PUT /my_index
2 {
3 "mappings": {
4 "properties": {
5 "location": {
6 "type": "geo_point"
7 }
8 }
9 }
10 }
2)使用以下查询来找到距离给定坐标点(例如lat和lon)小于或等于10公里的所有文档:
1 GET /my_index/_search
2 {
3 "query": {
4 "bool": {
5 "must": {
6 "match_all": {}
7 },
8 "filter": {
9 "geo_distance": {
10 "distance": "10km",
11 "distance_type": "arc",
12 "location": {
13 "lat": 39.9,
14 "lon": 116.4
15 }
16 }
17 }
18 }
19 }
20 }
在这个查询中:
"bool" 是一个逻辑查询容器,用于组合多个查询子句。
"match_all" 是一个匹配所有文档的查询子句。

"geo_distance" 是一个地理距离查询,它允许您指定一个距离和一个点的坐标。
"distance" 是查询的最大距离,单位可以是米(m)、公里(km)等。
"distance_type" 可以是 arc(以地球表面的弧长为单位)或 plane(以直线距离为单位)。通常对于地球上的距
离查询,建议使用 arc。
"location" 是查询的参考点,包含纬度和经度坐标。
这个查询将返回索引my_index中location字段在给定坐标点10公里范围内的所有文档。
示例
假设我们正在管理一个记录中国各地著名景点的索引,每个景点都带有地理坐标。以下是一些示例数
据:

1 # 创建索引
2 PUT /tourist_spots
3 {
4 "mappings": {
5 "properties": {
6 "name": {
7 "type": "text",
8 "analyzer": "ik_max_word",
9 "search_analyzer": "ik_max_word"
10 },
11 "location": {
12 "type": "geo_point"
13 }
14 }
15 }
16 }
17
18 # 插入文档
19 POST /tourist_spots/_doc
20 {
21 "name": "故宫博物院",
22 "location": {
23 "lat": 39.9159,
24 "lon": 116.3945
25 },
26 "city": "北京"
27 }
28
29 POST /tourist_spots/_doc
30 {
31 "name": "西湖",
32 "location": {
33 "lat": 30.2614,
34 "lon": 120.1479
35 },
36 "city": "杭州"
37 }
38
39 POST /tourist_spots/_doc

40 {
41 "name": "雷峰塔",
42 "location": {
43 "lat": 30.2511,
44 "lon": 120.1347
45 },
46 "city": "杭州"
47 }
48
49 POST /tourist_spots/_doc
50 {
51 "name": "苏堤春晓",
52 "location": {
53 "lat": 30.2584,
54 "lon": 120.1383
55 },
56 "city": "杭州"
57 }
58
59 # 搜索包含故宫或博物院的景点:
60 GET /tourist_spots/_search
61 {
62 "query": {
63 "match": {
64 "name": "故宫 博物院"
65 }
66 }
67 }
68 # 查询北京附近的景点
69 GET /tourist_spots/_search
70 {
71 "query": {
72 "bool": {
73 "must": {
74 "match_all": {}
75 },
76 "filter": {
77 "geo_distance": {
78 "distance": "10km",
79 "distance_type": "arc",

80 "location": {
81 "lat": 39.9159,
82 "lon": 116.3945
83 }
84 }
85 }
86 }
87 }
88 }
89 # 查询杭州西湖5km附近的景点
90 #雷峰塔 - 位于西湖附近,距离约2.8公里。
91 #苏堤春晓 - 位于西湖边,距离西湖中心约1公里。
92 GET /tourist_spots/_search
93 {
94 "query": {
95 "bool": {
96 "must": {
97 "match_all": {}
98 },
99 "filter": {
100 "geo_distance": {
101 "distance": "5km",
102 "distance_type": "arc",
103 "location": {
104 "lat": 30.2614,
105 "lon": 120.1479
106 }
107 }
108 }
109 }
110 }
111 }
112
113
1.7 ElasticSearch8.x 向量检索

Elasticsearch 8.x 引入了一个重要的新特性:向量检索(Vector Search),特别是通过KNN(K-
Nearest Neighbors)算法支持向量近邻检索。这一特性使得Elasticsearch在机器学习、数据分析和推
荐系统等领域的应用变得更加广泛和强大。
向量检索的基本思路是,将文档(或数据项)表示为高维向量,并使用这些向量来执行相似性搜索。
在Elasticsearch中,这些向量被存储在dense_vector类型的字段中,然后使用KNN算法来找到与给
定向量最相似的其他向量。
向量检索示例1

1 PUT image-index
2 {
3 "mappings": {
4 "properties": {
5 "image-vector": {
6 "type": "dense_vector",
7 "dims": 3
8 },
9 "title": {
10 "type": "text"
11 },
12 "file-type": {
13 "type": "keyword"
14 },
15 "my_label": {
16 "type": "text"
17 }
18 }
19 }
20 }
21
22 POST image-index/_bulk
23 { "index": {} }
24 { "image-vector": [-5, 9, -12], "title": "Image A", "file-type": "jpeg", "my_label":
"red" }
25 { "index": {} }
26 { "image-vector": [10, -2, 3], "title": "Image B", "file-type": "png", "my_label":
"blue" }
27 { "index": {} }
28 { "image-vector": [4, 0, -1], "title": "Image C", "file-type": "gif", "my_label":
"red" }
29
30 POST image-index/_search
31 {
32 "knn": {
33 "field": "image-vector",
34 "query_vector": [-5, 10, -12],
35 "k": 10,
36 "num_candidates": 100
37 },

38 "fields": [ "title", "file-type" ]
39 }
向量检索示例2
假设我们正在构建一个推荐系统,该系统基于用户对电影的评分向量来推荐相似电影。我们将使用
Elasticsearch的向量检索功能来实现这一需求。
首先,我们需要创建一些测试数据,包括几部电影的评分向量。以下是一些示例数据:

1 # 创建索引
2 # 指定了rating_vector为5维的稠密向量,并启用了向量索引,同时选择了dot_product作为相似度计算方
式。
3 PUT /movies
4 {
5 "mappings": {
6 "properties": {
7 "rating_vector": {
8 "type": "dense_vector",
9 "dims": 5
10 }
11 }
12 }
13 }
14 # 插入文档
15 # rating_vector字段存储了每部电影的评分向量,向量的维度为5。
16 POST /movies/_doc
17 {
18 "title": "肖申克的救赎",
19 "year": 1994,
20 "genre": "犯罪",
21 "rating_vector": [0.1, 0.3, 0.5, 0.7, 0.9]
22 }
23
24 POST /movies/_doc
25 {
26 "title": "阿甘正传",
27 "year": 1994,
28 "genre": "剧情",
29 "rating_vector": [0.2, 0.4, 0.6, 0.8, 1.0]
30 }
31
32 POST /movies/_doc
33 {
34 "title": "泰坦尼克号",
35 "year": 1997,
36 "genre": "爱情",
37 "rating_vector": [0.15, 0.35, 0.55, 0.75, 0.95]
38 }

测试用例1: 查询与《肖申克的救赎》评分向量最相似的电影
1 GET /movies/_search
2 {
3 "knn": {
4 "field": "rating_vector",
5 "query_vector": [
6 0.1,
7 0.3,
8 0.5,
9 0.7,
10 0.9
11 ],
12 "k": 1
13 }
14 }
预期结果:返回与查询向量最相似的电影,应该是肖申克的救赎。
测试用例2: 查询与自定义向量[0.2, 0.4, 0.6, 0.8, 1.0]最相似的电影
1 GET /movies/_search
2 {
3 "knn": {
4 "field": "rating_vector",
5 "query_vector": [
6 0.2,
7 0.4,
8 0.6,
9 0.8,
10 1
11 ],
12 "k": 1
13 }
14 }
预期结果:返回与查询向量最相似的电影,应该是阿甘正传。
