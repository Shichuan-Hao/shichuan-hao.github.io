---
title: "Explain笔记补充"
description: "【有道云笔记】 https://note.youdao.com/s/FMi8YpR7 关于《Explain详解与索引最佳实践》中课上示例是基于Mysql5.7的。mysql8也同样适用,有区别会在 本文档中进行记录 查看mysql版本 Explain分析示例 参考资料: https://dev.mysql.com/doc/refman/8.0/en/explain-output.html 在..."
author: hsc
date: 2026-06-06 00:00:00 +0800
categories: ['Java 后端', '性能调优']
tags: ['性能调优', 'JVM', 'MySQL', 'Tomcat', 'GC']
toc: true
---

> 本文整理自《一、性能调优专题》课程笔记，共 3 页。

【有道云笔记】
https://note.youdao.com/s/FMi8YpR7
关于《Explain详解与索引最佳实践》中课上示例是基于Mysql5.7的。mysql8也同样适用,有区别会在
本文档中进行记录
查看mysql版本
Explain分析示例
参考资料: https://dev.mysql.com/doc/refman/8.0/en/explain-output.html
在mysql8.0以上已经废除了explain extended这条命令,我们只需要使用explain就可以了。
索引最佳实践
3.不在索引列上做任何操作(计算、函数、(自动or手动)类型转换),会导致索引失效而转向全表扫描
给hire_time增加一个普通索引:
ALTER TABLE `employees` ADD INDEX `idx_hire_time` (`hire_time`) USING BTREE ;
转化为日期范围查询,有可能会走索引:
EXPLAIN select * from employees where hire_time >='2018-09-30 00:00:00' and hire_time <='2018-09-30
23:59:59';
mysql8中测试结果

6.mysql在使用不等于(!=或者<>),not in ,not exists 的时候无法使用索引会导致全表扫描
< 小于、 > 大于、 <=、>= 这些,mysql内部优化器会根据检索比例、表大小等多个因素整体评估是否使用索引
EXPLAIN SELECT * FROM employees WHERE name != 'LiLei';
mysql5.7中测试结果
mysql8中测试结果
10.少用or或in,用它查询时,mysql不一定使用索引,mysql内部优化器会根据检索比例、表大小等多个因素整体评
估是否使用索引,详见范围查询优化
EXPLAIN SELECT * FROM employees WHERE name = 'LiLei' or name = 'HanMeimei';
mysql5.7中测试结果
mysql8中测试结果
11.范围查询优化
给年龄添加单值索引
ALTER TABLE `employees` ADD INDEX `idx_age` (`age`) USING BTREE ;
explain select * from employees where age >=1 and age <=2000;
mysql5.7中测试结果
m ysql8中测试结果
