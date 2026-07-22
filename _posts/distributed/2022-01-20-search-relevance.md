---
title: "1 搜索相关性详解"
description: "主讲老师:Fox 有道云笔记地址:https://note.youdao.com/s/PJRhfowf 1. 相关性的概述 什么是相关性(Relevance) 搜索是用户和搜索引擎的对话,用户关心的是搜索结果的相关性 是否可以找到所有相关的内容 有多少不相关的内容被返回了 文档的打分是否合理 结合业务需求,平衡结果排名 相关性是指在搜索引擎中,描述一个文档与查询语句匹配程度的度量标准。这种相..."
author: hsc
date: 2022-01-20 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', 'Redis', 'Kafka', 'RocketMQ', 'Netty', 'ElasticSearch', 'ShardingSphere']
toc: true
---

> 本文整理自《四、分布式专题》课程笔记，共 27 页。

主讲老师:Fox
有道云笔记地址:https://note.youdao.com/s/PJRhfowf
1. 相关性的概述
什么是相关性(Relevance)
搜索是用户和搜索引擎的对话,用户关心的是搜索结果的相关性
是否可以找到所有相关的内容
有多少不相关的内容被返回了
文档的打分是否合理
结合业务需求,平衡结果排名
相关性是指在搜索引擎中,描述一个文档与查询语句匹配程度的度量标准。这种相关性通过为每个匹
配查询条件的文档计算一个相关性评分(_score)来实现,评分越高表示文档与查询语句的匹配程度
越高
如下例子:显而易见,查询JAVA多线程设计模式,文档id为2,3的文档的算分更高
关键词 文档ID
JAVA 1,2,3
设计模式 1,2,3,4,5,6
多线程 2,3,7,9
Elasticsearch使用评分算法,根据查询条件与索引文档的匹配程度来确定每个文档的相关性。同时,
为了满足各种特定的业务需求,Elasticsearch也充分允许用户自定义评分。
在下面示例中,_score就是Elasticsearch检索返回的评分,其值可以衡量每个文档与查询的匹配程
度,即相关性。每个文档都有对应的评分,该得分由正浮点数表示。文档评分越高,则该文档的相关
性越高。
计算相关性评分
Elasticsearch使用布尔模型查找匹配文档,并用一个名为“实用评分函数”的公式来计算相关性。这个公
式借鉴了TF-IDF(词频-逆向文档频率)和向量空间模型,同时加入了一些现代的新特性,如协调因
子、字段长度归一化以及词/查询语句权重提升。

Elasticsearch 5之前的版本,评分机制或者打分模型是基于TF-IDF实现的。从Elasticsearch 5之后,默
认的打分机制改成了Okapi BM25。其中BM是Best Match的缩写,25是指经过25次迭代调整之后得出
的算法,它是由TF-IDF机制进化来的。
传统TF-IDF和BM25都使用逆向文档频率来区分普通词(不重要)和非普通词(重要) ,使用词频来衡
量某个词在文档中出现的频率。两种机制的逻辑相似:首先,文档里的某个词出现得越频繁,文档与
这个词就越相关,得分越高;其次,某个词在集合中所有文档里出现的频次越高,则它的权重越低、
得分越低。也就是说,某个词在集合中所有文档里越罕见,其得分越高。BM25在传统TF-IDF的基础上
增加了几个可调节的参数,使得它在应用上更佳灵活和强大,具有较高的实用性。
TF-IDF评分公式:
TF是词频(Term Frequency)
检索词在文档中出现的频率越高,相关性也越高。
1 词频(TF) = 某个词在文档中出现的次数 / 文档的总词数
IDF是逆向文本频率(Inverse Document Frequency)
每个检索词在索引中出现的频率,频率越高,相关性越低。总文档中有些词比如“是”、“的” 、“在” 在所
有文档中出现频率都很高,并不重要,可以减少多个文档中都频繁出现的词的权重。
1 逆向文本频率(IDF)= log (语料库的文档总数 / (包含该词的文档数+1))
字段长度归一值( field-length norm)
检索词出现在一个内容短的 title 要比同样的词出现在一个内容长的 content 字段权重更大。
以上三个因素——词频(term frequency)、逆向文本频率(inverse document frequency)和字段长
度归一值(field-length norm)——是在索引时计算并存储的,最后将它们结合在一起计算单个词在特
定文档中的权重。
BM25 就是对 TF-IDF 算法的改进,对于 TF-IDF 算法,TF(t) 部分的值越大,整个公式返回的值就会越
大。BM25 就针对这点进行来优化,随着TF(t) 的逐步加大,该算法的返回值会趋于一个数值。
BM 25的公式
示例:通过Explain API查看TF-IDF

1 PUT /test_score/_bulk
2 {"index":{"_id":1}}
3 {"content":"we use Elasticsearch to power the search"}
4 {"index":{"_id":2}}
5 {"content":"we like elasticsearch"}
6 {"index":{"_id":3}}
7 {"content":"Thre scoring of documents is caculated by the scoring formula"}
8 {"index":{"_id":4}}
9 {"content":"you know,for search"}
10
11 GET /test_score/_search
12 {
13 "explain": true,
14 "query": {
15 "match": {
16 "content": "elasticsearch"
17 }
18 }
19 }
20
21 GET /test_score/_explain/2
22 {
23 "query": {
24 "match": {
25 "content": "elasticsearch"
26 }
27 }
28 }
Elasticsearch自定义评分
自定义评分是用来优化Elasticsearch默认评分算法的一种有效方法,可以更好地满足特定应用场景的
需求。
自定义评分的核心是通过修改评分来修改文档相关性,在最前面的位置返回用户最期望的结果。
Elasticsearch自定义评分的主要作用如下:
1) 排序偏好:通过在搜索结果中给每个文档自定义评分,可以更好地满足搜索用户的排序偏好。
2) 特殊字段权重:通过给特定字段赋予更高的权重,可以让这些字段对搜索结果的影响更大。
3) 业务逻辑需求:根据业务需求,可以定义复杂的评分逻辑,使搜索结果更符合业务需求。

4) 自定义用户行为:可以使用用户行为数据(如点击率)作为评分因素,提高用户搜索体验。
搜索结果相关性与自定义评分的关系
搜索引擎本质是一个匹配过程,即从海量的数据中找到匹配用户需求的内容。判定内容与用户查询的
相关性一直是搜索引擎领域的核心研究课题之一。如果搜索引擎不能准确地识别用户查询的意图并将
相关结果排在前面的位置,那么搜索结果就不能满足用户的需求,从而影响用户对搜索引擎的满意
度。
如上图所示,左侧圆圈代表用户期望通过搜索引擎获取的结果,右侧圆圈代表用户最终得到的结果。
左右两个圆的交集部分即为预期结果与实际结果的相关性。
2. 自定义评分的策略
然而,如何实现这样的自定义评分策略,以确保搜索结果能够最大限度地满足用户需求呢?我们可以
从多个层面,包括索引层面、查询层面以及后处理阶段着手。
以下是几种主要的自定义评分策略:
Index Boost: 在索引层面修改相关性
boosting: 修改文档相关性
negative_boost: 降低相关性
function_score: 自定义评分
rescore_query:查询后二次打分
Index Boost: 在索引层面修改相关性
Index Boost这种方式能在跨多个索引搜索时为每个索引配置不同的级别。所以它适用于索引级别调整
评分。
实战举例:一批数据里有不同的标签,数据结构一致,要将不同的标签存储到不同的索引(A、B、C),
并严格按照标签来分类展示(先展示A类,然后展示B类,最后展示C类) ,应该用什么方式查询呢?
具体实现如下。借助indices_boost提升索引的权重,让A排在最前,其次是B,最后是C。

1 PUT my_index_100a/_doc/1
2 {
3 "subject":"subject 1"
4 }
5 PUT my_index_100b/_doc/1
6 {
7 "subject":"subject 1"
8 }
9 PUT my_index_100c/_doc/1
10 {
11 "subject":"subject 1"
12 }
13
14 POST my_index_100*/_search
15 {
16 "query": {
17 "term": {
18 "subject.keyword": {
19 "value": "subject 1"
20 }
21 }
22 }
23 }
24
25 POST my_index_100*/_search
26 {
27 "query": {
28 "term": {
29 "subject.keyword": {
30 "value": "subject 1"
31 }
32 }
33 },
34 "indices_boost": [
35 {
36 "my_index_100a": 1.5
37 },
38 {
39 "my_index_100b": 1.2

40 },
41 {
42 "my_index_100c": 1
43 }
44 ]
45 }
boosting: 修改文档相关性
boosting可在查询时修改文档的相关度。boosting值所在范围不同,含义也不同。
若boosting值为0~1,如0.2,代表降低评分;
若boosting值>1,如1.5,则代表提升评分。
适用于某些特定的查询场景,用户可以自定义修改满足某个查询条件的结果评分。

1 POST /blogs/_bulk
2 {"index":{"_id":1}}
3 {"title":"Apple iPad","content":"Apple iPad,Apple iPad"}
4 {"index":{"_id":2}}
5 {"title":"Apple iPad,Apple iPad","content":"Apple iPad"}
6
7 GET /blogs/_search
8 {
9 "query": {
10 "bool": {
11 "should": [
12 {
13 "match": {
14 "title": {
15 "query": "apple,ipad",
16 "boost": 4
17 }
18 }
19 },
20 {
21 "match": {
22 "content": {
23 "query": "apple,ipad",
24 "boost": 1
25 }
26 }
27 }
28 ]
29 }
30 }
31 }
negative_boost: 降低相关性
若对某些返回结果不满意,但又不想将其排除(must_not),则可以考虑采用negative_boost的方式。
原理说明如下:
negative_boost仅对查询中定义为negative的部分生效。
计算评分时,不修改boosting部分评分,而negative部分的评分则乘以negative_boost的值。
negative_boost取值为0~1.0,如0.3。

案例:要求苹果公司的产品信息优先展示

1 POST /news/_bulk
2 {"index":{"_id":1}}
3 {"content":"Apple Mac"}
4 {"index":{"_id":2}}
5 {"content":"Apple iPad"}
6 {"index":{"_id":3}}
7 {"content":"Apple employee like Apple Pie and Apple Juice"}
8
9
10 GET /news/_search
11 {
12 "query": {
13 "bool": {
14 "must": {
15 "match": {
16 "content": "apple"
17 }
18 }
19 }
20 }
21 }
22
23 # 利用must not排除不是苹果公司产品的文档
24 GET /news/_search
25 {
26 "query": {
27 "bool": {
28 "must": {
29 "match": {
30 "content": "apple"
31 }
32 },
33 "must_not": {
34 "match":{
35 "content": "pie"
36 }
37 }
38 }
39 }

40 }
41 # 利用negative_boost降低相关性
42 GET /news/_search
43 {
44 "query": {
45 "boosting": {
46 "positive": {
47 "match": {
48 "content": "apple"
49 }
50 },
51 "negative": {
52 "match": {
53 "content": "pie"
54 }
55 },
56 "negative_boost": 0.2
57 }
58 }
59 }
function_score: 自定义评分
该方式支持用户自定义一个或多个查询语句及脚本,达到精细化控制评分的目的,以对搜索结果进行
高度个性化的排序设置。适用于需进行复杂查询的自定义评分业务场景。
案例1:商品信息如下,如何同时根据销量和浏览人数进行相关度提升?
商品 销量 浏览人数
A 10 10
B 20 20
想要提升相关度评分,则将每个文档的原始评分与其销量和浏览人数相结合,得到一个新的评分。例
如,使用如下公式:
评分=原始评分×(销量+浏览人数)
这样,销量和浏览人数较高的文档就会有更高的评分,从而在搜索结果中排名更靠前。这种评分方式
不仅考虑了文档与查询的匹配度(由_score表示) ,还考虑了文档的销量和浏览人数,非常适用于电
子商务等场景。

该需求可以借助script_score实现,代码如下,其评分是基于原始评分和销量与浏览人数之和的乘积计
算的结果。
1 PUT my_index_products/_bulk
2 {"index":{"_id":1}}
3 {"name":"A","sales":10,"visitors":10}
4 {"index":{"_id":2}}
5 {"name":"B","sales":20,"visitors":20}
6 {"index":{"_id":3}}
7 {"name":"C","sales":30,"visitors":30}
8
9 #基于function_score实现自定义评分检索
10 POST my_index_products/_search
11 {
12 "query": {
13 "function_score": {
14 "query": {
15 "match_all": {}
16 },
17 "script_score": {
18 "script": {
19 "source": "_score*(doc['sales'].value+doc['visitors'].value)"
20 }
21 }
22 }
23 }
24 }
rescore_query:查询后二次打分
二次评分是指重新计算查询所返回的结果文档中指定文档的得分。
Elasticsearch会截取查询返回的前N条结果,并使用预定义的二次评分方法来重新计算其得分。但对全
部有序的结果集进行重新排序的话,开销势必很大,使用rescore_query可以只对结果集的子集进行处
理。该方式适用于对查询语句的结果不满意,需要重新打分的场景。

1 PUT my_index_books-demo/_bulk
2 {"index":{"_id":"1"}}
3 {"title":"ES实战","content":"ES的实战操作,实战要领,实战经验"}
4 {"index":{"_id":"2"}}
5 {"title":"MySQL实战","content":"MySQL的实战操作"}
6 {"index":{"_id":"3"}}
7 {"title":"MySQL","content":"MySQL一定要会"}
8
9 GET my_index_books-demo/_search
10 {
11 "query": {
12 "match": {
13 "content": "实战"
14 }
15 }
16 }
17
18 # 查询content字段中包含”实战“的文档,权重为0.7。
19 # 并对文档中title为MySQL的文档增加评分,权重为1.2,
20 # window_size为50,表示取分片结果的前50进行重新算分
21 GET my_index_books-demo/_search
22 {
23 "query": {
24 "match": {
25 "content": "实战"
26 }
27 },
28 "rescore": {
29 "query": {
30 "rescore_query": {
31 "match": {
32 "title": "MySQL"
33 }
34 },
35 "query_weight": 0.7,
36 "rescore_query_weight": 1.2
37 },
38 "window_size": 50
39 }

40 }
通过rescore_query我们可以对检索结果进行二次评分,增加自己更复杂的评分逻辑,提供更准确的结
果排序,但是相应的也会增加查询的计算成本与响应时间。
多字段搜索场景优化
多字段搜索的三种场景:
最佳字段(Best Fields) : 多个字段中返回评分最高的
当字段之间相互竞争,又相互关联。例如,对于博客的 title和 body这样的字段,评分来自最匹配字段
多数字段(Most Fields):匹配多个字段,返回各个字段评分之和
处理英文内容时的一种常见的手段是,在主字段( English Analyzer),抽取词干,加入同义词,以匹配
更多的文档。相同的文本,加入子字段(Standard Analyzer),以提供更加精确的匹配。其他字段作
为匹配文档提高相关度的信号,匹配字段越多则越好。
混合字段(Cross Fields): 跨字段匹配,待查询内容在多个字段中都显示
对于某些实体,例如人名,地址,图书信息。需要在多个字段中确定信息,单个字段只能作为整体的
一部分。希望在任何这些列出的字段中找到尽可能多的词。
最佳字段搜索
将任何与任一查询匹配的文档作为结果返回,采用字段上最匹配的评分作为最终评分返回。
官方文档:https://www.elastic.co/guide/en/elasticsearch/reference/8.14/query-dsl-dis-max-query.
html
案例

1
2 DELETE /blogs
3 PUT /blogs/_doc/1
4 {
5 "title": "Quick brown rabbits",
6 "body": "Brown rabbits are commonly seen."
7 }
8
9 PUT /blogs/_doc/2
10 {
11 "title": "Keeping pets healthy",
12 "body": "My quick brown fox eats rabbits on a regular basis."
13 }
14 # 搜索棕色的狐狸
15 POST /blogs/_search
16 {
17 "query": {
18 "bool": {
19 "should": [
20 { "match": { "title": "Brown fox" }},
21 { "match": { "body": "Brown fox" }}
22 ]
23 }
24 }
25 }
26
思考:查询结果不符合预期,为什么?
bool should的算法过程:
查询should语句中的两个查询
加和两个查询的评分
乘以匹配语句的总数
除以所有语句的总数
上述例子中,title和body属于竞争关系,不应该将分数简单叠加,而是应该找到单个最佳匹配的字段的
评分。
使用dis max query查询

1 POST /blogs/_search
2 {
3 "query": {
4 "dis_max": {
5 "queries": [
6 { "match": { "title": "Brown fox" }},
7 { "match": { "body": "Brown fox" }}
8 ]
9 }
10 }
11 }
可以通过tie_breaker参数调整
Tie Breaker是一个介于0-1之间的浮点数。0代表使用最佳匹配;1代表所有语句同等重要。
1. 获得最佳匹配语句的评分_score 。
2. 将其他匹配语句的评分与tie_breaker相乘
3. 对以上评分求和并规范化
最终得分=最佳匹配字段+其他匹配字段*tie_breaker

1 POST /blogs/_search
2 {
3 "query": {
4 "dis_max": {
5 "queries": [
6 { "match": { "title": "Quick pets" }},
7 { "match": { "body": "Quick pets" }}
8 ]
9 }
10 }
11 }
12
13
14 POST /blogs/_search
15 {
16 "query": {
17 "dis_max": {
18 "queries": [
19 { "match": { "title": "Quick pets" }},
20 { "match": { "body": "Quick pets" }}
21 ],
22 "tie_breaker": 0.1
23 }
24 }
25 }
使用 best_fields 查询
best_fields策略获取最佳匹配字段的得分, final_score = max(其他匹配字段得分, 最佳匹配字段得分)
采用 best_fields 查询,并添加参数 tie_breaker=0.1,final_score = 其他匹配字段得分 * 0.1 + 最佳匹
配字段得分
Best Fields是默认类型,可以不用指定,等价于dis_max查询方式

1 POST /blogs/_search
2 {
3 "query": {
4 "multi_match": {
5 "type": "best_fields",
6 "query": "Brown fox",
7 "fields": ["title","body"],
8 "tie_breaker": 0.2
9 }
10 }
11 }
案例

1 PUT /employee
2 {
3 "settings" : {
4 "index" : {
5 "analysis.analyzer.default.type": "ik_max_word"
6 }
7 }
8 }
9
10 POST /employee/_bulk
11 {"index":{"_id":1}}
12 {"empId":"1","name":"员工
001","age":20,"sex":"男","mobile":"19000001111","salary":23343,"deptName":"技术
部","address":"湖北省武汉市洪山区光谷大厦","content":"i like to write best elasticsearch
article"}
13 {"index":{"_id":2}}
14 {"empId":"2","name":"员工
002","age":25,"sex":"男","mobile":"19000002222","salary":15963,"deptName":"销售
部","address":"湖北省武汉市江汉路","content":"i think java is the best programming
language"}
15 {"index":{"_id":3}}
16 {"empId":"3","name":"员工
003","age":30,"sex":"男","mobile":"19000003333","salary":20000,"deptName":"技术
部","address":"湖北省武汉市经济开发区","content":"i am only an elasticsearch beginner"}
17 {"index":{"_id":4}}
18 {"empId":"4","name":"员工
004","age":20,"sex":"女","mobile":"19000004444","salary":15600,"deptName":"销售
部","address":"湖北省武汉市沌口开发区","content":"elasticsearch and hadoop are all very
good solution, i am a beginner"}
19 {"index":{"_id":5}}
20 {"empId":"5","name":"员工
005","age":20,"sex":"男","mobile":"19000005555","salary":19665,"deptName":"测试
部","address":"湖北省武汉市东湖隧道","content":"spark is best big data solution based on
scala, an programming language similar to java"}
21 {"index":{"_id":6}}
22 {"empId":"6","name":"员工
006","age":30,"sex":"女","mobile":"19000006666","salary":30000,"deptName":"技术
部","address":"湖北省武汉市江汉路","content":"i like java developer"}
23 {"index":{"_id":7}}
24 {"empId":"7","name":"员工
007","age":60,"sex":"女","mobile":"19000007777","salary":52130,"deptName":"测试
部","address":"湖北省黄冈市边城区","content":"i like elasticsearch developer"}
25 {"index":{"_id":8}}

26 {"empId":"8","name":"员工
008","age":19,"sex":"女","mobile":"19000008888","salary":60000,"deptName":"技术
部","address":"湖北省武汉市江汉大学","content":"i like spark language"}
27 {"index":{"_id":9}}
28 {"empId":"9","name":"员工
009","age":40,"sex":"男","mobile":"19000009999","salary":23000,"deptName":"销售
部","address":"河南省郑州市郑州大学","content":"i like java developer"}
29 {"index":{"_id":10}}
30 {"empId":"10","name":"张湖
北","age":35,"sex":"男","mobile":"19000001010","salary":18000,"deptName":"测试
部","address":"湖北省武汉市东湖高新","content":"i like java developer, i also like
elasticsearch"}
31 {"index":{"_id":11}}
32 {"empId":"11","name":"王河
南","age":61,"sex":"男","mobile":"19000001011","salary":10000,"deptName":"销售
部","address":"河南省开封市河南大学","content":"i am not like java"}
33 {"index":{"_id":12}}
34 {"empId":"12","name":"张大
学","age":26,"sex":"女","mobile":"19000001012","salary":11321,"deptName":"测试
部","address":"河南省开封市河南大学","content":"i am java developer, java is good"}
35 {"index":{"_id":13}}
36 {"empId":"13","name":"李江
汉","age":36,"sex":"男","mobile":"19000001013","salary":11215,"deptName":"销售
部","address":"河南省郑州市二七区","content":"i like java and java is very best, i like
it, do you like java"}
37 {"index":{"_id":14}}
38 {"empId":"14","name":"王技
术","age":45,"sex":"女","mobile":"19000001014","salary":16222,"deptName":"测试
部","address":"河南省郑州市金水区","content":"i like c++"}
39 {"index":{"_id":15}}
40 {"empId":"15","name":"张测
试","age":18,"sex":"男","mobile":"19000001015","salary":20000,"deptName":"技术
部","address":"河南省郑州市高新开发区","content":"i think spark is good"}
41
42
43 GET /employee/_search
44 {
45 "query": {
46 "multi_match": {
47 "query": "elasticsearch beginner 湖北省 开封市",
48 "type": "best_fields",
49 "fields": [
50 "content",
51 "address"
52 ]
53 }

54 },
55 "size": 15
56 }
57
58
59 # 查看执行计划
60 GET /employee/_explain/3
61 {
62
63 "query": {
64 "multi_match": {
65 "query": "elasticsearch beginner 湖北省 开封市",
66 "type": "best_fields",
67 "fields": [
68 "content",
69 "address"
70 ]
71 }
72 }
73 }
74
75 GET /employee/_explain/3
76 {
77
78 "query": {
79 "multi_match": {
80 "query": "elasticsearch beginner 湖北省 开封市",
81 "type": "best_fields",
82 "fields": [
83 "content",
84 "address"
85 ],
86 "tie_breaker": 0.1
87 }
88 }
89 }
90

使用多数字段搜索
most_fields策略获取全部匹配字段的累计得分(综合全部匹配字段的得分),等价于bool should查询
方式
1 GET /employee/_explain/3
2 {
3
4 "query": {
5 "multi_match": {
6 "query": "elasticsearch beginner 湖北省 开封市",
7 "type": "most_fields",
8 "fields": [
9 "content",
10 "address"
11 ]
12 }
13 }
14 }
案例

1 DELETE /titles
2 PUT /titles
3 {
4 "mappings": {
5 "properties": {
6 "title": {
7 "type": "text",
8 "analyzer": "english",
9 "fields": {
10 "std": {
11 "type": "text",
12 "analyzer": "standard"
13 }
14 }
15 }
16 }
17 }
18 }
19
20 POST titles/_bulk
21 { "index": { "_id": 1 }}
22 { "title": "My dog barks" }
23 { "index": { "_id": 2 }}
24 { "title": "I see a lot of barking dogs on the road " }
25
26 # 结果与预期不匹配
27 GET /titles/_search
28 {
29 "query": {
30 "match": {
31 "title": "barking dogs"
32 }
33 }
34 }
用广度匹配字段title包括尽可能多的文档——以提升召回率——同时又使用字段title.std 作为信号将相
关度更高的文档置于结果顶部。

1 GET /titles/_search
2 {
3 "query": {
4 "multi_match": {
5 "query": "barking dogs",
6 "type": "most_fields",
7 "fields": [
8 "title",
9 "title.std"
10 ]
11 }
12 }
13 }
每个字段对于最终评分的贡献可以通过自定义值boost 来控制。比如,使title 字段更为重要,这样同时也
降低了其他信号字段的作用:
1 #增加title的权重
2 GET /titles/_search
3 {
4 "query": {
5 "multi_match": {
6 "query": "barking dogs",
7 "type": "most_fields",
8 "fields": [
9 "title^10",
10 "title.std"
11 ]
12 }
13 }
14 }
跨字段搜索
搜索内容在多个字段中都显示,类似bool+dis_max组合

1 DELETE /address
2 PUT /address
3 {
4 "settings" : {
5 "index" : {
6 "analysis.analyzer.default.type": "ik_max_word"
7 }
8 }
9 }
10
11 PUT /address/_bulk
12 { "index": { "_id": "1"} }
13 {"province": "湖南","city": "长沙"}
14 { "index": { "_id": "2"} }
15 {"province": "湖南","city": "常德"}
16 { "index": { "_id": "3"} }
17 {"province": "广东","city": "广州"}
18 { "index": { "_id": "4"} }
19 {"province": "湖南","city": "邵阳"}
20
21 #使用most_fields的方式结果不符合预期,不支持operator
22 GET /address/_search
23 {
24 "query": {
25 "multi_match": {
26 "query": "湖南常德",
27 "type": "most_fields",
28 "fields": ["province","city"]
29 }
30 }
31 }
32
33 # 可以使用cross_fields,支持operator
34 #与copy_to相比,其中一个优势就是它可以在搜索时为单个字段提升权重。
35 GET /address/_search
36 {
37 "query": {
38 "multi_match": {
39 "query": "湖南常德",

40 "type": "cross_fields",
41 "operator": "and",
42 "fields": ["province","city"]
43 }
44 }
45 }
还可以用copy...to 解决,但是需要额外的存储空间

1 DELETE /address
2 # copy_to参数允许将多个字段的值复制到组字段中,然后可以将其作为单个字段进行查询
3 PUT /address
4 {
5 "mappings" : {
6 "properties" : {
7 "province" : {
8 "type" : "keyword",
9 "copy_to": "full_address"
10 },
11 "city" : {
12 "type" : "text",
13 "copy_to": "full_address"
14 }
15 }
16 },
17 "settings" : {
18 "index" : {
19 "analysis.analyzer.default.type": "ik_max_word"
20 }
21 }
22 }
23
24 PUT /address/_bulk
25 { "index": { "_id": "1"} }
26 {"province": "湖南","city": "长沙"}
27 { "index": { "_id": "2"} }
28 {"province": "湖南","city": "常德"}
29 { "index": { "_id": "3"} }
30 {"province": "广东","city": "广州"}
31 { "index": { "_id": "4"} }
32 {"province": "湖南","city": "邵阳"}
33
34 GET /address/_search
35 {
36 "query": {
37 "match": {
38 "full_address": {
39 "query": "湖南常德",

40 "operator": "and"
41 }
42 }
43 }
44 }
45
