---
title: "ElasticSearch 进阶：深度分页、集群调优与 SpringBoot 实战"
date: 2022-06-15
categories: distributed
tags: [ElasticSearch, 深度分页, Scroll, SearchAfter, PIT, 集群调优, SpringBoot]
mermaid: true
---

> 进阶内容往往在面试和技术方案评审中成为区分度。本文覆盖深度分页四种方案对比、分词器定制、集群管理、性能调优、SpringBoot 集成、数据一致性保障等 ES 高级话题。

## 一、深度分页问题与解决方案

### 1.1 为什么 from+size 会有深度分页问题？

ES 的搜索结果是跨分片查询的。以查询第 10001~10100 条为例：

```
协调节点 → 向3个分片各请求前 10100 条数据
          (每个分片需要排序并保留前10100条)
各分片   → 返回 10100 × 3 = 30300 条数据到协调节点
协调节点 → 汇总后再次排序，取出第10001~10100条
```

> **关键**：ES 必须在每个分片中取出**前 from+size 条数据**，汇总到 Heap 中再进行**二次排序**。from 越大，内存压力越大。频繁深分页容易 OOM，甚至触发 FullGC。

**max_result_window** 保护机制：默认值 **10000**，即 from+size 不能超过 10000。

```json
# 超出限制的报错
{
  "error": {
    "root_cause": [{
      "type": "illegal_argument_exception",
      "reason": "Result window is too large, from + size must be less than or equal to: [10000]"
    }]
  }
}
```

**可以调大，但不建议**：

```json
PUT /employee/_settings
{ "index.max_result_window": 20000 }
```

### 1.2 Scroll 滚动查询（ES7 后不推荐）

Scroll 相当于对索引做**快照**，之后扫描遍历这个快照：

```json
# 1. 首次查询，scroll=5m 保持快照5分钟
GET /employee/_search?scroll=5m
{
  "query": { "match_all": {} },
  "size": 100
}

# 2. 滚动获取下一页（用返回的 _scroll_id）
GET /_search/scroll
{
  "scroll": "5m",
  "scroll_id": "FGluY2x1ZGVf..."
}

# 3. 用完清除 scroll（释放资源）
DELETE /_search/scroll
{ "scroll_id": "FGluY2x1ZGVf..." }
```

| Scroll 的优缺点 |
|---|
| ✅ 适合全量遍历（索引迁移、数据导出） |
| ❌ 非实时（快照机制，不反映后续变更） |
| ❌ 上下文需占用堆内存 |
| ❌ 不适合 C 端实时搜索 |

### 1.3 search_after（ES 7+ 推荐）

`search_after` 以前一页最后一条结果的排序值作为"锚点"，高效检索下一页：

```json
# 第1页
GET /employee/_search
{
  "size": 5,
  "query": { "match_all": {} },
  "sort": [
    { "age": "asc" },
    { "_id": "asc" }
  ]
}

# 第2页：传入上一页最后一条的 sort 值
GET /employee/_search
{
  "size": 5,
  "query": { "match_all": {} },
  "search_after": [32, "6"],    # ← 上一页最后一组 sort 值
  "sort": [
    { "age": "asc" },
    { "_id": "asc" }
  ]
}
```

**要求**：
- `sort` 字段取值必须**唯一**（否则定位不准）
- 一般用 `_id` 作为最后的 `sort` 字段做保障

### 1.4 Point In Time (PIT) + search_after

PIT 是 ES 7.10+ 引入的轻量级视图：

```json
# 1. 创建 PIT
POST /employee/_pit?keep_alive=5m
# 返回：{"id": "46ToAwMDaWR..."}

# 2. 基于 PIT 查询（不指定 index，用 pit.id）
GET /_search
{
  "size": 10,
  "query": { "match_all": {} },
  "pit": {
    "id": "46ToAwMDaWR...",
    "keep_alive": "1m"
  },
  "sort": [{"age": "asc"}, {"_id": "asc"}],
  "search_after": [22, "4"]
}

# 3. 删除 PIT
DELETE /_pit
{ "id": "46ToAwMDaWR..." }
```

### 1.5 四种分页方案对比

| 方案 | 实时性 | 深度分页 | 资源消耗 | 推荐场景 |
|------|--------|---------|---------|---------|
| **from+size** | ✅ 实时 | ❌ from+size<10000 | 中等 | 小数据量、Top N 查询 |
| **Scroll** | ❌ 非实时 | ✅ 全量遍历 | 高（占用 scroll 上下文） | 数据导出、索引重建 |
| **search_after** | ✅ 实时 | ✅ 深度分页 | 低 | C 端产品、列表翻页 |
| **PIT+search_after** | ✅ 实时 | ✅ 深度分页 | 低 | 需要一致性视图的 C 端产品 |

> **最佳实践**：C 端业务用 `search_after` + PIT，不提供"跳到第 N 页"功能（主流搜索引擎也是这样做的）。

---

## 二、分词与 Analyzer

### 2.1 Analyzer 的三部分

```
┌───────────────────────────────────────────┐
│               Analyzer                     │
├─────────────┬───────────────┬──────────────┤
│ Character   │    Tokenizer  │ Token Filters│
│  Filters    │    (分词器)    │  (词项过滤器) │
│ (字符过滤器) │               │              │
└─────────────┴───────────────┴──────────────┘
```

| 组件 | 作用 | 示例 |
|------|------|------|
| **Character Filters** | 字符预处理（转义、替换） | HTML 标签去除、`&`→`and` |
| **Tokenizer** | 按规则切分词汇 | standard、whitespace、ik_max_word |
| **Token Filters** | 对切分后的词再处理 | 小写转换、同义词、停用词移除 |

### 2.2 自定义 Analyzer

```json
PUT /test_index
{
  "settings": {
    "analysis": {
      "analyzer": {
        "my_custom_analyzer": {
          "type": "custom",
          "char_filter": ["html_strip"],
          "tokenizer": "standard",
          "filter": ["lowercase", "asciifolding"]
        }
      }
    }
  }
}

# 测试自定义分词器
POST /test_index/_analyze
{
  "analyzer": "my_custom_analyzer",
  "text": "Is this <b>déjà vu</b>?"
}
```

### 2.3 常见分词器速查

| 分词器 | 特点 | 适用场景 |
|--------|------|---------|
| `standard` | 按单词拆分 + 小写 | 英文通用 |
| `whitespace` | 按空白字符拆分 | 特殊格式 |
| `keyword` | **不分词**，整体作为一个词 | ID、邮箱 |
| `ik_max_word` | 中文最细粒度拆分 | 写入（最大化召回） |
| `ik_smart` | 中文智能拆分 | 搜索（更高精度） |

---

## 三、集群管理与性能调优

### 3.1 集群健康状态

```
Green:  所有 primary shard + replica shard 都已分配
Yellow: 所有 primary shard 已分配，部分 replica 未分配（ES 仍可工作）
Red:    部分 primary shard 未分配，部分数据丢失
```

```json
GET /_cluster/health
GET /_cluster/health?level=indices
GET /_cluster/health/employee
```

### 3.2 索引生命周期管理（ILM）

热-温-冷-删除四阶段分层管理：

```json
# 定义 Policy
PUT /_ilm/policy/logs_policy
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": { "max_size": "50GB", "max_age": "7d" }
        }
      },
      "warm": {
        "min_age": "7d",
        "actions": {
          "shrink": { "number_of_shards": 1 },
          "forcemerge": { "max_num_segments": 1 }
        }
      },
      "cold": {
        "min_age": "30d",
        "actions": {}
      },
      "delete": {
        "min_age": "90d",
        "actions": { "delete": {} }
      }
    }
  }
}
```

### 3.3 性能调优要点

**1. 索引设计**
- 分片数（number_of_shards）：创建后不可改，预分配充足（每个 shard 建议 10-50GB）
- 副本数（number_of_replicas）：可动态调整，读多时可增加

**2. 刷新间隔**
```json
PUT /my_index/_settings
{ "refresh_interval": "30s" }   # 默认1s，写入密集场景适当延长
```

**3. 合并策略**
```bash
# 手动触发 force merge（低峰期、只读索引）
POST /my_index/_forcemerge?max_num_segments=1
```

**4. Mapping 优化**
- 禁用不需要索引的字段：`"index": false`
- 用 `keyword` 替代 `text`（不需要分词时）
- 避免过多的字段和嵌套结构

**5. 查询优化**
- Filter Context 优先于 Query Context
- 避免 `*` 开头的通配符查询
- 使用 `search_after` 替代深度 `from+size`
- 聚合查询中减小 `size` 参数

---

## 四、SpringBoot 整合 ES 8

### 4.1 Maven 依赖（注意版本对应）

```xml
<!-- ES 8.x 对应 spring-data-elasticsearch 5.x -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-elasticsearch</artifactId>
</dependency>
```

> ⚠️ **版本兼容性**：必须确保 ES 服务端版本、Elasticsearch Client 版本、Spring Data Elasticsearch 版本三者匹配。

### 4.2 配置连接

```yaml
# application.yml
spring:
  elasticsearch:
    uris: http://192.168.65.47:9200
    username: elastic       # 安全认证（生产必开）
    password: yourpassword
    connection-timeout: 3s
    socket-timeout: 60s
```

### 4.3 实体类定义

```java
@Document(indexName = "employee")
public class Employee {
    @Id
    private String id;

    @Field(type = FieldType.Keyword)
    private String name;

    @Field(type = FieldType.Integer)
    private Integer sex;

    @Field(type = FieldType.Integer)
    private Integer age;

    @Field(type = FieldType.Text, analyzer = "ik_max_word")
    private String address;

    @Field(type = FieldType.Text, analyzer = "ik_smart",
           searchAnalyzer = "ik_smart")
    private String remark;

    // getters/setters...
}
```

### 4.4 Repository 查询

```java
@Repository
public interface EmployeeRepository extends ElasticsearchRepository<Employee, String> {

    // 方法名自动解析查询
    List<Employee> findByName(String name);

    // 精确匹配
    List<Employee> findBySex(Integer sex);

    // 全文检索（match）
    @Query("{\"match\": {\"remark\": \"?0\"}}")
    List<Employee> findByRemark(String keyword);

    // Bool 查询 + Filter
    @Query("{\"bool\": {\"must\": [{\"match\": {\"remark\": \"?0\"}}], " +
           "\"filter\": [{\"range\": {\"age\": {\"gte\": ?1, \"lte\": ?2}}}]}}")
    List<Employee> findByRemarkAndAgeBetween(
            String keyword, Integer minAge, Integer maxAge);
}
```

### 4.5 ES 8.x 新版客户端（ElasticsearchClient）

ES 8.x 推荐使用新的 `ElasticsearchClient`（基于 Jackson，非 RestHighLevelClient）：

```java
@Configuration
public class ESConfig {
    @Bean
    public ElasticsearchClient elasticsearchClient() {
        RestClient restClient = RestClient.builder(
            new HttpHost("192.168.65.47", 9200)
        ).build();

        ElasticsearchTransport transport = new RestClientTransport(
            restClient, new JacksonJsonpMapper()
        );

        return new ElasticsearchClient(transport);
    }
}
```

---

## 五、数据写入与一致性

### 5.1 写入流程

```
Client → 协调节点 → 计算路由 Hash(_id) % shard_count → 找到 Primary Shard
                                                              ↓
                                                  写入 Primary Shard + Translog
                                                              ↓
                                               同步到所有 Replica Shards
                                                              ↓
                                                    返回 Client 成功
```

### 5.2 Refresh、Flush、Translog

| 操作 | 频率 | 作用 |
|------|------|------|
| **Refresh** | 默认 1s | 将 Buffer 写入 Segment，**数据可被搜索** |
| **Flush** | 默认 Translog ≥512MB 或 30min | 执行 Refresh + 将 Segment fsync 到磁盘 + 清空 Translog |
| **Translog** | 每次写入同步 | Write-ahead Log，保证操作不丢失（类似 MySQL Redo Log） |

```
写入请求
  ↓
[ 内存 Buffer ] ← 写入立即进 buffer
  ↓ (refresh, 默认每1秒)
[ Segment (内存中可搜索，未持久化) ]
  ↓ (flush)
[ Segment (磁盘持久化) ] + [ Translog 清空 ]
```

### 5.3 数据一致性保障

- **Translog**：写入操作先记录到 Translog，若节点崩溃，可从 Translog 恢复
- **副本同步**：Primary → Replica 同步完成后才返回成功（可配置 `wait_for_active_shards`）
- **Seq No / Primary Term**：乐观锁并发控制（同前面的 `if_seq_no` + `if_primary_term`）

---

## 六、总结

| 维度 | 要点 |
|------|------|
| 深度分页 | from+size(≤10000) → search_after(生产推荐) → PIT(一致性视图) → Scroll(全量导出) |
| 分词器 | Analyzer = CharFilter + Tokenizer + TokenFilter；写入用 ik_max_word，搜索用 ik_smart |
| 集群 | Green/Yellow/Red 三态；ILM 热-温-冷-删除生命周期 |
| 调优 | 控制分片大小、延长 refresh_interval、forcemerge、Filter 优先 |
| SpringBoot | Entity + Repository 快速开发；ES8 推荐 ElasticsearchClient |
| 一致性 | Translog 防丢 + 副本同步 + SeqNo 乐观锁 |
