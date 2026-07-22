---
title: "2 电商项目仿京东商品搜索服务实战"
description: "主讲老师: Fox 有道笔记地址:https://note.youdao.com/s/Tj3txf8r 1. 业务场景——图灵商城商品搜索 根据关键字查询、根据品牌、商品类别、商品属性信息、价格区间、是否有库存筛选查询,根据销 量、价格、上架时间等排序 2. 商品文档建模 商品json文档  1 { 2 "id": "26", 3 "name": "小米 11 手机", 4 "keyword..."
author: hsc
date: 2026-10-15 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', 'Redis', 'Kafka', 'RocketMQ', 'Netty', 'ElasticSearch', 'ShardingSphere', '实战']
toc: true
---

> 本文整理自《四、分布式专题》课程笔记，共 39 页。

主讲老师: Fox
有道笔记地址:https://note.youdao.com/s/Tj3txf8r
1. 业务场景——图灵商城商品搜索
根据关键字查询、根据品牌、商品类别、商品属性信息、价格区间、是否有库存筛选查询,根据销
量、价格、上架时间等排序
2. 商品文档建模
商品json文档

1 {
2 "id": "26",
3 "name": "小米 11 手机",
4 "keywords": "小米手机",
5 "subTitle": "AI智慧全面屏 6GB +64GB 亮黑色 全网通版 移动联通电信4G手机 双卡双待 双卡双待",
6 "price": "3999",
7 "promotionPrice": "2999",
8 "originalPrice": "5999",
9 "pic": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20180615/xiaomi.jpg",
10 "sale": 999,
11 "hasStock": true,
12 "salecount":999,
13 "putawayDate":"2021-04-01",
14 "brandId": 6,
15 "brandName": "小米",
16 "brandImg": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20190129/1e34aef2a409119018a4c6258e39ecfb_222_222.png
",
17 "categoryId": 19,
18 "categoryName": "手机通讯",
19 "attrs": [
20 {
21 "attrId": 1,
22 "attrName": "cpu",
23 "attrValue": "2核"
24 },
25 {
26 "attrId": 2,
27 "attrName": "颜色",
28 "attrValue": "黑色"
29 }
30 ]
31 }
32
33 {
34 "id": "30",
35 "name": "HLA海澜之家简约动物印花短袖T恤",
36 "keywords": "海澜之家衣服",
37 "subTitle": "HLA海澜之家短袖T恤",

38 "price": "199",
39 "promotionPrice": "99",
40 "originalPrice": "299",
41 "pic": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20180615/5ad83a4fN6ff67ecd.jpg!cc_350x449.jpg",
42 "sale": 999,
43 "hasStock": true,
44 "salecount":19,
45 "putawayDate":"2021-04-05",
46 "brandId": 50,
47 "brandName": "海澜之家",
48 "brandImg": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20190129/99d3279f1029d32b929343b09d3c72de_222_222.jpg
",
49 "categoryId": 8,
50 "categoryName": "T恤",
51 "attrs": [
52 {
53 "attrId": 3,
54 "attrName": "尺寸",
55 "attrValue": "M"
56 },
57 {
58 "attrId": 4,
59 "attrName": "颜色",
60 "attrValue": "黑色"
61 }
62 ]
63 }
建模分析:
name,keywords,subTitle 需要使用中文分词器
categoryName,brandName 类型可以为keyword
不同的商品其属性也不同,属性和商品之间存在关联关系。商品属性attrs不会频繁更新,可以选择使用nested类
型
思考:如何处理商品和商品属性之间的关联关系?
定义mapping,创建索引

1 PUT product_db
2 {
3 "mappings": {
4 "properties": {
5 "id": {
6 "type": "long"
7 },
8 "name": {
9 "type": "text",
10 "analyzer": "ik_max_word"
11 },
12 "keywords": {
13 "type": "text",
14 "analyzer": "ik_max_word"
15 },
16 "subTitle": {
17 "type": "text",
18 "analyzer": "ik_max_word"
19 },
20 "salecount":{
21 "type": "long"
22 },
23 "putawayDate":{
24 "type": "date"
25 },
26 "price": {
27 "type": "double"
28 },
29
30 "promotionPrice": {
31 "type": "keyword"
32 },
33 "originalPrice": {
34 "type": "keyword"
35 },
36 "pic": {
37 "type": "keyword"
38 },
39 "sale": {

40 "type": "long"
41 },
42 "hasStock": {
43 "type": "boolean"
44 },
45 "brandId": {
46 "type": "long"
47 },
48 "brandName": {
49 "type": "keyword"
50 },
51 "brandImg": {
52 "type": "keyword"
53 },
54 "categoryId": {
55 "type": "long"
56 },
57 "categoryName": {
58 "type": "keyword"
59 },
60 "attrs": {
61 "type": "nested",
62 "properties": {
63 "attrId": {
64 "type": "long"
65 },
66 "attrName": {
67 "type": "keyword"
68 },
69 "attrValue": {
70 "type": "keyword"
71 }
72 }
73 }
74 }
75 }
76 }
77

测试数据

1 PUT /product_db/_doc/1
2 {
3 "id": "26",
4 "name": "小米 11 手机",
5 "keywords": "小米手机",
6 "subTitle": "AI智慧全面屏 6GB +64GB 亮黑色 全网通版 移动联通电信4G手机 双卡双待 双卡双待",
7 "price": "3999",
8 "promotionPrice": "2999",
9 "originalPrice": "5999",
10 "pic": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20180615/xiaomi.jpg",
11 "sale": 999,
12 "hasStock": true,
13 "salecount":999,
14 "putawayDate":"2021-04-01",
15 "brandId": 6,
16 "brandName": "小米",
17 "brandImg": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20190129/1e34aef2a409119018a4c6258e39ecfb_222_222.png
",
18 "categoryId": 19,
19 "categoryName": "手机通讯",
20 "attrs": [
21 {
22 "attrId": 1,
23 "attrName": "cpu",
24 "attrValue": "2核"
25 },
26 {
27 "attrId": 2,
28 "attrName": "颜色",
29 "attrValue": "黑色"
30 }
31 ]
32 }
33
34 PUT /product_db/_doc/2
35 {
36 "id": "27",
37 "name": "小米 10 手机",

38 "keywords": "小米手机",
39 "subTitle": "AI智慧全面屏 4GB +64GB 亮白色 全网通版 移动联通电信4G手机 双卡双待 双卡双待",
40 "price": "2999",
41 "promotionPrice": "1999",
42 "originalPrice": "3999",
43 "pic": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20180615/xiaomi.jpg",
44 "sale": 999,
45 "hasStock": false,
46 "salecount":99,
47 "putawayDate":"2021-04-02",
48 "brandId": 6,
49 "brandName": "小米",
50 "brandImg": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20190129/1e34aef2a409119018a4c6258e39ecfb_222_222.png
",
51 "categoryId": 19,
52 "categoryName": "手机通讯",
53 "attrs": [
54 {
55 "attrId": 1,
56 "attrName": "cpu",
57 "attrValue": "4核"
58 },
59 {
60 "attrId": 2,
61 "attrName": "颜色",
62 "attrValue": "白色"
63 }
64 ]
65 }
66 PUT /product_db/_doc/3
67 {
68 "id": "28",
69 "name": "小米 手机",
70 "keywords": "小米手机",
71 "subTitle": "AI智慧全面屏 4GB +64GB 亮蓝色 全网通版 移动联通电信4G手机 双卡双待 双卡双待",
72 "price": "2999",
73 "promotionPrice": "1999",
74 "originalPrice": "3999",
75 "pic": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20180615/xiaomi.jpg",

76 "sale": 999,
77 "hasStock": true,
78 "salecount":199,
79 "putawayDate":"2021-04-03",
80 "brandId": 6,
81 "brandName": "小米",
82 "brandImg": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20190129/1e34aef2a409119018a4c6258e39ecfb_222_222.png
",
83 "categoryId": 19,
84 "categoryName": "手机通讯",
85 "attrs": [
86 {
87 "attrId": 1,
88 "attrName": "cpu",
89 "attrValue": "2核"
90 },
91 {
92 "attrId": 2,
93 "attrName": "颜色",
94 "attrValue": "蓝色"
95 }
96 ]
97 }
98 PUT /product_db/_doc/4
99 {
100 "id": "29",
101 "name": "Apple iPhone 8 Plus 64GB 金色特别版 移动联通电信4G手机",
102 "keywords": "苹果手机",
103 "subTitle": "苹果手机 Apple产品年中狂欢节,好物尽享,美在智慧!速来 >> 勾选[保障服务][原厂
保2年],获得AppleCare+全方位服务计划,原厂延保售后无忧。",
104 "price": "5999",
105 "promotionPrice": "4999",
106 "originalPrice": "7999",
107 "pic": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20180615/5acc5248N6a5f81cd.jpg",
108 "sale": 999,
109 "hasStock": true,
110 "salecount":1199,
111 "putawayDate":"2021-04-04",
112 "brandId": 51,
113 "brandName": "苹果",

114 "brandImg": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20180607/timg.jpg",
115 "categoryId": 19,
116 "categoryName": "手机通讯",
117 "attrs": [
118 {
119 "attrId": 1,
120 "attrName": "cpu",
121 "attrValue": "4核"
122 },
123 {
124 "attrId": 2,
125 "attrName": "颜色",
126 "attrValue": "金色"
127 }
128 ]
129 }
130 PUT /product_db/_doc/5
131 {
132 "id": "30",
133 "name": "HLA海澜之家简约动物印花短袖T恤",
134 "keywords": "海澜之家衣服",
135 "subTitle": "HLA海澜之家短袖T恤",
136 "price": "199",
137 "promotionPrice": "99",
138 "originalPrice": "299",
139 "pic": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20180615/5ad83a4fN6ff67ecd.jpg!cc_350x449.jpg",
140 "sale": 999,
141 "hasStock": true,
142 "salecount":19,
143 "putawayDate":"2021-04-05",
144 "brandId": 50,
145 "brandName": "海澜之家",
146 "brandImg": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20190129/99d3279f1029d32b929343b09d3c72de_222_222.jpg
",
147 "categoryId": 8,
148 "categoryName": "T恤",
149 "attrs": [
150 {
151 "attrId": 3,

152 "attrName": "尺寸",
153 "attrValue": "M"
154 },
155 {
156 "attrId": 4,
157 "attrName": "颜色",
158 "attrValue": "黑色"
159 }
160 ]
161 }
162 PUT /product_db/_doc/6
163 {
164 "id": "31",
165 "name": "HLA海澜之家蓝灰花纹圆领针织布短袖T恤",
166 "keywords": "海澜之家衣服",
167 "subTitle": "HLA海澜之家短袖T恤",
168 "price": "299",
169 "promotionPrice": "199",
170 "originalPrice": "299",
171 "pic": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20180615/5ac98b64N70acd82f.jpg!cc_350x449.jpg",
172 "sale": 999,
173 "hasStock": true,
174 "salecount":399,
175 "putawayDate":"2021-04-06",
176 "brandId": 50,
177 "brandName": "海澜之家",
178 "brandImg": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20190129/99d3279f1029d32b929343b09d3c72de_222_222.jpg
",
179 "categoryId": 8,
180 "categoryName": "T恤",
181 "attrs": [
182 {
183 "attrId": 3,
184 "attrName": "尺寸",
185 "attrValue": "X"
186 },
187 {
188 "attrId": 4,
189 "attrName": "颜色",

190 "attrValue": "蓝灰"
191 }
192 ]
193 }
194 PUT /product_db/_doc/7
195 {
196 "id": "32",
197 "name": "HLA海澜之家短袖T恤男基础款",
198 "keywords": "海澜之家衣服",
199 "subTitle": "HLA海澜之家短袖T恤",
200 "price": "269",
201 "promotionPrice": "169",
202 "originalPrice": "399",
203 "pic": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20180615/5a51eb88Na4797877.jpg",
204 "sale": 999,
205 "hasStock": true,
206 "salecount":399,
207 "putawayDate":"2021-04-07",
208 "brandId": 50,
209 "brandName": "海澜之家",
210 "brandImg": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20190129/99d3279f1029d32b929343b09d3c72de_222_222.jpg
",
211 "categoryId": 8,
212 "categoryName": "T恤",
213 "attrs": [
214 {
215 "attrId": 3,
216 "attrName": "尺寸",
217 "attrValue": "L"
218 },
219 {
220 "attrId": 4,
221 "attrName": "颜色",
222 "attrValue": "蓝色"
223 }
224 ]
225 }
226 PUT /product_db/_doc/8
227 {

228 "id": "33",
229 "name": "小米(MI)小米电视4A ",
230 "keywords": "小米电视机家用电器",
231 "subTitle": "小米(MI)小米电视4A 55英寸 L55M5-AZ/L55M5-AD 2GB+8GB HDR 4K超高清 人工智能
网络液晶平板电视",
232 "price": "2269",
233 "promotionPrice": "2169",
234 "originalPrice": "2399",
235 "pic": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20180615/5b02804dN66004d73.jpg",
236 "sale": 999,
237 "hasStock": true,
238 "salecount":132,
239 "putawayDate":"2021-04-09",
240 "brandId": 6,
241 "brandName": "小米",
242 "brandImg": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20190129/1e34aef2a409119018a4c6258e39ecfb_222_222.png
",
243 "categoryId": 35,
244 "categoryName": "手机数码",
245 "attrs": [
246 {
247 "attrId": 5,
248 "attrName": "屏幕尺寸",
249 "attrValue": "52"
250 },
251 {
252 "attrId": 6,
253 "attrName": "机身颜色",
254 "attrValue": "黑色"
255 }
256 ]
257 }
258 PUT /product_db/_doc/9
259 {
260 "id": "34",
261 "name": "小米(MI)小米电视4A 65英寸",
262 "keywords": "小米电视机家用电器",
263 "subTitle": "小米(MI)小米电视4A 65英寸 L55M5-AZ/L55M5-AD 2GB+8GB HDR 4K超高清 人工智能
网络液晶平板电视",
264 "price": "3269",

265 "promotionPrice": "3169",
266 "originalPrice": "3399",
267 "pic": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20180615/5b028530N51eee7d4.jpg",
268 "sale": 999,
269 "hasStock": true,
270 "salecount":999,
271 "putawayDate":"2021-04-10",
272 "brandId": 6,
273 "brandName": "小米",
274 "brandImg": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20190129/1e34aef2a409119018a4c6258e39ecfb_222_222.png
",
275 "categoryId": 35,
276 "categoryName": "手机数码",
277 "attrs": [
278 {
279 "attrId": 5,
280 "attrName": "屏幕尺寸",
281 "attrValue": "65"
282 },
283 {
284 "attrId": 6,
285 "attrName": "机身颜色",
286 "attrValue": "金色"
287 }
288 ]
289 }
290 PUT /product_db/_doc/10
291 {
292 "id": "35",
293 "name": "耐克NIKE 男子 休闲鞋 ROSHE RUN 运动鞋 511881-010黑色41码",
294 "keywords": "耐克运动鞋 鞋子",
295 "subTitle": "耐克NIKE 男子 休闲鞋 ROSHE RUN 运动鞋 511881-010黑色41码",
296 "price": "569",
297 "promotionPrice": "369",
298 "originalPrice": "899",
299 "pic": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20180615/5b235bb9Nf606460b.jpg",
300 "sale": 999,
301 "hasStock": true,
302 "salecount":399,

303 "putawayDate":"2021-04-11",
304 "brandId": 58,
305 "brandName": "NIKE",
306 "brandImg": "http://macro-oss.oss-cn-shenzhen.aliyuncs.com/mall/images/20180615/timg
(51).jpg",
307 "categoryId": 29,
308 "categoryName": "男鞋",
309 "attrs": [
310 {
311 "attrId": 7,
312 "attrName": "尺码",
313 "attrValue": "42"
314 },
315 {
316 "attrId": 8,
317 "attrName": "颜色",
318 "attrValue": "黑色"
319 }
320 ]
321 }
322 PUT /product_db/_doc/11
323 {
324 "id": "36",
325 "name": "耐克NIKE 男子 气垫 休闲鞋 AIR MAX 90 ESSENTIAL 运动鞋 AJ1285-101白色41码",
326 "keywords": "耐克运动鞋 鞋子",
327 "subTitle": "AIR MAX 90 ESSENTIAL 运动鞋 AJ1285-101白色",
328 "price": "769",
329 "promotionPrice": "469",
330 "originalPrice": "999",
331 "pic": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20180615/5b19403eN9f0b3cb8.jpg",
332 "sale": 999,
333 "hasStock": true,
334 "salecount":499,
335 "putawayDate":"2021-04-13",
336 "brandId": 58,
337 "brandName": "NIKE",
338 "brandImg": "http://macro-oss.oss-cn-shenzhen.aliyuncs.com/mall/images/20180615/timg
(51).jpg",
339 "categoryId": 29,
340 "categoryName": "男鞋",

341 "attrs": [
342 {
343 "attrId": 7,
344 "attrName": "尺码",
345 "attrValue": "44"
346 },
347 {
348 "attrId": 8,
349 "attrName": "颜色",
350 "attrValue": "白色"
351 }
352 ]
353 }
354 PUT /product_db/_doc/12
355 {
356 "id": "37",
357 "name": "(华为)HUAWEI MateBook X Pro 2019款 13.9英寸3K触控全面屏 轻薄笔记本",
358 "keywords": "轻薄笔记本华为 笔记本电脑",
359 "subTitle": "轻薄华为笔记本 电脑",
360 "price": "4769",
361 "promotionPrice": "4469",
362 "originalPrice": "4999",
363 "pic": "http://tuling-mall.oss-cn-
shenzhen.aliyuncs.com/tulingmall/images/20200317/800_800_1555752016264mp.png",
364 "sale": 999,
365 "hasStock": true,
366 "salecount":699,
367 "putawayDate":"2021-04-14",
368 "brandId": 3,
369 "brandName": "华为",
370 "brandImg": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20190129/17f2dd9756d9d333bee8e60ce8c03e4c_222_222.jpg
",
371 "categoryId": 19,
372 "categoryName": "手机通讯",
373 "attrs": [
374 {
375 "attrId": 9,
376 "attrName": "容量",
377 "attrValue": "16G"
378 },

379 {
380 "attrId": 10,
381 "attrName": "网络",
382 "attrValue": "4G"
383 }
384 ]
385 }
386 PUT /product_db/_doc/13
387 {
388 "id": "38",
389 "name": "华为nova6se 手机 绮境森林 全网通(8G+128G)",
390 "keywords": "轻薄笔记本华为 手机",
391 "subTitle": "华为nova6se 手机",
392 "price": "6769",
393 "promotionPrice": "6469",
394 "originalPrice": "6999",
395 "pic": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20180607/5ac1bf58Ndefaac16.jpg",
396 "sale": 999,
397 "hasStock": true,
398 "salecount":899,
399 "putawayDate":"2021-04-15",
400 "brandId": 3,
401 "brandName": "华为",
402 "brandImg": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20190129/17f2dd9756d9d333bee8e60ce8c03e4c_222_222.jpg
",
403 "categoryId": 19,
404 "categoryName": "手机通讯",
405 "attrs": [
406 {
407 "attrId": 9,
408 "attrName": "容量",
409 "attrValue": "64G"
410 },
411 {
412 "attrId": 10,
413 "attrName": "网络",
414 "attrValue": "5G"
415 }
416 ]

417 }
418 PUT /product_db/_doc/14
419 {
420 "id": "39",
421 "name": "iPhone7/6s/8钢化膜苹果8Plus全屏复盖抗蓝光防窥防偷看手机膜",
422 "keywords": "手机膜",
423 "subTitle": "iPhone7/6s/8钢化膜苹果8Plus全屏复盖抗蓝光防窥防偷看手机膜",
424 "price": "29",
425 "promotionPrice": "39",
426 "originalPrice": "49",
427 "pic": "http://tuling-mall.oss-cn-
shenzhen.aliyuncs.com/tulingmall/images/20200311/6df99dab78bb2014.jpg",
428 "sale": 999,
429 "hasStock": true,
430 "salecount":799,
431 "putawayDate":"2021-04-16",
432 "brandId": 51,
433 "brandName": "苹果",
434 "brandImg": "http://tuling-mall.oss-cn-
shenzhen.aliyuncs.com/tulingmall/images/20200311/2b84746650fc122d67749a876c453619.png",
435 "categoryId": 30,
436 "categoryName": "手机配件",
437 "attrs": [
438 {
439 "attrId": 11,
440 "attrName": "手机膜-材料",
441 "attrValue": "钢化"
442 },
443 {
444 "attrId": 12,
445 "attrName": "手机膜-颜色",
446 "attrValue": "白色"
447 }
448 ]
449 }
450
451 PUT /product_db/_doc/15
452 {
453 "id": "40",
454 "name": "七匹狼短袖T恤男纯棉舒适春夏修身运动休闲短袖三条装 圆领3条装",
455 "keywords": "七匹狼服装 衣服",

456 "subTitle": "七匹狼短袖T恤男纯棉舒适春夏修身运动休闲短袖三条装 圆领3条装",
457 "price": "129",
458 "promotionPrice": "139",
459 "originalPrice": "149",
460 "pic": "http://tuling-mall.oss-cn-
shenzhen.aliyuncs.com/tulingmall/images/20200311/19e846e727dff337.jpg",
461 "sale": 999,
462 "hasStock": true,
463 "salecount":199,
464 "putawayDate":"2021-04-20",
465 "brandId": 49,
466 "brandName": "七匹狼",
467 "brandImg": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20190129/18d8bc3eb13533fab466d702a0d3fd1f40345bcd.jpg
",
468 "categoryId": 8,
469 "categoryName": "T恤",
470 "attrs": [
471 {
472 "attrId": 3,
473 "attrName": "尺寸",
474 "attrValue": "M"
475 },
476 {
477 "attrId": 4,
478 "attrName": "颜色",
479 "attrValue": "白色"
480 }
481 ]
482 }
483 PUT /product_db/_doc/16
484 {
485 "id": "41",
486 "name": "华为P40 Pro手机",
487 "keywords": "华为手机",
488 "subTitle": "华为P40 Pro手机",
489 "price": "2129",
490 "promotionPrice": "2139",
491 "originalPrice": "2149",
492 "pic": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20180607/5ac1bf58Ndefaac16.jpg",
493 "sale": 999,

494 "hasStock": true,
495 "salecount":199,
496 "putawayDate":"2021-05-03",
497 "brandId": 3,
498 "brandName": "华为",
499 "brandImg": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20190129/17f2dd9756d9d333bee8e60ce8c03e4c_222_222.jpg
",
500 "categoryId": 19,
501 "categoryName": "手机通讯",
502 "attrs": [
503 {
504 "attrId": 9,
505 "attrName": "容量",
506 "attrValue": "128G"
507 },
508 {
509 "attrId": 10,
510 "attrName": "网络",
511 "attrValue": "5G"
512 }
513 ]
514 }
515 PUT /product_db/_doc/17
516 {
517 "id": "42",
518 "name": "朵唯智能手机 4G全网通 老人学生双卡双待手机",
519 "keywords": "朵唯手机",
520 "subTitle": "朵唯手机后置双摄,国产虎贲芯片!优化散热结构!浅薄机身!朵唯4月特惠!",
521 "price": "3129",
522 "promotionPrice": "3139",
523 "originalPrice": "3249",
524 "pic": "http://macro-oss.oss-cn-
shenzhen.aliyuncs.com/mall/images/20180615/xiaomi.jpg",
525 "sale": 999,
526 "hasStock": true,
527 "salecount":1199,
528 "putawayDate":"2021-06-01",
529 "brandId": 59,
530 "brandName": "朵唯",
531 "brandImg": "http://tuling-mall.oss-cn-
shenzhen.aliyuncs.com/tulingmall/images/20200311/2b84746650fc122d67749a876c453619.png",

532 "categoryId": 19,
533 "categoryName": "手机通讯",
534 "attrs": [
535 {
536 "attrId": 9,
537 "attrName": "容量",
538 "attrValue": "32G"
539 },
540 {
541 "attrId": 10,
542 "attrName": "网络",
543 "attrValue": "4G"
544 }
545 ]
546 }
547
3. 构建DSL语句实现商品搜索

1 POST /product_db/_doc/_search
2 {
3 "from": 0,
4 "size": 8,
5 "query": {
6 "bool": {
7 "must": [
8 {
9 "match": {
10 "name": {
11 "query": "手机"
12 }
13 }
14 }
15 ],
16 "filter": [
17 {
18 "term": {
19 "hasStock": {
20 "value": true
21 }
22 }
23 },
24 {
25 "range": {
26 "price": {
27 "from": "1",
28 "to": "5000"
29 }
30 }
31 }
32 ]
33 }
34 },"sort": [
35 {
36 "salecount": {
37 "order": "asc"
38 }
39 }

40 ],
41 "aggregations": {
42 "brand_agg": {
43 "terms": {
44 "field": "brandId",
45 "size": 50
46 },
47 "aggregations": {
48 "brand_name_agg": {
49 "terms": {
50 "field": "brandName"
51 }
52 },
53 "brand_img_agg": {
54 "terms": {
55 "field": "brandImg"
56 }
57 }
58 }
59 },
60 "category_agg": {
61 "terms": {
62 "field": "categoryId",
63 "size": 50,
64 "min_doc_count": 1
65 },
66 "aggregations": {
67 "category_name_agg": {
68 "terms": {
69 "field": "categoryName"
70 }
71 }
72 }
73 },
74 "attr_agg": {
75 "nested": {
76 "path": "attrs"
77 },
78 "aggregations": {
79 "attr_id_agg": {

80 "terms": {
81 "field": "attrs.attrId"
82 },
83 "aggregations": {
84 "attr_name_agg": {
85 "terms": {
86 "field": "attrs.attrName"
87 }
88 },
89 "attr_value_agg": {
90 "terms": {
91 "field": "attrs.attrValue"
92 }
93 }
94 }
95 }
96 }
97 }
98 },
99 "highlight": {
100 "pre_tags": [
101 "<b style='color:red'>"
102 ],
103 "post_tags": [
104 "</b>"
105 ],
106 "fields": {
107 "name": {}
108 }
109 }
110 }
111
112

1 GET product_db/_search
2 {
3 "from": 0,
4 "size": 20,
5 "query": {
6 "bool": {
7 "must": [
8 {
9 "multi_match": {
10 "query": "手机",
11 "fields": [
12 "name",
13 "keywords",
14 "subTitle"
15 ]
16 }
17 }
18 ],
19 "filter": [
20 {
21 "term": {
22 "hasStock": "true"
23 }
24 },
25 {
26 "range": {
27 "price": {
28 "gte": 2000,
29 "lte": 5000
30 }
31 }
32 }
33 ]
34 }
35 },
36 "aggs": {
37 "brandId_aggs": {
38 "terms": {
39 "field": "brandId",

40 "size": 10
41 },
42 "aggs": {
43 "brandName_aggs": {
44 "terms": {
45 "field": "brandName"
46 }
47 },
48 "brandImg_aggs": {
49 "terms": {
50 "field": "brandImg"
51 }
52 }
53 }
54 },
55 "categoryId_aggs": {
56 "terms": {
57 "field": "categoryId",
58 "size": 10
59 },
60 "aggs": {
61 "categoryName_aggs": {
62 "terms": {
63 "field": "categoryName"
64 }
65 }
66 }
67 },
68 "attrs_aggs": {
69 "nested": {
70 "path": "attrs"
71 },
72 "aggs": {
73 "attrId_aggs": {
74 "terms": {
75 "field": "attrs.attrId"
76 },
77 "aggs": {
78 "attrName_aggs": {
79 "terms": {

80 "field": "attrs.attrName"
81 }
82 },
83 "attrValue_aggs": {
84 "terms": {
85 "field": "attrs.attrValue"
86 }
87 }
88 }
89 }
90 }
91 }
92 },
93 "sort": [
94 {
95 "salecount": {
96 "order": "desc"
97 }
98 }
99 ],
100 "highlight": {
101 "fields": {
102 "*": {}
103 }
104 }
105 }
4. 微服务实现商品搜索功能
1)引入依赖
1 <dependency>
2 <groupId>org.springframework.boot</groupId>
3 <artifactId>spring-boot-starter-data-elasticsearch</artifactId>
4 </dependency>

2)核心代码

1
2 import co.elastic.clients.elasticsearch.ElasticsearchClient;
3 import co.elastic.clients.elasticsearch._types.FieldSort;
4 import co.elastic.clients.elasticsearch._types.FieldValue;
5 import co.elastic.clients.elasticsearch._types.SortOptionsBuilders;
6 import co.elastic.clients.elasticsearch._types.SortOrder;
7 import co.elastic.clients.elasticsearch._types.aggregations.*;
8
9 import co.elastic.clients.elasticsearch._types.query_dsl.*;
10 import co.elastic.clients.elasticsearch.core.SearchRequest;
11 import co.elastic.clients.elasticsearch.core.SearchResponse;
12
13 import co.elastic.clients.elasticsearch.core.search.*;
14 import co.elastic.clients.json.JsonData;
15 import org.springframework.beans.factory.annotation.Autowired;
16 import org.springframework.beans.factory.annotation.Qualifier;
17
18 import org.springframework.stereotype.Service;
19 import org.springframework.util.StringUtils;
20 import org.tuling.tlmall_search.common.SearchConstant;
21 import org.tuling.tlmall_search.domain.EsProduct;
22 import org.tuling.tlmall_search.service.TulingMallSearchService;
23 import org.tuling.tlmall_search.vo.ESRequestParam;
24 import org.tuling.tlmall_search.vo.ESResponseResult;
25
26 import java.util.*;
27 import java.util.stream.Collectors;
28
29
30 @Service(value = "tulingMallSearchService")
31 public class TulingMallSearchServiceImpl implements TulingMallSearchService {
32
33
34 @Qualifier("elasticsearchClient")
35 @Autowired
36 ElasticsearchClient client;
37
38
39 /**************************图灵商城搜索*****************************/

40 @Override
41 public ESResponseResult search(ESRequestParam param) {
42
43 try {
44 //1、构建检索对象-封装请求相关参数信息
45 SearchRequest searchRequest = startBuildRequestParam(param);
46
47 //2、进行检索操作
48 SearchResponse response = client.search(searchRequest, EsProduct.class);
49 System.out.println("response:" + response);
50 //3、分析响应数据,封装成指定的格式
51 ESResponseResult responseResult = startBuildResponseResult(response,
param);
52 return responseResult;
53 } catch (Exception e) {
54 e.printStackTrace();
55 }
56
57 return null;
58
59 }
60
61 /**
62 * 封装请求参数信息
63 * 关键字查询、根据属性、分类、品牌、价格区间、是否有库存等进行过滤、分页、高亮、以及聚合统
计品牌分类属性
64 * price=1_5000&keyword=手机
&sort=salecount_asc&hasStock=1&pageNum=1&pageSize=20&categoryId=19&attrs=2_蓝色
&attrs=1_2核
65 */
66 private SearchRequest startBuildRequestParam(ESRequestParam param) {
67
68 //构建搜索请求
69 SearchRequest.Builder searchRequestBuilder = new SearchRequest.Builder();
70
71 /**
72 * 关键字查询、根据属性、分类、品牌、价格区间、是否有库存等进行过滤、分页、高亮、以及聚
合统计品牌分类属性
73 */
74
75 //构建bool查询
76 BoolQuery.Builder boolQueryBuilder = new BoolQuery.Builder();

77
78 //1、查询关键字
79 if (!StringUtils.isEmpty(param.getKeyword())) {
80 //单字段查询
81 // boolQueryBuilder.must(QueryBuilders.match(
82 // m->m.field("name").query(param.getKeyword())
83 // ));
84 //多字段查询
85 boolQueryBuilder.must(m->m.multiMatch(
86 q->q.fields("name", "keywords",
"subTitle").query(param.getKeyword())
87 ));
88 }
89 //2、根据类目ID进行过滤
90 if (null != param.getCategoryId()) {
91 boolQueryBuilder.filter(QueryBuilders.term(t ->
t.field("categoryId").value(param.getCategoryId())));
92
93 }
94
95 //3、根据品牌ID进行过滤
96 if (null != param.getBrandId() && param.getBrandId().size() > 0) {
97 List<FieldValue> brandIds = param.getBrandId().stream().map(b ->
FieldValue.of(b)).collect(Collectors.toList());
98 boolQueryBuilder.filter(QueryBuilders.terms(t ->
t.field("brandId").terms(v -> v.value(brandIds))));
99 }
100
101 //4、根据属性进行相关过滤
102 if (param.getAttrs() != null && param.getAttrs().size() > 0) {
103
104 param.getAttrs().forEach(item -> {
105 //attrs=1_白色&2_4核
106 BoolQuery.Builder boolQuery = QueryBuilders.bool();
107
108 //attrs=1_64G
109 String[] s = item.split("_");
110 String attrId = s[0];
111 String[] attrValues = s[1].split(":");//这个属性检索用的值
112
113 boolQuery.filter(QueryBuilders.term(t ->
t.field("attrs.attrId").value(attrId)));

114
115 List<FieldValue> attrValueList = Arrays.stream(attrValues).map(b ->
FieldValue.of(b)).collect(Collectors.toList());
116 boolQuery.filter(QueryBuilders.terms(t ->
t.field("attrs.attrValue").terms(v -> v.value(attrValueList))));
117
118 NestedQuery.Builder nestedQueryBuilder = new NestedQuery.Builder();
119 //nested查询
120 nestedQueryBuilder.path("attrs").query(q ->
q.bool(boolQuery.build())).scoreMode(ChildScoreMode.None);
121
122 boolQueryBuilder.filter(q -> q.nested(nestedQueryBuilder.build()));
123 });
124
125 }
126
127 //5、是否有库存
128 if (null != param.getHasStock()) {
129 boolQueryBuilder.filter(QueryBuilders.term(t ->
t.field("hasStock").value(param.getHasStock() == 1)));
130 }
131
132
133 //6、根据价格过滤
134 if (!StringUtils.isEmpty(param.getPrice())) {
135 //价格的输入形式为:10_100(起始价格和最终价格)或_100(不指定起始价格)或10_(不
限制最终价格)
136 RangeQuery.Builder rangeQueryBuilder =
QueryBuilders.range().field("price");
137
138 String[] price = param.getPrice().split("_");
139 if (price.length == 2) {
140 //price: _5000 [, 5000]
141 if (param.getPrice().startsWith("_")) {
142 rangeQueryBuilder.lte(JsonData.of(price[1]));
143 } else {
144 //price: 1_5000 [1, 5000]
145
rangeQueryBuilder.gte(JsonData.of(price[0])).lte(JsonData.of(price[1]));
146 }
147
148 } else if (price.length == 1) {
149 //price: 1_ [1]

150 if (param.getPrice().endsWith("_")) {
151 rangeQueryBuilder.gte(JsonData.of(price[0]));
152 }
153 }
154 boolQueryBuilder.filter(r -> r.range(rangeQueryBuilder.build()));
155 }
156
157 //封装所有查询条件
158 searchRequestBuilder.query(q -> q.bool(boolQueryBuilder.build()));
159
160
161 /**
162 * 实现排序、高亮、分页操作
163 */
164
165 //排序
166 //页面传入的参数值形式 sort=price_asc/desc
167 if (!StringUtils.isEmpty(param.getSort())) {
168 String sort = param.getSort();
169 String[] sortFileds = sort.split("_");
170
171 if (!StringUtils.isEmpty(sortFileds[0])) {
172
173 SortOrder sortOrder = "asc".equalsIgnoreCase(sortFileds[1]) ?
SortOrder.Asc : SortOrder.Desc;
174
175 //排序
176 FieldSort fieldSort =
SortOptionsBuilders.field().field(sortFileds[0]).order(sortOrder).build();
177 searchRequestBuilder.sort(s -> s.field(fieldSort));
178 }
179 }
180
181
182 //分页查询
183 searchRequestBuilder.from((param.getPageNum() - 1) * SearchConstant.PAGE_SIZE);
184 searchRequestBuilder.size(SearchConstant.PAGE_SIZE);
185
186 //高亮显示
187 if (!StringUtils.isEmpty(param.getKeyword())) {
188

189 HighlightField highlightField = new HighlightField.Builder().preTags("<b
style='color:red'>").postTags("</b>").build();
190 searchRequestBuilder.highlight(h -> h.fields("name", highlightField));
191 }
192
193
194 /**
195 * 对品牌、分类信息、属性信息进行聚合分析
196 */
197 //1. 按照品牌进行聚合
198 //1.1 品牌的子聚合-品牌名聚合
199 Aggregation brand_name_agg = AggregationBuilders.terms(t ->
t.field("brandName").size(1));
200 //1.2 品牌的子聚合-品牌图片聚合
201 Aggregation brand_img_agg = AggregationBuilders.terms(t ->
t.field("brandImg").size(1));
202
203 Aggregation brand_agg = new Aggregation.Builder()
204 //按照品牌id进行聚合
205 .terms(t -> t.field("brandId").size(50)).aggregations("brand_name_agg",
brand_name_agg).aggregations("brand_img_agg", brand_img_agg).build();
206 searchRequestBuilder.aggregations("brand_agg", brand_agg);
207
208 //2. 按照分类信息进行聚合
209 Aggregation category_agg = new Aggregation.Builder().terms(t ->
t.field("categoryId").size(50)).aggregations("category_name_agg",
AggregationBuilders.terms(t -> t.field("categoryName").size(1))).build();
210 searchRequestBuilder.aggregations("category_agg", category_agg);
211
212
213 //2. 按照属性信息进行聚合
214 NestedAggregation attrs = new
NestedAggregation.Builder().path("attrs").build();
215
216 Aggregation attr_id_agg = new Aggregation.Builder()
217 //2.1 按照属性ID进行聚合
218 .terms(t -> t.field("attrs.attrId"))
219 //2.1.1 在每个属性ID下,按照属性名进行聚合
220 .aggregations("attr_name_agg", AggregationBuilders.terms(t ->
t.field("attrs.attrName").size(1)))
221 //2.1.1 在每个属性ID下,按照属性值进行聚合
222 .aggregations("attr_value_agg", AggregationBuilders.terms(t ->
t.field("attrs.attrValue").size(1))).build();

223
224 Aggregation attrs_agg = new
Aggregation.Builder().nested(attrs).aggregations("attr_id_agg", attr_id_agg).build();
225
226 searchRequestBuilder.aggregations("attrs_agg", attrs_agg);
227
228 System.out.println("构建的DSL语句:" + searchRequestBuilder.toString());
229
230
231 SearchRequest searchRequest =
searchRequestBuilder.index(SearchConstant.INDEX_NAME).build();
232
233 return searchRequest;
234 }
235
236
237 /**
238 * 封装查询到的结果信息
239 * 关键字查询、根据属性、分类、品牌、价格区间、是否有库存等进行过滤、分页、高亮、以及聚合统
计品牌分类属性
240 */
241 private ESResponseResult startBuildResponseResult(SearchResponse response,
ESRequestParam param) {
242 //构建返回结果
243 ESResponseResult result = new ESResponseResult();
244
245 //1、获取查询到的商品信息
246 HitsMetadata<EsProduct> hitsMetadata = response.hits();
247 List<Hit<EsProduct>> hits = hitsMetadata.hits();
248
249 List<EsProduct> esProducts = new ArrayList<>();
250 //2、遍历所有商品信息
251 if (!hits.isEmpty()) {
252 for (Hit<EsProduct> hit : hits) {
253 EsProduct product = hit.source();
254
255 //2.1 判断是否按关键字检索,若是就显示高亮,否则不显示
256 if (!StringUtils.isEmpty(param.getKeyword())) {
257 //2.2 拿到高亮信息显示标题
258 List<String> name = hit.highlight().get("name");
259 //2.3 判断name中是否含有查询的关键字(因为是多字段查询,因此可能不包含指定
的关键字,假设不包含则显示原始name字段的信息)

260 String nameValue = name != null ? name.get(0) : product.getName();
261 product.setName(nameValue);
262 }
263 esProducts.add(product);
264
265 }
266 }
267 result.setProducts(esProducts);
268
269 //3、当前商品涉及到的所有品牌信息,小米手机和小米电脑都属于小米品牌,过滤重复品牌信息
270 List<ESResponseResult.BrandVo> brandVos = new ArrayList<>();
271
272 // 获取聚合结果
273 Map<String, Aggregate> aggs = response.aggregations();
274 //获取到品牌的聚合
275 Aggregate brandAgg = aggs.get("brand_agg");
276 if (brandAgg != null) {
277 List<LongTermsBucket> brandIdBuckets = brandAgg.lterms().buckets().array();
278 for (LongTermsBucket brandIdBucket : brandIdBuckets) {
279 //构建品牌信息
280 ESResponseResult.BrandVo brandVo = new ESResponseResult.BrandVo();
281 //设置品牌ID
282 brandVo.setBrandId(brandIdBucket.key());
283
284 Aggregate brandImgAgg =
brandIdBucket.aggregations().get("brand_img_agg");
285 Aggregate brandNameAgg =
brandIdBucket.aggregations().get("brand_name_agg");
286 if (brandImgAgg != null && brandNameAgg != null) {
287 StringTermsBucket imgBucket =
brandImgAgg.sterms().buckets().array().get(0);
288 StringTermsBucket nameBucket =
brandNameAgg.sterms().buckets().array().get(0);
289 //设置品牌的图片和名称
290 brandVo.setBrandImg(imgBucket.key().stringValue());
291 brandVo.setBrandName(nameBucket.key().stringValue());
292 }
293 brandVos.add(brandVo);
294 }
295 }
296 result.setBrands(brandVos);
297

298
299 //4、当前商品相关的所有类目信息
300 //获取到分类的聚合
301 List<ESResponseResult.categoryVo> categoryVos = new ArrayList<>();
302
303 Aggregate categoryAgg = aggs.get("category_agg");
304 if (categoryAgg != null) {
305 List<LongTermsBucket> categoryBuckets =
categoryAgg.lterms().buckets().array();
306 for (LongTermsBucket categoryBucket : categoryBuckets) {
307 //构建分类信息
308 ESResponseResult.categoryVo categoryVo = new
ESResponseResult.categoryVo();
309 //设置分类ID
310 categoryVo.setCategoryId(categoryBucket.key());
311
312 Aggregate categoryNameAgg =
categoryBucket.aggregations().get("category_name_agg");
313 if (categoryNameAgg != null) {
314 StringTermsBucket nameBucket =
categoryNameAgg.sterms().buckets().array().get(0);
315 //设置分类名称
316 categoryVo.setCategoryName(nameBucket.key().stringValue());
317 }
318 categoryVos.add(categoryVo);
319 }
320 }
321 result.setCategorys(categoryVos);
322
323
324 //5、获取商品相关的所有属性信息
325 List<ESResponseResult.AttrVo> attrVos = new ArrayList<>();
326 //获取属性信息的聚合
327 Aggregate attrsAgg = aggs.get("attrs_agg");
328 if (attrsAgg != null) {
329 //获取属性id的集合
330 Aggregate attrIdAgg = attrsAgg.nested().aggregations().get("attr_id_agg");
331 List<LongTermsBucket> attrBuckets = attrIdAgg.lterms().buckets().array();
332 for (LongTermsBucket attrBucket : attrBuckets) {
333 //构建属性信息
334 ESResponseResult.AttrVo attrVo = new ESResponseResult.AttrVo();
335 //设置属性ID

336 attrVo.setAttrId(attrBucket.key());
337
338 Aggregate attrNameAgg = attrBucket.aggregations().get("attr_name_agg");
339 Aggregate attrValueAgg =
attrBucket.aggregations().get("attr_value_agg");
340 if (attrNameAgg != null && attrValueAgg != null) {
341 StringTermsBucket attrNameBucket =
attrNameAgg.sterms().buckets().array().get(0);
342 //设置属性名称
343 attrVo.setAttrName(attrNameBucket.key().stringValue());
344
345 List<StringTermsBucket> attrValueBuckets =
attrValueAgg.sterms().buckets().array();
346 List<String> attrValues = new ArrayList<>();
347 for (StringTermsBucket attrValueBucket : attrValueBuckets) {
348 attrValues.add(attrValueBucket.key().stringValue());
349 }
350 //设置属性值
351 attrVo.setAttrValue(attrValues);
352 }
353 attrVos.add(attrVo);
354 }
355 }
356 result.setAttrs(attrVos);
357
358 //6、进行分页操作
359 result.setPageNum(param.getPageNum());
360 //获取总记录数
361 long total = hitsMetadata.total().value();
362 result.setTotal(total);
363
364 //计算总页码
365 int totalPages = (int) total % SearchConstant.PAGE_SIZE == 0 ? (int) total /
SearchConstant.PAGE_SIZE : ((int) total / SearchConstant.PAGE_SIZE + 1);
366 result.setTotalPages(totalPages);
367
368 List<Integer> pageNavs = new ArrayList<>();
369 for (int i = 1; i <= totalPages; i++) {
370 pageNavs.add(i);
371 }
372 result.setPageNavs(pageNavs);
373

374 return result;
375 }
376
377 }
378
379
380
381
382
测试
http://localhost:8054/searchList?price=1_5000&keyword=%E6%89%8B%E6%9C%BA&sort=salecou
nt_asc&hasStock=1&pageNum=1&pageSize=20&categoryId=19&attrs=2_%E8%93%9D%E8%89%B
2&attrs=1_2%E6%A0%B8
