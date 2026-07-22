---
title: "索引底层数据结构笔记补充"
description: "有道笔记地址: https://note.youdao.com/s/5yh3I3oO 关于《深入理解Mysql索引底层数据结构与算法》这节课的笔记补充 课程中联合索引案例使用的脚本 1 CREATE TABLE `employees` ( 2 `id` int(11) NOT NULL AUTO_INCREMENT, 3 `name` varchar(24) NOT NULL DEFAULT..."
author: hsc
date: 2016-07-08 00:00:00 +0800
categories: ['Java 后端', '性能调优']
tags: ['性能调优', 'JVM', 'MySQL', 'Tomcat', 'GC']
toc: true
---

> 本文整理自《一、性能调优专题》课程笔记，共 3 页。

有道笔记地址: https://note.youdao.com/s/5yh3I3oO
关于《深入理解Mysql索引底层数据结构与算法》这节课的笔记补充
课程中联合索引案例使用的脚本
1 CREATE TABLE `employees` (
2 `id` int(11) NOT NULL AUTO_INCREMENT,
3 `name` varchar(24) NOT NULL DEFAULT '' COMMENT '姓名',
4 `age` int(11) NOT NULL DEFAULT '0' COMMENT '年龄',
5 `position` varchar(20) NOT NULL DEFAULT '' COMMENT '职位',
6 `hire_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入职时间',
7 PRIMARY KEY (`id`),
8 KEY `idx_name_age_position` (`name`,`age`,`position`) USING BTREE
9 ) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8 COMMENT='员工记录表';
10
11 INSERT INTO employees(name,age,position,hire_time) VALUES('LiLei',22,'manager',NOW());
12 INSERT INTO employees(name,age,position,hire_time) VALUES('HanMeimei', 23,'dev',NOW());
13 INSERT INTO employees(name,age,position,hire_time) VALUES('Lucy',23,'dev',NOW());
14
15
16 EXPLAIN SELECT * FROM employees WHERE name = 'Bill' and age = 31;
17 EXPLAIN SELECT * FROM employees WHERE age = 30 AND position = 'dev';
18 EXPLAIN SELECT * FROM employees WHERE position = 'manager';
关于最左前缀的补充
MySQL一定是遵循最左前缀匹配的,这句话在mysql8以前是正确的,没有任何毛病。但是在MySQL
8.0中,就不一定了。
索引跳跃扫描(Index Skip Scan)
参考:https://dev.mysql.com/doc/refman/8.0/en/range-optimization.html#range-access-skip-scan
官网示例
1 CREATE TABLE t1 (f1 INT NOT NULL, f2 INT NOT NULL, PRIMARY KEY(f1, f2));
2 INSERT INTO t1 VALUES
3 (1,1), (1,2), (1,3), (1,4), (1,5),
4 (2,1), (2,2), (2,3), (2,4), (2,5);

5 INSERT INTO t1 SELECT f1, f2 + 5 FROM t1;
6 INSERT INTO t1 SELECT f1, f2 + 10 FROM t1;
7 INSERT INTO t1 SELECT f1, f2 + 20 FROM t1;
8 INSERT INTO t1 SELECT f1, f2 + 40 FROM t1;
9 ANALYZE TABLE t1;
10
11 EXPLAIN SELECT f1, f2 FROM t1 WHERE f2 > 40;
虽然我们的SQL中,没有遵循最左前缀原则,只使用了f2作为查询条件,但是经过MySQL 8.0的优化以
后,还是通过索引跳跃扫描的方式用到了索引了。
索引跳跃扫描优化原理
mysql8.013后通过优化器帮我们加了联合索引,SQL执行过程如下:
1. 获取 f1 字段第一个唯一值,也就是 f1 = 1
2. 构造 f1 = 1 and f2 > 40,进行范围查询
3. 获取 f1 字段第二个唯一值,也就是 f1 = 2
4. 构造 f1 = 2 and f2 > 40,进行范围查询
1 SELECT f1, f2 FROM t1 WHERE f2 > 40;
2
3 执行的最终SQL:
4 SELECT f1, f2 FROM t1 WHERE f1 =1 and f2 > 40
5 UNION
6 SELECT f1, f2 FROM t1 WHERE f1 =2 and f2 > 40;
7
所以对于对于f1值很少,区分度不高的情况索引跳跃扫描会快一些;反之查询效率慢些。
我们不能依赖这个优化,建立索引的时候,还是优先把区分度高的,查询频繁的字段放到联合索引的
左边。
限制条件
查询必须只能依赖一张表,不能多表JOIN。
查询中不能使用 GROUP BY 或 DISTINCT 语句。
查询的字段必须是索引中的列。

组合索引形式:([A_1, ..., A_k,] B_1, ..., B_m, C [, D_1, ..., D_n]),A,D 可以为空,但是B ,C 不能为空。
