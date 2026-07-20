---
title: "1 Spring Boot整合ElasticSearch8.x实战"
description: "主讲老师:Fox 有道云笔记地址:https://note.youdao.com/s/dhwCycLz 1. Spring Data Elasticsearch的介绍 Spring Data Elasticsearch 基于 spring data API 简化 Elasticsearch 操作,将原始操作Elasticsearch 的客户端 API 进行封装 。Spring Data 为 ..."
author: hsc
date: 2022-03-12 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', 'Redis', 'Kafka', 'RocketMQ', 'Netty', 'ElasticSearch', 'ShardingSphere', 'ES', '实战', 'Spring']
toc: true
---

> 本文整理自《四、分布式专题》课程笔记，共 18 页。

主讲老师:Fox
有道云笔记地址:https://note.youdao.com/s/dhwCycLz
1. Spring Data Elasticsearch的介绍
Spring Data Elasticsearch 基于 spring data API 简化 Elasticsearch 操作,将原始操作Elasticsearch
的客户端 API 进行封装 。Spring Data 为 Elasticsearch 项目提供集成搜索引擎。Spring Data
Elasticsearch POJO 的关键功能区域为中心的模型与 Elastichsearch 交互文档和轻松地编写一个存储
索引库数据访问层。
官方网站: https://spring.io/projects/spring-data-elasticsearch
2. Spring Boot整合Spring Data Elasticsearch
1)版本选型
Elasticsearch 8.14.x 对应依赖 Spring Data Elasticsearch 5.3.x,对应Spring6.1.x,Spring Boot版本可
以选择3.3.x
2)引入依赖

1 <dependency>
2 <groupId>org.springframework.boot</groupId>
3 <spanrtifactId>spring-boot-starter-data-elasticsearch</artifactId>
4 </dependency>
如果Spring Boot版本选择3.3.2,对应的Spring Data Elasticsearch为5.3.2
3)配置ElasticSearch
Spring Boot中有两种配置ElasticSearch的方式,选择一种即可。
方式1:yml配置
1 spring:
2 elasticsearch:
3 uris: http://localhost:9200
4 connection-timeout: 3s
方式2: @Configuration配置
1 @Configuration
2 public class MyESClientConfig extends ElasticsearchConfiguration {
3
4 @Override
5 public ClientConfiguration clientConfiguration() {
6 return ClientConfiguration.builder().connectedTo("localhost:9200").build();
7 }
8 }
4)Java代码实现
方式1:使用ElasticsearchRepository

ElasticsearchRepository 是Spring Data Elasticsearch项目中的一个接口,用于简化对Elasticsearch集
群的CRUD操作以及其他高级搜索功能的集成。这个接口允许开发者通过声明式编程模型来执行数据
持久化操作,从而避免直接编写复杂的REST API调用代码。
创建实体类
1 @Data
2 @AllArgsConstructor
3 @NoArgsConstructor
4 @Document(indexName = "employees")
5 public class Employee {
6 @Id
7 private Long id;
8 @Field(type= FieldType.Keyword)
9 private String name;
10 private int sex;
11 private int age;
12 @Field(type= FieldType.Text,analyzer="ik_max_word")
13 private String address;
14 private String remark;
15 }
实现ElasticsearchRepository接口
该接口是框架封装的用于操作Elastsearch的高级接口
1 @Repository
2 public interface EmployeeRepository extends ElasticsearchRepository<Employee, Long> {
3 List<Employee> findByName(String name);
4 }
测试

1 @Autowired
2 EmployeeRepository employeeRepository;
3
4 @Test
5 public void testDocument() {
6
7 Employee employee = new Employee(10L, "fox666", 1, 32, "长沙麓谷", "java
architect");
8 //插入文档
9 employeeRepository.save(employee);
10
11 //根据id查询
12 Optional<Employee> result = employeeRepository.findById(10L);
13 if (!result.isEmpty()){
14 log.info(String.valueOf(result.get()));
15 }
16
17
18 //根据name查询
19 List<Employee> list = employeeRepository.findByName("fox666");
20 if(!list.isEmpty()){
21 log.info(String.valueOf(list.get(0)));
22 }
23
24 }
更多实现参考官方文档:https://docs.spring.io/spring-data/elasticsearch/reference/elasticsearch/repo
sitories/elasticsearch-repository-queries.html
方式2:使用ElasticsearchTemplate
ElasticsearchTemplate模板类,封装了便捷操作Elasticsearch的模板方法,包括 索引 / 映射 / 文档
CRUD 等底层操作和高级操作。
1 @Autowired
2 ElasticsearchTemplate elasticsearchTemplate;

从 Java Rest Client 7.15.0 版本开始,Elasticsearch 官方决定将 RestHighLevelClient 标记为废弃
的,并推荐使用新的 Java API Client,即 ElasticsearchClient. Spring Data ElasticSearch对
ElasticsearchClient做了进一步的封装,成了新的客户端 ElasticsearchTemplate
测试

1 @Slf4j
2 public class ElasticsearchClientTest extends VipEsDemoApplicationTests{
3
4 @Autowired
5 ElasticsearchTemplate elasticsearchTemplate;
6
7
8 @Test
9 public void testCreateIndex(){
10
11 //索引是否存在
12 boolean exist = elasticsearchTemplate.indexOps(Employee.class).exists();
13 if(exist){
14 //删除索引
15 elasticsearchTemplate.indexOps(Employee.class).delete();
16 }
17 //创建索引
18 //1)配置settings
19 Map<String, Object> settings = new HashMap<>();
20 //"number_of_shards": 1,
21 //"number_of_replicas": 1
22 settings.put("number_of_shards",1);
23 settings.put("number_of_replicas",1);
24 //2) 配置mapping
25 String json = "{\n" +
26 " \"properties\": {\n" +
27 " \"_class\": {\n" +
28 " \"type\": \"text\",\n" +
29 " \"fields\": {\n" +
30 " \"keyword\": {\n" +
31 " \"type\": \"keyword\",\n" +
32 " \"ignore_above\": 256\n" +
33 " }\n" +
34 " }\n" +
35 " },\n" +
36 " \"address\": {\n" +
37 " \"type\": \"text\",\n" +
38 " \"fields\": {\n" +
39 " \"keyword\": {\n" +

40 " \"type\": \"keyword\"\n" +
41 " }\n" +
42 " },\n" +
43 " \"analyzer\": \"ik_max_word\"\n" +
44 " },\n" +
45 " \"age\": {\n" +
46 " \"type\": \"integer\"\n" +
47 " },\n" +
48 " \"id\": {\n" +
49 " \"type\": \"long\"\n" +
50 " },\n" +
51 " \"name\": {\n" +
52 " \"type\": \"keyword\"\n" +
53 " },\n" +
54 " \"remark\": {\n" +
55 " \"type\": \"text\",\n" +
56 " \"fields\": {\n" +
57 " \"keyword\": {\n" +
58 " \"type\": \"keyword\"\n" +
59 " }\n" +
60 " },\n" +
61 " \"analyzer\": \"ik_smart\"\n" +
62 " },\n" +
63 " \"sex\": {\n" +
64 " \"type\": \"integer\"\n" +
65 " }\n" +
66 " }\n" +
67 " }";
68 Document mapping = Document.parse(json);
69 //3)创建索引
70 elasticsearchTemplate.indexOps(Employee.class)
71 .create(settings,mapping);
72
73 //查看索引mappings信息
74 Map<String, Object> mappings =
elasticsearchTemplate.indexOps(Employee.class).getMapping();
75 log.info(mappings.toString());
76
77
78 }
79

80
81 @Test
82 public void testBulkBatchInsert(){
83 List<Employee> employees = new ArrayList<>();
84 employees.add(new Employee(2L,"张三",1,25,"广州天河公园","java developer"));
85 employees.add(new Employee(3L,"李四",1,28,"广州荔湾大厦","java assistant"));
86 employees.add(new Employee(4L,"小红",0,26,"广州白云山公园","php developer"));
87
88 List<IndexQuery> bulkInsert = new ArrayList<>();
89 for (Employee employee : employees) {
90 IndexQuery indexQuery = new IndexQuery();
91 indexQuery.setId(String.valueOf(employee.getId()));
92 String json = JSONObject.toJSONString(employee);
93 indexQuery.setSource(json);
94 bulkInsert.add(indexQuery);
95 }
96 //bulk批量插入文档
97 elasticsearchTemplate.bulkIndex(bulkInsert,Employee.class);
98 }
99
100
101 @Test
102 public void testDocument(){
103
104 //根据id删除文档
105 //对应: DELETE /employee/_doc/12
106 elasticsearchTemplate.delete(String.valueOf(12L),Employee.class);
107
108 Employee employee = new Employee(12L,"张三三",1,25,"广州天河公园","java
developer");
109 //插入文档
110 elasticsearchTemplate.save(employee);
111
112 //根据id查询文档
113 //对应:GET /employee/_doc/12
114 Employee emp = elasticsearchTemplate.get(String.valueOf(12L),Employee.class);
115 log.info(String.valueOf(emp));
116
117 }
118
119

120
121 @Test
122 public void testQueryDocument(){
123 //条件查询
124 /* 查询姓名为张三的员工信息
125 GET /employee/_search
126 {
127 "query": {
128 "term": {
129 "name": {
130 "value": "张三"
131 }
132 }
133 }
134 }*/
135
136 //第一步:构建查询语句
137 //方式1:StringQuery
138 // Query query = new StringQuery("{\n" +
139 // " \"term\": {\n" +
140 // " \"name\": {\n" +
141 // " \"value\": \"张三\"\n" +
142 // " }\n" +
143 // " }\n" +
144 // " }");
145 //方式2:NativeQuery
146 Query query = NativeQuery.builder()
147 .withQuery(q -> q.term(
148 t -> t.field("name").value("张三")))
149 .build();
150
151
152 //第二步:调用search查询
153 SearchHits<Employee> search = elasticsearchTemplate.search(query,
Employee.class);
154 //第三步:解析返回结果
155 List<SearchHit<Employee>> searchHits = search.getSearchHits();
156 for (SearchHit hit: searchHits){
157 log.info("返回结果:"+hit.toString());
158 }
159

160
161 }
162
163
164 @Test
165 public void testMatchQueryDocument(){
166 //条件查询
167 /*最少匹配广州,公园两个词
168 GET /employee/_search
169 {
170 "query": {
171 "match": {
172 "address": {
173 "query": "广州公园",
174 "minimum_should_match": 2
175 }
176 }
177 }
178 }*/
179
180 //第一步:构建查询语句
181 //方式1:StringQuery
182 // Query query = new StringQuery("{\n" +
183 // " \"match\": {\n" +
184 // " \"address\": {\n" +
185 // " \"query\": \"广州公园\",\n" +
186 // " \"minimum_should_match\": 2\n" +
187 // " }\n" +
188 // " }\n" +
189 // " }");
190 //方式2:NativeQuery
191 Query query = NativeQuery.builder()
192 .withQuery(q -> q.match(
193 m -> m.field("address").query("广州公园")
194 .minimumShouldMatch("2")))
195 .build();
196
197
198 //第二步:调用search查询
199 SearchHits<Employee> search = elasticsearchTemplate.search(query,
Employee.class);

200 //第三步:解析返回结果
201 List<SearchHit<Employee>> searchHits = search.getSearchHits();
202 for (SearchHit hit: searchHits){
203 log.info("返回结果:"+hit.toString());
204 }
205
206 }
207
208 @Test
209 public void testQueryDocument3(){
210 // 分页排序高亮
211 /*
212 GET /employee/_search
213 {
214 "from": 0,
215 "size": 3,
216 "query": {
217 "match": {
218 "remark": {
219 "query": "JAVA"
220 }
221 }
222 },
223 "highlight": {
224 "pre_tags": ["<font color='red'>"],
225 "post_tags": ["<font/>"],
226 "require_field_match": "false",
227 "fields": {
228 "*":{}
229 }
230 },
231 "sort": [
232 {
233 "age": {
234 "order": "desc"
235 }
236 }
237 ]
238 }*/
239 //第一步:构建查询语句

240 Query query = new StringQuery("{\n" +
241 " \"match\": {\n" +
242 " \"remark\": {\n" +
243 " \"query\": \"JAVA\"\n" +
244 " }\n" +
245 " }\n" +
246 " }");
247 //分页 注意:from = pageNumber(页码,从0开始,) * pageSize(每页的记录数)
248 query.setPageable(PageRequest.of(0, 3));
249 //排序
250 query.addSort(Sort.by(Order.desc("age")));
251 //高亮
252 HighlightField highlightField = new HighlightField("*");
253 HighlightParameters highlightParameters = new
HighlightParameters.HighlightParametersBuilder()
254 .withPreTags("<font color='red'>")
255 .withPostTags("<font/>")
256 .withRequireFieldMatch(false)
257 .build();
258 Highlight highlight = new
Highlight(highlightParameters,Arrays.asList(highlightField));
259 HighlightQuery highlightQuery = new HighlightQuery(highlight,Employee.class);
260
261 query.setHighlightQuery(highlightQuery);
262
263
264 //第二步:调用search查询
265 SearchHits<Employee> search = elasticsearchTemplate.search(query,
Employee.class);
266 //第三步:解析返回结果
267 List<SearchHit<Employee>> searchHits = search.getSearchHits();
268 for (SearchHit hit: searchHits){
269 log.info("返回结果:"+hit.toString());
270 }
271 }
272
273
274 @Test
275 public void testBoolQueryDocument(){
276 //条件查询
277 /*

278 GET /employee/_search
279 {
280 "query": {
281 "bool": {
282 "must": [
283 {
284 "match": {
285 "address": "广州"
286 }
287 },{
288 "match": {
289 "remark": "java"
290 }
291 }
292 ]
293 }
294 }
295 }
296 */
297
298 //第一步:构建查询语句
299 //方式1:StringQuery
300 // Query query = new StringQuery("{\n" +
301 // " \"bool\": {\n" +
302 // " \"must\": [\n" +
303 // " {\n" +
304 // " \"match\": {\n" +
305 // " \"address\": \"广州\"\n" +
306 // " }\n" +
307 // " },{\n" +
308 // " \"match\": {\n" +
309 // " \"remark\": \"java\"\n" +
310 // " }\n" +
311 // " }\n" +
312 // " ]\n" +
313 // " }\n" +
314 // " }");
315 //方式2:NativeQuery
316 Query query = NativeQuery.builder()
317 .withQuery(q -> q.bool(

318 m -> m.must(
319 QueryBuilders.match( q1 -> q1.field("address").query("广
州")),
320 QueryBuilders.match( q2 -> q2.field("remark").query("java"))
321 )))
322 .build();
323
324 //第二步:调用search查询
325 SearchHits<Employee> search = elasticsearchTemplate.search(query,
Employee.class);
326 //第三步:解析返回结果
327 List<SearchHit<Employee>> searchHits = search.getSearchHits();
328 for (SearchHit hit: searchHits){
329 log.info("返回结果:"+hit.toString());
330 }
331
332 }
333
334 }
方式3:使用ElasticsearchClient
从 Java Rest Client 7.15.0 版本开始,Elasticsearch 官方决定将 RestHighLevelClient 标记为废弃的,
并推荐使用新的 Java API Client,即 ElasticsearchClient.
官网文档:https://www.elastic.co/guide/en/elasticsearch/client/java-api-client/8.14/getting-started-jav
a.html
测试

1 @Autowired
2 ElasticsearchClient elasticsearchClient;
3
4 String indexName = "employee_demo";
5
6 @Test
7 public void testCreateIndex() throws IOException {
8
9 //索引是否存在
10 BooleanResponse exist = elasticsearchClient.indices()
11 .exists(e->e.index(indexName));
12 if(exist.value()){
13 //删除索引
14 elasticsearchClient.indices().delete(d->d.index(indexName));
15 }
16 //创建索引
17 elasticsearchClient.indices().create(c->c.index(indexName)
18 .settings(s->s.numberOfShards("1").numberOfReplicas("1"))
19 .mappings(m-> m.properties("name",p->p.keyword(k->k))
20 .properties("sex",p->p.long_(l->l))
21 .properties("address",p->p.text(t->t.analyzer("ik_max_word")))
22 )
23 );
24
25 //查询索引
26 GetIndexResponse getIndexResponse = elasticsearchClient.indices().get(g ->
g.index(indexName));
27 log.info(getIndexResponse.result().toString());
28
29 }
30
31
32 @Test
33 public void testBulkBatchInsert() throws IOException {
34 List<Employee> employees = new ArrayList<>();
35 employees.add(new Employee(2L,"张三",1,25,"广州天河公园","java developer"));
36 employees.add(new Employee(3L,"李四",1,28,"广州荔湾大厦","java assistant"));
37 employees.add(new Employee(4L,"小红",0,26,"广州白云山公园","php developer"));
38
39 List<IndexQuery> bulkInsert = new ArrayList<>();

40 for (Employee employee : employees) {
41 IndexQuery indexQuery = new IndexQuery();
42 indexQuery.setId(String.valueOf(employee.getId()));
43 String json = JSONObject.toJSONString(employee);
44 indexQuery.setSource(json);
45 bulkInsert.add(indexQuery);
46 }
47 List<BulkOperation> list = new ArrayList<>();
48 for (Employee employee : employees) {
49 BulkOperation bulkOperation = new BulkOperation.Builder()
50 .create(c->c.id(String.valueOf(employee.getId()))
51 .document(employee)
52 )
53 .build();
54
55 list.add(bulkOperation);
56 }
57
58 //bulk批量插入文档
59 elasticsearchClient.bulk(b->b.index(indexName).operations(list));
60 }
61
62 @Test
63 public void testDocument() throws IOException {
64 Employee employee = new Employee(12L,"张三三",1,25,"广州天河公园","java developer");
65
66 IndexRequest<Employee> request = IndexRequest.of(i -> i
67 .index(indexName)
68 .id(employee.getId().toString())
69 .document(employee)
70 );
71
72 IndexResponse response = elasticsearchClient.index(request);
73
74 log.info("response:"+response);
75 }
76
77
78 @Test
79 public void testQuery() throws IOException {

80 SearchRequest searchRequest = SearchRequest.of(s -> s
81 .index(indexName)
82 .query(q -> q.match(m -> m.field("name").query("张三三"))
83 ));
84
85 log.info("构建的DSL语句:"+ searchRequest.toString());
86
87 SearchResponse<Employee> searchResponse = elasticsearchClient.search(searchRequest,
Employee.class);
88
89 List<Hit<Employee>> hits = searchResponse.hits().hits();
90 hits.stream().map(Hit::source).forEach(employee -> {
91 log.info("员工信息:"+employee);
92 });
93
94 }
95
96 @Test
97 public void testBoolQueryDocument() throws IOException {
98 //条件查询
99 /*
100 GET /employee/_search
101 {
102 "query": {
103 "bool": {
104 "must": [
105 {
106 "match": {
107 "address": "广州"
108 }
109 },{
110 "match": {
111 "remark": "java"
112 }
113 }
114 ]
115 }
116 }
117 }
118 */
119

120 //第一步:构建查询语句
121 BoolQuery.Builder boolQueryBuilder = new BoolQuery.Builder();
122 boolQueryBuilder.must(m->m.match(q->q.field("address").query("广州")))
123 .must(m->m.match(q->q.field("remark").query("java")));
124
125 SearchRequest searchRequest = new SearchRequest.Builder()
126 .index("employee")
127 .query(q->q.bool(boolQueryBuilder.build()))
128 .build();
129
130 //第二步:调用search查询
131 SearchResponse<Employee> searchResponse = elasticsearchClient.search(searchRequest,
Employee.class);
132 //第三步:解析返回结果
133 List<Hit<Employee>> list = searchResponse.hits().hits();
134 for(Hit<Employee> hit: list){
135 //返回source
136 log.info(String.valueOf(hit.source()));
137 }
138
139 }
