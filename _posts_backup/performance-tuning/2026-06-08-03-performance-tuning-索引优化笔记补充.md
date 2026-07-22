---
title: "索引优化笔记补充"
description: "【有道云笔记】https://note.youdao.com/s/T2FZ3b0M 关于《Mysql索引优化实战一》中课上示例是基于Mysql5.7的。mysql8也同样适用,有区别会在本文档 中进行记录 示例表 如果示例脚本执行失败,可以使用下面的脚本 1 -- 删除已存在的 insert_emp 存储过程(如果存在的话) 2 DROP PROCEDURE IF EXISTS insert..."
author: hsc
date: 2026-06-08 00:00:00 +0800
categories: ['Java 后端', '性能调优']
tags: ['性能调优', 'JVM', 'MySQL', 'Tomcat', 'GC']
toc: true
---

> 本文整理自《一、性能调优专题》课程笔记，共 3 页。

【有道云笔记】https://note.youdao.com/s/T2FZ3b0M
关于《Mysql索引优化实战一》中课上示例是基于Mysql5.7的。mysql8也同样适用,有区别会在本文档
中进行记录
示例表
如果示例脚本执行失败,可以使用下面的脚本
1 -- 删除已存在的 insert_emp 存储过程(如果存在的话)
2 DROP PROCEDURE IF EXISTS insert_emp;
3
4 -- 修改语句结束符为 ;;
5 DELIMITER ;;
6
7 -- 创建 insert_emp 存储过程
8 CREATE PROCEDURE insert_emp()
9 BEGIN
10 DECLARE i INT DEFAULT 1;
11 WHILE i <= 100000 DO
12 INSERT INTO employees(name, age, position) VALUES(CONCAT('zhuge', i), i, 'dev');
13 SET i = i + 1;
14 END WHILE;
15 END;;
16
17 -- 恢复语句结束符为 ;
18 DELIMITER ;
19
20 -- 调用 insert_emp 存储过程
21 CALL insert_emp();
举一个大家不容易理解的综合例子:
4、in和or在表数据量比较大的情况会走索引,在表记录不多的情况下会选择全表扫描
mysql5.7

mysql 8
mysql8中in和or在表记录不多的情况下也会走索引。
Order by与Group by优化
Mysql8降序索引示例
Case 7:
mysql8

filesort文件排序方式
MySQL8中max_length_for_sort_data默认4096字节
