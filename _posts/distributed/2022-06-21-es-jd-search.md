---
layout: post
title: "仿京东商品搜索实战：ES电商搜索全流程开发"
date: 2022-06-21
categories: [distributed]
tags: [ElasticSearch, 电商搜索, 商品检索, 过滤筛选, 排序, nested]
comments: true
---

> 从零构建一个仿京东的商品搜索服务，涵盖文档建模、多字段搜索、属性筛选、价格区间、排序、高亮。

---

## 一、业务需求分析

**核心搜索功能**：
- 根据关键字搜索
- 根据品牌、商品类别、属性信息筛选
- 价格区间筛选
- 是否有库存
- 按销量、价格、上架时间排序

**商品 JSON 文档示例**：

```json
{
  "id": "26",
  "name": "小米 11 手机",
  "keywords": "小米手机",
  "subTitle": "AI智慧全面屏 6GB+64GB 全网通",
  "price": 3999,
  "promotionPrice": 2999,
  "originalPrice": 5999,
  "pic": "http://...",
  "sale": 999,
  "hasStock": true,
  "salecount": 999,
  "putawayDate": "2021-04-01",
  "brandId": 6,
  "brandName": "小米",
  "brandImg": "http://...",
  "categoryId": 19,
  "categoryName": "手机通讯",
  "attrs": [
    { "attrId": 1, "attrName": "cpu", "attrValue": "2核" },
    { "attrId": 2, "attrName": "颜色", "attrValue": "黑色" }
  ]
}
```

---

## 二、Mapping 设计

### 建模分析

| 字段 | 类型 | 分析器 | 原因 |
|------|------|--------|------|
| `name` | text | ik_max_word | 商品名全文搜索 |
| `keywords` | text | ik_max_word | 搜索关键词匹配 |
| `subTitle` | text | ik_max_word | 副标题搜索 |
| `brandName` | keyword | — | 精确筛选 |
| `categoryName` | keyword | — | 精确筛选 |
| `price` | long | — | 价格范围筛选 |
| `hasStock` | boolean | — | 库存筛选 |
| `salecount` | long | — | 排序 |
| `putawayDate` | date | — | 排序 |
| `attrs` | nested | — | **关联属性，独立查询** |

### 为什么 attrs 要用 nested？

如果使用 Object 类型，ES 内部会扁平化：
```
attrs.attrName:  ["cpu", "颜色"]
attrs.attrValue: ["2核", "黑色"]
```
搜索 `cpu=黑色` 会错误被匹配！

**Nested 类型**保持子对象独立关联。

### 创建索引

```json
PUT product_db
{
  "mappings": {
    "properties": {
      "id": { "type": "long" },
      "name": { "type": "text", "analyzer": "ik_max_word" },
      "keywords": { "type": "text", "analyzer": "ik_max_word" },
      "subTitle": { "type": "text", "analyzer": "ik_max_word" },
      "price": { "type": "long" },
      "promotionPrice": { "type": "long" },
      "originalPrice": { "type": "long" },
      "sale": { "type": "long" },
      "hasStock": { "type": "boolean" },
      "salecount": { "type": "long" },
      "putawayDate": { "type": "date" },
      "brandId": { "type": "long" },
      "brandName": { "type": "keyword" },
      "categoryId": { "type": "long" },
      "categoryName": { "type": "keyword" },
      "attrs": {
        "type": "nested",
        "properties": {
          "attrId": { "type": "long" },
          "attrName": { "type": "keyword" },
          "attrValue": { "type": "keyword" }
        }
      }
    }
  }
}
```

---

## 三、商品搜索 DSL 实战

### 1、关键字搜索

```json
GET /product_db/_search
{
  "query": {
    "multi_match": {
      "query": "小米手机",
      "fields": ["name^3", "keywords^2", "subTitle"]
    }
  }
}
```

### 2、按品牌/分类筛选

```json
{
  "query": {
    "bool": {
      "must": [
        { "multi_match": { "query": "手机", "fields": ["name^3", "keywords"] } }
      ],
      "filter": [
        { "term": { "brandName": "小米" } },
        { "term": { "categoryName": "手机通讯" } }
      ]
    }
  }
}
```

### 3、价格区间筛选

```json
{
  "query": {
    "bool": {
      "must": [...],
      "filter": [
        { "range": { "price": { "gte": 1000, "lte": 5000 } } }
      ]
    }
  }
}
```

### 4、商品属性筛选（nested）

```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "name": "手机" } }
      ],
      "filter": [
        {
          "nested": {
            "path": "attrs",
            "query": {
              "bool": {
                "must": [
                  { "term": { "attrs.attrName": "颜色" } },
                  { "term": { "attrs.attrValue": "黑色" } }
                ]
              }
            }
          }
        }
      ]
    }
  }
}
```

### 5、库存筛选

```json
{ "term": { "hasStock": true } }
```

### 6、完整搜索 DSL

```json
GET /product_db/_search
{
  "query": {
    "bool": {
      "must": [
        { "multi_match": { "query": "小米", "fields": ["name^3", "keywords^2"] } }
      ],
      "filter": [
        { "term": { "brandName": "小米" } },
        { "term": { "hasStock": true } },
        { "range": { "price": { "gte": 1000, "lte": 5000 } } },
        {
          "nested": {
            "path": "attrs",
            "query": {
              "bool": {
                "must": [
                  { "term": { "attrs.attrName": "颜色" } },
                  { "term": { "attrs.attrValue": "黑色" } }
                ]
              }
            }
          }
        }
      ]
    }
  },
  "sort": [
    { "salecount": { "order": "desc" } },
    { "price": { "order": "asc" } },
    { "putawayDate": { "order": "desc" } }
  ],
  "from": 0,
  "size": 20,
  "highlight": {
    "fields": {
      "name": {},
      "keywords": {}
    }
  }
}
```

---

## 四、SpringBoot 实现电商搜索

### Service 层

```java
@Service
public class ProductSearchService {
    
    @Autowired
    private ElasticsearchTemplate template;
    
    public SearchResult search(ProductSearchParam param) {
        // 构建 bool query
        BoolQuery.Builder boolBuilder = new BoolQuery.Builder();
        
        // 关键字搜索（must，参与评分）
        if (StringUtils.hasText(param.getKeyword())) {
            boolBuilder.must(m -> m.multiMatch(mm -> mm
                .query(param.getKeyword())
                .fields("name^3", "keywords^2", "subTitle")
            ));
        } else {
            boolBuilder.must(m -> m.matchAll(ma -> ma));
        }
        
        // 品牌筛选（filter，不参与评分）
        if (param.getBrandId() != null) {
            boolBuilder.filter(f -> f.term(t -> t.field("brandId").value(param.getBrandId())));
        }
        
        // 分类筛选
        if (StringUtils.hasText(param.getCategoryName())) {
            boolBuilder.filter(f -> f.term(t -> t.field("categoryName").value(param.getCategoryName())));
        }
        
        // 价格区间
        if (param.getMinPrice() != null || param.getMaxPrice() != null) {
            boolBuilder.filter(f -> f.range(r -> {
                r.field("price");
                if (param.getMinPrice() != null) r.gte(JsonData.of(param.getMinPrice()));
                if (param.getMaxPrice() != null) r.lte(JsonData.of(param.getMaxPrice()));
                return r;
            }));
        }
        
        // 库存
        if (param.getHasStock() != null) {
            boolBuilder.filter(f -> f.term(t -> t.field("hasStock").value(param.getHasStock())));
        }
        
        NativeQuery query = NativeQuery.builder()
            .withQuery(q -> q.bool(boolBuilder.build()))
            .withPageable(PageRequest.of(param.getPage(), param.getSize()))
            .build();
        
        return template.search(query, Product.class);
    }
}
```

### 参数对象

```java
@Data
public class ProductSearchParam {
    private String keyword;        // 搜索关键字
    private Long brandId;          // 品牌ID
    private String categoryName;   // 分类名称
    private Integer minPrice;      // 最低价
    private Integer maxPrice;      // 最高价
    private Boolean hasStock;      // 是否有货
    private Integer page = 0;
    private Integer size = 20;
    private String sortField;      // 排序字段
    private String sortOrder;      // asc/desc
}
```

---

## 五、搜索优化建议

### 权重配置

```json
// 标题权重最高 → 关键词权重 → 副标题权重
"fields": ["name^3", "keywords^2", "subTitle^1"]
```

### 高亮返回

```json
"highlight": {
  "fields": {
    "name": { "fragment_size": 50, "number_of_fragments": 1 },
    "keywords": {}
  },
  "pre_tags": ["<span style='color:red'>"],
  "post_tags": ["</span>"]
}
```

### 多级排序

```json
"sort": [
  { "salecount": "desc" },      // 首先按销量
  { "_score": "desc" },         // 同销量按相关性
  { "price": "asc" }            // 同相关性按价格（低价优先）
]
```

---

## 六、总结

```
商品搜索完整流程：

  用户输入关键字
       ↓
  multi_match 多字段搜索（name^3 / keywords^2）
       ↓
  filter 精确筛选（品牌/分类/价格/库存/属性）
       ↓
  sort 排序（销量/价格/上架时间/相关性）
       ↓
  highlight 高亮返回
       ↓
  分页返回结果
```

> 有道云笔记：[仿京东商品搜索实战](https://note.youdao.com/s/Tj3txf8r)
