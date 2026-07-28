---
layout: post
title: "ElasticSearch自定义分词需求实战：中文分词、停用词、同义词全解析"
date: 2022-06-23
categories: [distributed]
tags: [ElasticSearch, 分词器, 自定义分词, IK分词, 停用词, 同义词]
comments: true
---

> 分词是构建倒排索引的重要一环。当标准分词器无法满足业务需求时，需要自定义分词器。

---

## 一、什么是分词

### 分词概念

分词（Tokenization）将一段文本拆分成一系列独立的词条（Token）。

**英文分词**：天然以空格/标点分隔
```
"you cannot use from and size" 
→ you / cannot / use / from / and / size
```

**中文分词**：字词间无分隔符，分词结果直接影响搜索质量
```
"杭州市长春药店"
→ 杭州 / 市长 / 春药 / 店           (错误!)
→ 杭州市 / 长春 / 药店               (正确!)
```

### ES 分词三阶段

```
Character Filter (字符过滤器)
    ↓ 预处理文本（去除HTML标签、特殊字符转换等）
Tokenizer (分词器) 
    ↓ 将文本切分为词条
Token Filter (词项过滤器)
    ↓ 对词条做进一步处理（小写转换、停用词过滤、同义词处理等）
```

### 查看分词效果

```bash
GET _analyze
{
  "analyzer": "ik_max_word",
  "text": "昨天，小明和他的朋友们去了市中心的图书馆"
}
```

返回：
```json
{
  "tokens": [
    { "token": "昨天", "start_offset": 0, "end_offset": 2, "type": "CN_WORD", "position": 0 },
    { "token": "小明", "start_offset": 3, "end_offset": 5, "type": "CN_WORD", "position": 1 },
    { "token": "和他", "start_offset": 5, "end_offset": 7, "type": "CN_WORD", "position": 2 },
    { "token": "朋友们", "start_offset": 8, "end_offset": 11, "position": 4 },
    { "token": "市中心", "start_offset": 13, "end_offset": 16, "position": 7 },
    { "token": "图书馆", "start_offset": 18, "end_offset": 21, "position": 9 }
  ]
}
```

---

## 二、为什么需要分词

| 维度 | 原因 |
|------|------|
| **语义维度** | 单字表达不了语义，词能表达。分词是语义分析的基础 |
| **存储维度** | 按单字索引需要大量倒排记录；按词索引大幅减少 |
| **时间维度** | 通过倒排索引，以 O(1) 时间复杂度通过词组定位文章 |

**示例**：“深入浅出Elasticsearch”
- 按"深"索引 → 无数条记录
- 按"深入"索引 → 少一些
- 按"深入浅出"索引 → 极少
- 按全名索引 → 精确匹配

> **Mapping 设计原则**：不需要分词的字段设为 `keyword`；需要分词的字段设为 `text` 并指定分词器。

---

## 三、ES 内置分词器

| 分词器 | 特点 | 适用场景 |
|--------|------|----------|
| `standard` | 默认分词器，按词切分 + 小写 | 英文 |
| `simple` | 非字母字符分割 + 小写 | 简单英文 |
| `whitespace` | 按空格切分 | |
| `keyword` | 不分词，整体作为单个词条 | 精确匹配 |
| `pattern` | 正则表达式切分 | 自定义规则 |
| `ik_max_word` | 最细粒度中文分词 | 中文索引 |
| `ik_smart` | 智能最简中文分词 | 中文搜索 |
| `pinyin` | 拼音分词 | 拼音搜索 |

---

## 四、自定义分词器配置

### 分词器组成

```json
PUT /my_index
{
  "settings": {
    "analysis": {
      "char_filter": {
        // 字符过滤器定义
      },
      "tokenizer": {
        // 分词器定义
      },
      "filter": {
        // 词项过滤器定义
      },
      "analyzer": {
        "my_custom_analyzer": {
          "type": "custom",
          "char_filter": ["html_strip"],
          "tokenizer": "ik_max_word",
          "filter": ["lowercase", "stop"]
        }
      }
    }
  }
}
```

### 实战：自定义分词器

```json
PUT /my_analyzer_test
{
  "settings": {
    "analysis": {
      "analyzer": {
        "my_ik_analyzer": {
          "type": "custom",
          "tokenizer": "ik_max_word",
          "filter": ["lowercase"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "content": {
        "type": "text",
        "analyzer": "my_ik_analyzer"
      }
    }
  }
}
```

---

## 五、IK 分词器自定义词库

### 扩展热词

有些专业词汇需要专门加入词库。修改 IK 配置目录下的文件：

**配置自定义词典**（`IKAnalyzer.cfg.xml`）：
```xml
<properties>
    <comment>IK Analyzer 扩展配置</comment>
    <entry key="ext_dict">custom/mydict.dic</entry>
    <entry key="ext_stopwords">custom/mystop.dic</entry>
</properties>
```

**添加自定义词**（`custom/mydict.dic`）：
```
王者荣耀
吃鸡
白嫖
内卷
躺平
```

**远程词库**（支持热更新）：
```xml
<entry key="remote_ext_dict">http://192.168.1.100/es_dict/mydict.dic</entry>
```

### 停用词

停用词（Stop Words）是搜索时应该忽略的词汇：

**`custom/mystop.dic`**：
```
的
了
是
在
和
也
就
都
```

---

## 六、同义词

### 同义词定义

让用户搜索"电脑"时也能匹配"计算机"。

```json
PUT /synonym_test
{
  "settings": {
    "analysis": {
      "filter": {
        "my_synonym_filter": {
          "type": "synonym",
          "synonyms": [
            "电脑, 计算机, PC",
            "手机, 移动电话, 电话",
            "ES, Elasticsearch, elastic"
          ]
        }
      },
      "analyzer": {
        "my_synonym_analyzer": {
          "type": "custom",
          "tokenizer": "ik_max_word",
          "filter": ["my_synonym_filter"]
        }
      }
    }
  }
}
```

### 同义词文件方式

```json
"my_synonym_filter": {
  "type": "synonym",
  "synonyms_path": "analysis/synonym.txt"
}
```

---

## 七、拼音分词器

### 安装

```bash
bin/elasticsearch-plugin install https://get.infini.cloud/elasticsearch/analysis-pinyin/8.14.3
```

### 配置

```json
PUT /pinyin_test
{
  "settings": {
    "analysis": {
      "analyzer": {
        "pinyin_analyzer": {
          "tokenizer": "pinyin",
          "filter": ["lowercase"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "name": {
        "type": "text",
        "fields": {
          "keyword": { "type": "keyword" },
          "pinyin": { "type": "text", "analyzer": "pinyin_analyzer" }
        }
      }
    }
  }
}
```

搜索示例：
```bash
GET /pinyin_test/_search
{
  "query": {
    "match": { "name.pinyin": "wangzherongyao" }
  }
}
```

---

## 八、分词策略建议

| 场景 | 推荐策略 |
|------|----------|
| 中文搜索 | `ik_max_word` 索引 + `ik_smart` 搜索 |
| 精确匹配 | 不分词（`keyword` 类型） |
| 专业术语 | 自定义 IK 词典 |
| 错别字/谐音 | 同义词配置 |
| 拼音搜索 | pinyin 分词器 |

```
设计目标：召回率 + 精确率 平衡

  召回率高 → ik_max_word（多分词）→ 多返回结果
  精确率高 → ik_smart（少分词）→ 精确匹配
  两者平衡 → 索引用 max_word，搜索用 smart
```

> 有道云笔记：[ES自定义分词需求实战](https://note.youdao.com/s/WH8kgRmM)
