---


title: "索引优化笔记补充"
description: "关于《Mysql 索引优化实战一》中课上示例是基于 Mysql5.7 的。"
author: hsc
date: 2020-08-04 00:00:00 +0800
categories: [Java, 性能调优]
tags: ['性能调优', 'MySQL', 'MySQL优化', '索引优化']
toc: true


---

关于《Mysql 索引优化实战一》中课上示例是基于 Mysql5.7 的。 mysql8 也同样适用,有区别会在本文档中进行记录示例表如果示例脚本执行失败,可以使用下面的脚本 1 -- 删除已存在的 insert_emp 存储过程(如果存在的话)
2 DROP PROCEDURE IF EXISTS insert_emp;
34 -- 修改语句结束符为 ;;
5 DELIMITER ;;
67 -- 创建 insert_emp 存储过程 8 CREATE PROCEDURE insert_emp()
9 BEGIN10 DECLARE i INT DEFAULT 1;
11 WHILE i <= 100000 DO12 INSERT INTO employees(name, age, position) VALUES(CONCAT('zhuge', i), i, 'dev');
13 SET i = i + 1;
14 END WHILE;
15 END;;
1617 -- 恢复语句结束符为 ;
18 DELIMITER ;
1920 -- 调用 insert_emp 存储过程 21 CALL insert_emp();
举一个大家不容易理解的综合例子:
4、in 和 or 在表数据量比较大的情况会走索引,在表记录不多的情况下会选择全表扫描 mysql5.7

mysql 8mysql8 中 in 和 or 在表记录不多的情况下也会走索引。
Order by 与 Group by 优化 Mysql8 降序索引示例 Case 7:
mysql8

filesort 文件排序方式 MySQL8 中 max_length_for_sort_data 默认 4096 字节
