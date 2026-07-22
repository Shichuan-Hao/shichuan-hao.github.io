---



title: "1 Spring Boot整合ElasticSearch8.x实战"
description: "官方网站: 2. Spring Boot 整合 Spring Data Elasticsearch 1)版本选型 Elasticsearch 8.14.x 对应"
author: hsc
date: 2024-07-24 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', '中间件', 'ElasticSearch']
toc: true



---

### 1. Spring Data Elasticsearch 的介绍 Spring Data Elasticsearch 基于 spring data API 简化 Elasticsearch 操作,将原始操作 Elasticsearch 的客户端 API 进行封装 。Spring Data 为 Elasticsearch 项目提供集成搜索引擎。 Spring DataElasticsearch POJO 的关键功能区域为中心的模型与 Elastichsearch 交互文档和轻松地编写一个存储索引库数据访问层。
官方网站: https://spring.io/projects/spring-data-elasticsearch
2. Spring Boot 整合 Spring Data Elasticsearch
1)版本选型 Elasticsearch 8.14.x 对应依赖 Spring Data Elasticsearch 5.3.x,对应 Spring6.1.x,Spring Boot 版本可以选择 3.3.x2)引入依赖

1 <dependency>2 <groupId>org.springframework.boot</groupId>3 <spanrtifactId>spring-boot-starter-data-elasticsearch</artifactId>4 </dependency>如果 Spring Boot 版本选择 3.3.2,对应的 Spring Data Elasticsearch 为 5.3.23)配置 ElasticSearchSpring Boot 中有两种配置 ElasticSearch 的方式,选择一种即可。
方式 1:yml 配置 1 spring:
2 elasticsearch:
3 uris: http://localhost:92004 connection-timeout: 3s 方式 2: @Configuration 配置 1 @Configuration2 public class MyESClientConfig extends ElasticsearchConfiguration {34 @Override5 public ClientConfiguration clientConfiguration() {6 return ClientConfiguration.builder().connectedTo("localhost:9200").build();
7 }8 }4)Java 代码实现方式 1:使用 ElasticsearchRepository

ElasticsearchRepository 是 Spring Data Elasticsearch 项目中的一个接口,用于简化对 Elasticsearch 集群的 CRUD 操作以及其他高级搜索功能的集成。这个接口允许开发者通过声明式编程模型来执行数据持久化操作,从而避免直接编写复杂的 REST API 调用代码。
创建实体类 1 @Data2 @AllArgsConstructor3 @NoArgsConstructor4 @Document(indexName = "employees")
5 public class Employee {6 @Id7 private Long id;
8 @Field(type= FieldType.Keyword)
9 private String name;
10 private int sex;
11 private int age;
12 @Field(type= FieldType.Text,analyzer="ik_max_word")
13 private String address;
14 private String remark;
15 }实现 ElasticsearchRepository 接口该接口是框架封装的用于操作 Elastsearch 的高级接口 1 @Repository2 public interface EmployeeRepository extends ElasticsearchRepository<Employee, Long> {3 List<Employee> findByName(String name);
4 }测试

1 @Autowired2 EmployeeRepository employeeRepository;
34 @Test5 public void testDocument() {67 Employee employee = new Employee(10L, "fox666", 1, 32, "长沙麓谷", "javaarchitect");
8 //插入文档 9 employeeRepository.save(employee);
1011 //根据 id 查询 12 Optional<Employee> result = employeeRepository.findById(10L);
13 if (!result.isEmpty()){14 log.info(String.valueOf(result.get()));
15 }161718 //根据 name 查询 19 List<Employee> list = employeeRepository.findByName("fox666");
20 if(!list.isEmpty()){21 log.info(String.valueOf(list.get(0)));
22 }2324 }更多实现参考官方文档:https://docs.spring.io/spring-data/elasticsearch/reference/elasticsearch/repositories/elasticsearch-repository-queries.html 方式 2:使用 ElasticsearchTemplateElasticsearchTemplate 模板类,封装了便捷操作 Elasticsearch 的模板方法,包括 索引 / 映射 / 文档 CRUD 等底层操作和高级操作。
1 @Autowired2 ElasticsearchTemplate elasticsearchTemplate;

从 Java Rest Client 7.15.0 版本开始,Elasticsearch 官方决定将 RestHighLevelClient 标记为废弃的,并推荐使用新的 Java API Client,即 ElasticsearchClient. Spring Data ElasticSearch 对 ElasticsearchClient 做了进一步的封装,成了新的客户端 ElasticsearchTemplate 测试

1 @Slf4j2 public class ElasticsearchClientTest extends VipEsDemoApplicationTests{34 @Autowired5 ElasticsearchTemplate elasticsearchTemplate;
678 @Test9 public void testCreateIndex(){1011 //索引是否存在 12 boolean exist = elasticsearchTemplate.indexOps(Employee.class).exists();
13 if(exist){14 //删除索引 15 elasticsearchTemplate.indexOps(Employee.class).delete();
16 }17 //创建索引 18 //1)配置 settings19 Map<String, Object> settings = new HashMap<>();
20 //"number_of_shards": 1,21 //"number_of_replicas": 122 settings.put("number_of_shards",1);
23 settings.put("number_of_replicas",1);
24 //2) 配置 mapping25 String json = "{\n" +26 " \"properties\": {\n" +27 " \"_class\": {\n" +28 " \"type\": \"text\",\n" +29 " \"fields\": {\n" +30 " \"keyword\": {\n" +31 " \"type\": \"keyword\",\n" +32 " \"ignore_above\": 256\n" +33 " }\n" +34 " }\n" +35 " },\n" +36 " \"address\": {\n" +37 " \"type\": \"text\",\n" +38 " \"fields\": {\n" +39 " \"keyword\": {\n" +

40 " \"type\": \"keyword\"\n" +41 " }\n" +42 " },\n" +43 " \"analyzer\": \"ik_max_word\"\n" +44 " },\n" +45 " \"age\": {\n" +46 " \"type\": \"integer\"\n" +47 " },\n" +48 " \"id\": {\n" +49 " \"type\": \"long\"\n" +50 " },\n" +51 " \"name\": {\n" +52 " \"type\": \"keyword\"\n" +53 " },\n" +54 " \"remark\": {\n" +55 " \"type\": \"text\",\n" +56 " \"fields\": {\n" +57 " \"keyword\": {\n" +58 " \"type\": \"keyword\"\n" +59 " }\n" +60 " },\n" +61 " \"analyzer\": \"ik_smart\"\n" +62 " },\n" +63 " \"sex\": {\n" +64 " \"type\": \"integer\"\n" +65 " }\n" +66 " }\n" +67 " }";
68 Document mapping = Document.parse(json);
69 //3)创建索引 70 elasticsearchTemplate.indexOps(Employee.class)
71 .create(settings,mapping);
7273 //查看索引 mappings 信息 74 Map<String, Object> mappings =elasticsearchTemplate.indexOps(Employee.class).getMapping();
75 log.info(mappings.toString());
767778 }8081 @Test82 public void testBulkBatchInsert(){83 List<Employee> employees = new ArrayList<>();
84 employees.add(new Employee(2L,"张三",1,25,"广州天河公园","java developer"));
85 employees.add(new Employee(3L,"李四",1,28,"广州荔湾大厦","java assistant"));
86 employees.add(new Employee(4L,"小红",0,26,"广州白云山公园","php developer"));
8788 List<IndexQuery> bulkInsert = new ArrayList<>();
89 for (Employee employee : employees) {90 IndexQuery indexQuery = new IndexQuery();
91 indexQuery.setId(String.valueOf(employee.getId()));
92 String json = JSONObject.toJSONString(employee);
93 indexQuery.setSource(json);
94 bulkInsert.add(indexQuery);
95 }96 //bulk 批量插入文档 97 elasticsearchTemplate.bulkIndex(bulkInsert,Employee.class);
98 }99100101 @Test102 public void testDocument(){103104 //根据 id 删除文档 105 //对应: DELETE /employee/_doc/12106 elasticsearchTemplate.delete(String.valueOf(12L),Employee.class);
107108 Employee employee = new Employee(12L,"张三三",1,25,"广州天河公园","javadeveloper");
109 //插入文档 110 elasticsearchTemplate.save(employee);
111112 //根据 id 查询文档 113 //对应:GET /employee/_doc/12114 Employee emp = elasticsearchTemplate.get(String.valueOf(12L),Employee.class);
115 log.info(String.valueOf(emp));
116117 }118120121 @Test122 public void testQueryDocument(){123 //条件查询 124 /* 查询姓名为张三的员工信息 125 GET /employee/_search126 {127 "query": {128 "term": {129 "name": {130 "value": "张三"
131 }132 }133 }134 }*/135136 //第一步:构建查询语句 137 //方式 1:StringQuery138 // Query query = new StringQuery("{\n" +139 // " \"term\": {\n" +140 // " \"name\": {\n" +141 // " \"value\": \"张三\"\n" +142 // " }\n" +143 // " }\n" +144 // " }");
145 //方式 2:NativeQuery146 Query query = NativeQuery.builder()
147 .withQuery(q -> q.term(148 t -> t.field("name").value("张三")))
149 .build();
150151152 //第二步:调用 search 查询 153 SearchHits<Employee> search = elasticsearchTemplate.search(query,Employee.class);
154 //第三步:解析返回结果 155 List<SearchHit<Employee>> searchHits = search.getSearchHits();
156 for (SearchHit hit: searchHits){157 log.info("返回结果:"+hit.toString());
158 }160161 }162163164 @Test165 public void testMatchQueryDocument(){166 //条件查询 167 /*最少匹配广州,公园两个词 168 GET /employee/_search169 {170 "query": {171 "match": {172 "address": {173 "query": "广州公园",174 "minimum_should_match": 2175 }176 }177 }178 }*/179180 //第一步:构建查询语句 181 //方式 1:StringQuery182 // Query query = new StringQuery("{\n" +183 // " \"match\": {\n" +184 // " \"address\": {\n" +185 // " \"query\": \"广州公园\",\n" +186 // " \"minimum_should_match\": 2\n" +187 // " }\n" +188 // " }\n" +189 // " }");
190 //方式 2:NativeQuery191 Query query = NativeQuery.builder()
192 .withQuery(q -> q.match(193 m -> m.field("address").query("广州公园")
194 .minimumShouldMatch("2")))
195 .build();
196197198 //第二步:调用 search 查询 199 SearchHits<Employee> search = elasticsearchTemplate.search(query,Employee.class);

200 //第三步:解析返回结果 201 List<SearchHit<Employee>> searchHits = search.getSearchHits();
202 for (SearchHit hit: searchHits){203 log.info("返回结果:"+hit.toString());
204 }205206 }207208 @Test209 public void testQueryDocument3(){210 // 分页排序高亮 211 /*212 GET /employee/_search213 {214 "from": 0,215 "size": 3,216 "query": {217 "match": {218 "remark": {219 "query": "JAVA"
220 }221 }222 },223 "highlight": {224 "pre_tags": ["<font color='red'>"],225 "post_tags": ["<font/>"],226 "require_field_match": "false",227 "fields": {228 "*":{}229 }230 },231 "sort": [232 {233 "age": {234 "order": "desc"
235 }236 }237 ]238 }*/239 //第一步:构建查询语句

240 Query query = new StringQuery("{\n" +241 " \"match\": {\n" +242 " \"remark\": {\n" +243 " \"query\": \"JAVA\"\n" +244 " }\n" +245 " }\n" +246 " }");
247 //分页 注意:from = pageNumber(页码,从 0 开始,) * pageSize(每页的记录数)
248 query.setPageable(PageRequest.of(0, 3));
249 //排序 250 query.addSort(Sort.by(Order.desc("age")));
251 //高亮 252 HighlightField highlightField = new HighlightField("*");
253 HighlightParameters highlightParameters = newHighlightParameters.HighlightParametersBuilder()
254 .withPreTags("<font color='red'>")
255 .withPostTags("<font/>")
256 .withRequireFieldMatch(false)
257 .build();
258 Highlight highlight = newHighlight(highlightParameters,Arrays.asList(highlightField));
259 HighlightQuery highlightQuery = new HighlightQuery(highlight,Employee.class);
260261 query.setHighlightQuery(highlightQuery);
262263264 //第二步:调用 search 查询 265 SearchHits<Employee> search = elasticsearchTemplate.search(query,Employee.class);
266 //第三步:解析返回结果 267 List<SearchHit<Employee>> searchHits = search.getSearchHits();
268 for (SearchHit hit: searchHits){269 log.info("返回结果:"+hit.toString());
270 }271 }272273274 @Test275 public void testBoolQueryDocument(){276 //条件查询 277 /*

278 GET /employee/_search279 {280 "query": {281 "bool": {282 "must": [283 {284 "match": {285 "address": "广州"
286 }287 },{288 "match": {289 "remark": "java"
290 }291 }292 ]293 }294 }295 }296 */297298 //第一步:构建查询语句 299 //方式 1:StringQuery300 // Query query = new StringQuery("{\n" +301 // " \"bool\": {\n" +302 // " \"must\": [\n" +303 // " {\n" +304 // " \"match\": {\n" +305 // " \"address\": \"广州\"\n" +306 // " }\n" +307 // " },{\n" +308 // " \"match\": {\n" +309 // " \"remark\": \"java\"\n" +310 // " }\n" +311 // " }\n" +312 // " ]\n" +313 // " }\n" +314 // " }");
315 //方式 2:NativeQuery316 Query query = NativeQuery.builder()
317 .withQuery(q -> q.bool(

318 m -> m.must(319 QueryBuilders.match( q1 -> q1.field("address").query("广州")),320 QueryBuilders.match( q2 -> q2.field("remark").query("java"))
321 )))
322 .build();
323324 //第二步:调用 search 查询 325 SearchHits<Employee> search = elasticsearchTemplate.search(query,Employee.class);
326 //第三步:解析返回结果 327 List<SearchHit<Employee>> searchHits = search.getSearchHits();
328 for (SearchHit hit: searchHits){329 log.info("返回结果:"+hit.toString());
330 }331332 }333334 }方式 3:使用 ElasticsearchClient 从 Java Rest Client 7.15.0 版本开始,Elasticsearch 官方决定将 RestHighLevelClient 标记为废弃的,并推荐使用新的 Java API Client,即 ElasticsearchClient.官网文档:https://www.elastic.co/guide/en/elasticsearch/client/java-api-client/8.14/getting-started-java.html 测试

1 @Autowired2 ElasticsearchClient elasticsearchClient;
34 String indexName = "employee_demo";
56 @Test7 public void testCreateIndex() throws IOException {89 //索引是否存在 10 BooleanResponse exist = elasticsearchClient.indices()
11 .exists(e->e.index(indexName));
12 if(exist.value()){13 //删除索引 14 elasticsearchClient.indices().delete(d->d.index(indexName));
15 }16 //创建索引 17 elasticsearchClient.indices().create(c->c.index(indexName)
18 .settings(s->s.numberOfShards("1").numberOfReplicas("1"))
19 .mappings(m-> m.properties("name",p->p.keyword(k->k))
20 .properties("sex",p->p.long_(l->l))
21 .properties("address",p->p.text(t->t.analyzer("ik_max_word")))
22 )
23 );
2425 //查询索引 26 GetIndexResponse getIndexResponse = elasticsearchClient.indices().get(g ->g.index(indexName));
27 log.info(getIndexResponse.result().toString());
2829 }303132 @Test33 public void testBulkBatchInsert() throws IOException {34 List<Employee> employees = new ArrayList<>();
35 employees.add(new Employee(2L,"张三",1,25,"广州天河公园","java developer"));
36 employees.add(new Employee(3L,"李四",1,28,"广州荔湾大厦","java assistant"));
37 employees.add(new Employee(4L,"小红",0,26,"广州白云山公园","php developer"));
3839 List<IndexQuery> bulkInsert = new ArrayList<>();

40 for (Employee employee : employees) {41 IndexQuery indexQuery = new IndexQuery();
42 indexQuery.setId(String.valueOf(employee.getId()));
43 String json = JSONObject.toJSONString(employee);
44 indexQuery.setSource(json);
45 bulkInsert.add(indexQuery);
46 }47 List<BulkOperation> list = new ArrayList<>();
48 for (Employee employee : employees) {49 BulkOperation bulkOperation = new BulkOperation.Builder()
50 .create(c->c.id(String.valueOf(employee.getId()))
51 .document(employee)
52 )
53 .build();
5455 list.add(bulkOperation);
56 }5758 //bulk 批量插入文档 59 elasticsearchClient.bulk(b->b.index(indexName).operations(list));
60 }6162 @Test63 public void testDocument() throws IOException {64 Employee employee = new Employee(12L,"张三三",1,25,"广州天河公园","java developer");
6566 IndexRequest<Employee> request = IndexRequest.of(i -> i67 .index(indexName)
68 .id(employee.getId().toString())
69 .document(employee)
70 );
7172 IndexResponse response = elasticsearchClient.index(request);
7374 log.info("response:"+response);
75 }767778 @Test79 public void testQuery() throws IOException {

80 SearchRequest searchRequest = SearchRequest.of(s -> s81 .index(indexName)
82 .query(q -> q.match(m -> m.field("name").query("张三三"))
83 ));
8485 log.info("构建的 DSL 语句:"+ searchRequest.toString());
8687 SearchResponse<Employee> searchResponse = elasticsearchClient.search(searchRequest,Employee.class);
8889 List<Hit<Employee>> hits = searchResponse.hits().hits();
90 hits.stream().map(Hit::source).forEach(employee -> {91 log.info("员工信息:"+employee);
92 });
9394 }9596 @Test97 public void testBoolQueryDocument() throws IOException {98 //条件查询 99 /*100 GET /employee/_search101 {102 "query": {103 "bool": {104 "must": [105 {106 "match": {107 "address": "广州"
108 }109 },{110 "match": {111 "remark": "java"
112 }113 }114 ]115 }116 }117 }118 */120 //第一步:构建查询语句 121 BoolQuery.Builder boolQueryBuilder = new BoolQuery.Builder();
122 boolQueryBuilder.must(m->m.match(q->q.field("address").query("广州")))
123 .must(m->m.match(q->q.field("remark").query("java")));
124125 SearchRequest searchRequest = new SearchRequest.Builder()
126 .index("employee")
127 .query(q->q.bool(boolQueryBuilder.build()))
128 .build();
129130 //第二步:调用 search 查询 131 SearchResponse<Employee> searchResponse = elasticsearchClient.search(searchRequest,Employee.class);
132 //第三步:解析返回结果 133 List<Hit<Employee>> list = searchResponse.hits().hits();
134 for(Hit<Employee> hit: list){135 //返回 source136 log.info(String.valueOf(hit.source()));
137 }138139 }
