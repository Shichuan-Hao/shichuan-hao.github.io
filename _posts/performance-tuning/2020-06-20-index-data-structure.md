---



title: "索引底层数据结构笔记补充"
description: "关于《深入理解 Mysql 索引底层数据结构与算法》这节课的笔记补充课程中联合索引案例使用的脚本 1 CREATE TABLE (2 int(11) NOT N"
author: hsc
date: 2020-06-20 00:00:00 +0800
categories: ['Java 后端', '性能调优']
tags: ['性能调优', 'MySQL', 'MySQL优化', '索引优化']
toc: true



---

关于《深入理解 Mysql 索引底层数据结构与算法》这节课的笔记补充课程中联合索引案例使用的脚本 1 CREATE TABLE `employees` (2 `id` int(11) NOT NULL AUTO_INCREMENT,3 `name` varchar(24) NOT NULL DEFAULT '' COMMENT '姓名',4 `age` int(11) NOT NULL DEFAULT '0' COMMENT '年龄',5 `position` varchar(20) NOT NULL DEFAULT '' COMMENT '职位',6 `hire_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入职时间',7 PRIMARY KEY (`id`),8 KEY `idx_name_age_position` (`name`,`age`,`position`) USING BTREE9 ) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8 COMMENT='员工记录表';
1011 INSERT INTO employees(name,age,position,hire_time) VALUES('LiLei',22,'manager',NOW());
12 INSERT INTO employees(name,age,position,hire_time) VALUES('HanMeimei', 23,'dev',NOW());
13 INSERT INTO employees(name,age,position,hire_time) VALUES('Lucy',23,'dev',NOW());
141516 EXPLAIN SELECT * FROM employees WHERE name = 'Bill' and age = 31;
17 EXPLAIN SELECT * FROM employees WHERE age = 30 AND position = 'dev';
18 EXPLAIN SELECT * FROM employees WHERE position = 'manager';
关于最左前缀的补充 MySQL 一定是遵循最左前缀匹配的,这句话在 mysql8 以前是正确的,没有任何毛病。但是在 MySQL8.0 中,就不一定了。
索引跳跃扫描(Index Skip Scan)
参考:https://dev.mysql.com/doc/refman/8.0/en/range-optimization.html#range-access-skip-scan 官网示例 1 CREATE TABLE t1 (f1 INT NOT NULL, f2 INT NOT NULL, PRIMARY KEY(f1, f2));
2 INSERT INTO t1 VALUES3 (1,1), (1,2), (1,3), (1,4), (1,5),4 (2,1), (2,2), (2,3), (2,4), (2,5);

5 INSERT INTO t1 SELECT f1, f2 + 5 FROM t1;
6 INSERT INTO t1 SELECT f1, f2 + 10 FROM t1;
7 INSERT INTO t1 SELECT f1, f2 + 20 FROM t1;
8 INSERT INTO t1 SELECT f1, f2 + 40 FROM t1;
9 ANALYZE TABLE t1;
1011 EXPLAIN SELECT f1, f2 FROM t1 WHERE f2 > 40;
虽然我们的 SQL 中,没有遵循最左前缀原则,只使用了 f2 作为查询条件,但是经过 MySQL 8.0 的优化以后,还是通过索引跳跃扫描的方式用到了索引了。
索引跳跃扫描优化原理 mysql8.013 后通过优化器帮我们加了联合索引,SQL 执行过程如下:
1. 获取 f1 字段第一个唯一值,也就是 f1 = 1
2. 构造 f1 = 1 and f2 > 40,进行范围查询
3. 获取 f1 字段第二个唯一值,也就是 f1 = 2
4. 构造 f1 = 2 and f2 > 40,进行范围查询 1 SELECT f1, f2 FROM t1 WHERE f2 > 40;
23 执行的最终 SQL:
4 SELECT f1, f2 FROM t1 WHERE f1 =1 and f2 > 405 UNION6 SELECT f1, f2 FROM t1 WHERE f1 =2 and f2 > 40;
7 所以对于对于 f1 值很少,区分度不高的情况索引跳跃扫描会快一些;反之查询效率慢些。
我们不能依赖这个优化,建立索引的时候,还是优先把区分度高的,查询频繁的字段放到联合索引的左边。
限制条件查询必须只能依赖一张表,不能多表 JOIN。
查询中不能使用 GROUP BY 或 DISTINCT 语句。
查询的字段必须是索引中的列。

组合索引形式:([A_1, ..., A_k,] B_1, ..., B_m, C [, D_1, ..., D_n]),A,D 可以为空,但是 B ,C 不能为空。
