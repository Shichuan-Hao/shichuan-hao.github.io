---


title: "索引优化笔记补充"
description: "Join 关联查询优化如果脚本中的存储过程抛出语法错误"
author: hsc
date: 2020-08-27 00:00:00 +0800
categories: [Java, 性能调优]
tags: ['性能调优', 'MySQL', 'MySQL优化']
toc: true


---

Join 关联查询优化如果脚本中的存储过程抛出语法错误,使用下面的脚本 1 -- 示例表:
2 CREATE TABLE `t1` (3 `id` int(11) NOT NULL AUTO_INCREMENT,4 `a` int(11) DEFAULT NULL,5 `b` int(11) DEFAULT NULL,6 PRIMARY KEY (`id`),7 KEY `idx_a` (`a`)
8 ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
910 create table t2 like t1;
1112 -- 插入一些示例数据 13 -- 往 t1 表插入 1 万行记录 14 DROP PROCEDURE IF EXISTS insert_t1;
15 DELIMITER ;;
16 CREATE PROCEDURE insert_t1()
17 BEGIN18 DECLARE i INT DEFAULT 1;
19 WHILE i <= 10000 DO20 INSERT INTO t1(a, b) VALUES(i, i);
21 SET i = i + 1;
22 END WHILE;
23 END;;
24 DELIMITER ;
25 CALL insert_t1();
2627 -- 往 t2 表插入 100 行记录 28 DROP PROCEDURE IF EXISTS insert_t2;
29 DELIMITER ;;
30 CREATE PROCEDURE insert_t2()
31 BEGIN

32 DECLARE i INT;
33 SET i = 1;
34 WHILE i <= 100 DO35 INSERT INTO t2(a, b) VALUES(i, i);
36 SET i = i + 1;
37 END WHILE;
38 END;;
39 DELIMITER ;
40 CALL insert_t2();
