---
layout: post
title: "Spring Boot整合ElasticSearch 8.x实战：Repository与Template双模式"
date: 2022-06-20
categories: [distributed]
tags: [ElasticSearch, Spring Boot, Spring Data, Repository, ElasticsearchTemplate]
comments: true
---

> Spring Data Elasticsearch 基于 Spring Data API 简化 ES 操作，提供 POJO 为中心的模型与 ES 交互。

---

## 一、版本选型

| 组件 | 版本 |
|------|------|
| Elasticsearch | 8.14.x |
| Spring Data Elasticsearch | 5.3.x |
| Spring Framework | 6.1.x |
| Spring Boot | 3.3.x |

如果 Spring Boot 3.3.2 → Spring Data Elasticsearch 5.3.2

---

## 二、引入依赖

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-elasticsearch</artifactId>
</dependency>
```

---

## 三、配置 Elasticsearch

### 方式一：yml 配置

```yaml
spring:
  elasticsearch:
    uris: http://localhost:9200
    connection-timeout: 3s
```

### 方式二：@Configuration 配置

```java
@Configuration
public class MyESClientConfig extends ElasticsearchConfiguration {

    @Override
    public ClientConfiguration clientConfiguration() {
        return ClientConfiguration.builder()
            .connectedTo("localhost:9200")
            .build();
    }
}
```

> 从 ES 7.15.0 开始，`RestHighLevelClient` 被标记为废弃，推荐使用新的 `ElasticsearchClient`。Spring Data 封装后成为 `ElasticsearchTemplate`。

---

## 四、方式一：ElasticsearchRepository

### 1、创建实体类

```java
@Data
@AllArgsConstructor
@NoArgsConstructor
@Document(indexName = "employees")
public class Employee {
    @Id
    private Long id;
    
    @Field(type = FieldType.Keyword)
    private String name;
    
    private int sex;
    private int age;

    @Field(type = FieldType.Text, analyzer = "ik_max_word")
    private String address;
    
    private String remark;
}
```

**常用注解**：

| 注解 | 说明 |
|------|------|
| `@Document` | 标记实体类为 ES 文档，指定 indexName |
| `@Id` | 标记主键字段 |
| `@Field` | 字段映射配置（type/analyzer/searchAnalyzer/name 等） |
| `@Transient` | 不参与序列化 |

### 2、创建 Repository 接口

```java
@Repository
public interface EmployeeRepository extends ElasticsearchRepository<Employee, Long> {
    
    // 方法名自动生成查询
    List<Employee> findByName(String name);
    
    // 更多自动支持的方法
    List<Employee> findByAgeBetween(int min, int max);
    List<Employee> findByAddressContaining(String keyword);
}
```

**支持的方法命名规则**（类似 Spring Data JPA）：

| 关键字 | 方法名 | ES 操作 |
|--------|--------|---------|
| `And` | `findByNameAndAge` | must + term |
| `Or` | `findByNameOrAge` | should |
| `Between` | `findByAgeBetween` | range |
| `Containing` | `findByAddressContaining` | match |
| `LessThan` | `findByAgeLessThan` | range |
| `GreaterThan` | `findByAgeGreaterThan` | range |

### 3、使用 Repository

```java
@Autowired
EmployeeRepository employeeRepository;

@Test
public void testDocument() {
    // 插入 / 更新文档
    Employee employee = new Employee(10L, "fox666", 1, 32, "长沙麓谷", "java architect");
    employeeRepository.save(employee);

    // 根据 ID 查询
    Optional<Employee> result = employeeRepository.findById(10L);
    
    // 根据 name 查询
    List<Employee> list = employeeRepository.findByName("fox666");
    
    // 删除
    employeeRepository.deleteById(10L);
}
```

---

## 五、方式二：ElasticsearchTemplate

动态查询、复杂操作场景推荐使用 Template。

### 基础操作

```java
@Slf4j
public class ElasticsearchClientTest {
    
    @Autowired
    ElasticsearchTemplate elasticsearchTemplate;

    @Test
    public void testCreateIndex() {
        // 索引是否存在
        boolean exist = elasticsearchTemplate.indexOps(Employee.class).exists();
        if (!exist) {
            // 创建索引（根据 @Document 和 @Field 注解自动生成 mapping）
            elasticsearchTemplate.indexOps(Employee.class).create();
        }
    }

    @Test
    public void testSave() {
        Employee employee = new Employee(1L, "张三", 1, 25, "广州天河", "java developer");
        // 保存 / 更新
        elasticsearchTemplate.save(employee);
    }

    @Test
    public void testFindById() {
        Employee employee = elasticsearchTemplate.get("1", Employee.class);
        log.info(employee.toString());
    }

    @Test
    public void testDelete() {
        // 删除文档
        elasticsearchTemplate.delete("1", Employee.class);
        // 删除索引
        elasticsearchTemplate.indexOps(Employee.class).delete();
    }
}
```

### 高级查询（NativeQuery）

```java
@Test
public void testSearch() {
    NativeQuery query = NativeQuery.builder()
        .withQuery(q -> q
            .bool(b -> b
                .must(m -> m.match(ma -> ma.field("remark").query("java")))
                .filter(f -> f.range(r -> r.field("age").gte(JsonData.of(20)).lte(JsonData.of(35))))
            )
        )
        .withPageable(PageRequest.of(0, 10))
        .build();
    
    SearchHits<Employee> hits = elasticsearchTemplate.search(query, Employee.class);
    hits.forEach(hit -> {
        Employee emp = hit.getContent();
        float score = hit.getScore();
        log.info("Employee: {}, Score: {}", emp, score);
    });
}
```

### CriteriaQuery

```java
@Test
public void testCriteriaQuery() {
    Criteria criteria = new Criteria("age").greaterThan(25).lessThan(35);
    Query query = new CriteriaQuery(criteria).setPageable(PageRequest.of(0, 10));
    
    SearchHits<Employee> hits = elasticsearchTemplate.search(query, Employee.class);
}
```

---

## 六、两种模式对比

| | Repository | Template |
|------|------------|----------|
| 使用方式 | 继承接口，方法名约定 | 直接注入使用 |
| 简单CRUD | ✅ 简洁快速 | 需写代码 |
| 复杂查询 | ❌ 有限（方法名太长） | ✅ 灵活强大 |
| 动态条件 | ❌ 不方便 | ✅ NativeQuery/CriteriaQuery |
| 聚合操作 | ❌ 不支持 | ✅ 支持 |
| **推荐场景** | 固定查询、简单业务 | 复杂搜索、动态条件 |

---

## 七、实际项目配置建议

```java
@Configuration
public class ElasticsearchConfig {
    
    @Bean
    public ElasticsearchTemplate elasticsearchTemplate(ElasticsearchClient client) {
        return new ElasticsearchTemplate(client);
    }
}

// 在业务 Service 中注入使用
@Service
public class EmployeeService {
    
    @Autowired
    private ElasticsearchTemplate template;
    
    @Autowired  
    private EmployeeRepository repository;
    
    // 简单查询 → repository
    public List<Employee> findByName(String name) {
        return repository.findByName(name);
    }
    
    // 复杂搜索 → template
    public SearchHits<Employee> advancedSearch(SearchParam param) {
        // ...构建复杂 NativeQuery
        return template.search(query, Employee.class);
    }
}
```

> 官方文档：[Spring Data Elasticsearch](https://docs.spring.io/spring-data/elasticsearch/reference/)

> 有道云笔记：[Spring Boot整合ES](https://note.youdao.com/s/dhwCycLz)
