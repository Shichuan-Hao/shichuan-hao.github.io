---
title: "-VIP-Explain详解与索引优化最佳实践"
description: "Mysql安装文档参考: 1 文档:02-Mysql5.7与8.0安装文档.note 2 链接:http://note.youdao.com/noteshare?id=e263c02782b7c3fc8a342c0ddae124e1&sub=40918B2FF3D94B74955F328BA20F Explain工具介绍 使用EXPLAIN关键字可以模拟优化器执行SQL语句,分析你的查询语句..."
author: hsc
date: 2026-06-05 00:00:00 +0800
categories: ['Java 后端', '性能调优']
tags: ['性能调优', 'JVM', 'MySQL', 'Tomcat', 'GC']
toc: true
---

> 本文整理自《一、性能调优专题》课程笔记，共 11 页。

Mysql安装文档参考:
1 文档:02-Mysql5.7与8.0安装文档.note
2 链接:http://note.youdao.com/noteshare?id=e263c02782b7c3fc8a342c0ddae124e1&sub=40918B2FF3D94B74955F328BA20F
Explain工具介绍
使用EXPLAIN关键字可以模拟优化器执行SQL语句,分析你的查询语句或是结构的性能瓶颈
在 select 语句之前增加 explain 关键字,MySQL 会在查询上设置一个标记,执行查询会返回执行计划的信息,而不是执
行这条SQL
注意:如果 from 中包含子查询,仍会执行该子查询,将结果放入临时表中
Explain分析示例
参考官方文档:https://dev.mysql.com/doc/refman/5.7/en/explain-output.html
11 示示例例表表::
22 DDRROOPP TTAABBLLEE IIFF EEXXIISSTTSS ``aaccttoorr``;;
33 CCRREEAATTEE TTAABBLLEE ``aaccttoorr`` ((
44 ``iidd`` iinntt((1111)) NNOOTT NNUULLLL,,
55 ``nnaammee`` vvaarrcchhaarr((4455)) DDEEFFAAUULLTT NNUULLLL,,
66 ``uuppddaattee__ttiimmee`` ddaatteettiimmee DDEEFFAAUULLTT NNUULLLL,,
77 PPRRIIMMAARRYY KKEEYY ((``iidd``))
88 )) EENNGGIINNEE==IInnnnooDDBB DDEEFFAAUULLTT CCHHAARRSSEETT==uuttff88;;
99
1100 IINNSSEERRTT IINNTTOO ``aaccttoorr`` ((``iidd``,, ``nnaammee``,, ``uuppddaattee__ttiimmee``)) VVAALLUUEESS ((11,,''aa'',,''22001177--1122--2222 1155::2277::1188'')),, ((22,,''bb'',,''22001177--1122--2222
1111
1122 DDRROOPP TTAABBLLEE IIFF EEXXIISSTTSS ``ffiillmm``;;
1133 CCRREEAATTEE TTAABBLLEE ``ffiillmm`` ((
1144 ``iidd`` iinntt((1111)) NNOOTT NNUULLLL AAUUTTOO__IINNCCRREEMMEENNTT,,
1155 ``nnaammee`` vvaarrcchhaarr((1100)) DDEEFFAAUULLTT NNUULLLL,,
1166 PPRRIIMMAARRYY KKEEYY ((``iidd``)),,
1177 KKEEYY ``iiddxx__nnaammee`` ((``nnaammee``))
1188 )) EENNGGIINNEE==IInnnnooDDBB DDEEFFAAUULLTT CCHHAARRSSEETT==uuttff88;;
1199
2200 IINNSSEERRTT IINNTTOO ``ffiillmm`` ((``iidd``,, ``nnaammee``)) VVAALLUUEESS ((33,,''ffiillmm00'')),,((11,,''ffiillmm11'')),,((22,,''ffiillmm22''));;
2211
2222 DDRROOPP TTAABBLLEE IIFF EEXXIISSTTSS ``ffiillmm__aaccttoorr``;;
2233 CCRREEAATTEE TTAABBLLEE ``ffiillmm__aaccttoorr`` ((
2244 ``iidd`` iinntt((1111)) NNOOTT NNUULLLL,,
2255 ``ffiillmm__iidd`` iinntt((1111)) NNOOTT NNUULLLL,,
2266 ``aaccttoorr__iidd`` iinntt((1111)) NNOOTT NNUULLLL,,
2277 ``rreemmaarrkk`` vvaarrcchhaarr((225555)) DDEEFFAAUULLTT NNUULLLL,,
2288 PPRRIIMMAARRYY KKEEYY ((``iidd``)),,
2299 KKEEYY ``iiddxx__ffiillmm__aaccttoorr__iidd`` ((``ffiillmm__iidd``,,``aaccttoorr__iidd``))
3300 )) EENNGGIINNEE==IInnnnooDDBB DDEEFFAAUULLTT CCHHAARRSSEETT==uuttff88;;
3311

3322 IINNSSEERRTT IINNTTOO ``ffiillmm__aaccttoorr`` ((``iidd``,, ``ffiillmm__iidd``,, ``aaccttoorr__iidd``)) VVAALLUUEESS ((11,,11,,11)),,((22,,11,,22)),,((33,,22,,11));;
11 mmyyssqqll>> eexxppllaaiinn sseelleecctt ** ffrroomm aaccttoorr;;
在查询中的每个表会输出一行,如果有两个表通过 join 连接查询,那么会输出两行。
explain 两个变种
1)explain extended:会在 explain 的基础上额外提供一些查询优化的信息。紧随其后通过 show warnings 命令可以
得到优化后的查询语句,从而看出优化器优化了什么。额外还有 filtered 列,是一个百分比的值,rows * filtered/100 可
以估算出将要和 explain 中前一个表进行连接的行数(前一个表指 explain 中的id值比当前表id值小的表)。
11 mmyyssqqll>> eexxppllaaiinn eexxtteennddeedd sseelleecctt ** ffrroomm ffiillmm wwhheerree iidd == 11;;
11 mmyyssqqll>> sshhooww wwaarrnniinnggss;;
2)explain partitions:相比 explain 多了个 partitions 字段,如果查询是基于分区表的话,会显示查询将访问的分
区。
explain中的列
接下来我们将展示 explain 中每个列的信息。
1. id列
id列的编号是 select 的序列号,有几个 select 就有几个id,并且id的顺序是按 select 出现的顺序增长的。
id列越大执行优先级越高,id相同则从上往下执行,id为NULL最后执行。
2. select_type列
select_type 表示对应行是简单还是复杂的查询。
1)simple:简单查询。查询不包含子查询和union
11 mmyyssqqll>> eexxppllaaiinn sseelleecctt ** ffrroomm ffiillmm wwhheerree iidd == 22;;
2)primary:复杂查询中最外层的 select
3)subquery:包含在 select 中的子查询(不在 from 子句中)
4)derived:包含在 from 子句中的子查询。MySQL会将结果存放在一个临时表中,也称为派生表(derived的英文含
义)
用这个例子来了解 primary、subquery 和 derived 类型

11 mmyyssqqll>> sseett sseessssiioonn ooppttiimmiizzeerr__sswwiittcchh==''ddeerriivveedd__mmeerrggee==ooffff'';; ##关关闭闭mmyyssqqll55..77新新特特性性对对衍衍生生表表的的合合并并优优化化
22 mmyyssqqll>> eexxppllaaiinn sseelleecctt ((sseelleecctt 11 ffrroomm aaccttoorr wwhheerree iidd == 11)) ffrroomm ((sseelleecctt ** ffrroomm ffiillmm wwhheerree iidd == 11)) ddeerr;;
11 mmyyssqqll>> sseett sseessssiioonn ooppttiimmiizzeerr__sswwiittcchh==''ddeerriivveedd__mmeerrggee==oonn'';; ##还还原原默默认认配配置置
5)union:在 union 中的第二个和随后的 select
11 mmyyssqqll>> eexxppllaaiinn sseelleecctt 11 uunniioonn aallll sseelleecctt 11;;
3. table列
这一列表示 explain 的一行正在访问哪个表。
当 from 子句中有子查询时,table列是 <derivenN> 格式,表示当前查询依赖 id=N 的查询,于是先执行 id=N 的查
询。
当有 union 时,UNION RESULT 的 table 列的值为<union1,2>,1和2表示参与 union 的 select 行id。
4. partitions列
如果查询是基于分区表的话,partitions 字段会显示查询将访问的分区。
5. type列
这一列表示关联类型或访问类型,即MySQL决定如何查找表中的行,查找数据行记录的大概范围。
依次从最优到最差分别为:system > const > eq_ref > ref > range > index > ALL
一般来说,得保证查询达到range级别,最好达到ref
NULL:mysql能够在优化阶段分解查询语句,在执行阶段用不着再访问表或索引。例如:在索引列中选取最小值,可以
单独查找索引来完成,不需要在执行时访问表
11 mmyyssqqll>> eexxppllaaiinn sseelleecctt mmiinn((iidd)) ffrroomm ffiillmm;;
const, system:mysql能对查询的某部分进行优化并将其转化成一个常量(可以看show warnings 的结果)。用于
primary key 或 unique key 的所有列与常数比较时,所以表最多有一个匹配行,读取1次,速度比较快。system是
const的特例,表里只有一条元组匹配时为system
11 mmyyssqqll>> eexxppllaaiinn eexxtteennddeedd sseelleecctt ** ffrroomm ((sseelleecctt ** ffrroomm ffiillmm wwhheerree iidd == 11)) ttmmpp;;
11 mmyyssqqll>> sshhooww wwaarrnniinnggss;;

eq_ref:primary key 或 unique key 索引的所有部分被连接使用 ,最多只会返回一条符合条件的记录。这可能是在
const 之外最好的联接类型了,简单的 select 查询不会出现这种 type。
11 mmyyssqqll>> eexxppllaaiinn sseelleecctt ** ffrroomm ffiillmm__aaccttoorr lleefftt jjooiinn ffiillmm oonn ffiillmm__aaccttoorr..ffiillmm__iidd == ffiillmm..iidd;;
ref:相比 eq_ref,不使用唯一索引,而是使用普通索引或者唯一性索引的部分前缀,索引要和某个值相比较,可能会找
到多个符合条件的行。
1. 简单 select 查询,name是普通索引(非唯一索引)
11 mmyyssqqll>> eexxppllaaiinn sseelleecctt ** ffrroomm ffiillmm wwhheerree nnaammee == ''ffiillmm11'';;
2.关联表查询,idx_film_actor_id是film_id和actor_id的联合索引,这里使用到了film_actor的左边前缀film_id部分。
11 mmyyssqqll>> eexxppllaaiinn sseelleecctt ffiillmm__iidd ffrroomm ffiillmm lleefftt jjooiinn ffiillmm__aaccttoorr oonn ffiillmm..iidd == ffiillmm__aaccttoorr..ffiillmm__iidd;;
range:范围扫描通常出现在 in(), between ,> ,<, >= 等操作中。使用一个索引来检索给定范围的行。
11 mmyyssqqll>> eexxppllaaiinn sseelleecctt ** ffrroomm aaccttoorr wwhheerree iidd >> 11;;
index:扫描全索引就能拿到结果,一般是扫描某个二级索引,这种扫描不会从索引树根节点开始快速查找,而是直接对
二级索引的叶子节点遍历和扫描,速度还是比较慢的,这种查询一般为使用覆盖索引,二级索引一般比较小,所以这种通
常比ALL快一些。
11 mmyyssqqll>> eexxppllaaiinn sseelleecctt ** ffrroomm ffiillmm;;
ALL:即全表扫描,扫描你的聚簇索引的所有叶子节点。通常情况下这需要增加索引来进行优化了。
11 mmyyssqqll>> eexxppllaaiinn sseelleecctt ** ffrroomm aaccttoorr;;
6. possible_keys列

这一列显示查询可能使用哪些索引来查找。
explain 时可能出现 possible_keys 有列,而 key 显示 NULL 的情况,这种情况是因为表中数据不多,mysql认为索引对
此查询帮助不大,选择了全表查询。
如果该列是NULL,则没有相关的索引。在这种情况下,可以通过检查 where 子句看是否可以创造一个适当的索引来提高
查询性能,然后用 explain 查看效果。
7. key列
这一列显示mysql实际采用哪个索引来优化对该表的访问。
如果没有使用索引,则该列是 NULL。如果想强制mysql使用或忽视possible_keys列中的索引,在查询中使用 force
index、ignore index。
8. key_len列
这一列显示了mysql在索引里使用的字节数,通过这个值可以算出具体使用了索引中的哪些列。
举例来说,film_actor的联合索引 idx_film_actor_id 由 film_id 和 actor_id 两个int列组成,并且每个int是4字节。通过
结果中的key_len=4可推断出查询使用了第一个列:film_id列来执行索引查找。
11 mmyyssqqll>> eexxppllaaiinn sseelleecctt ** ffrroomm ffiillmm__aaccttoorr wwhheerree ffiillmm__iidd == 22;;
key_len计算规则如下:
字符串,char(n)和varchar(n),5.0.3以后版本中,n均代表字符数,而不是字节数,如果是utf-8,一个数字或字母占1个字节,一个汉字
占3个字节
char(n):如果存汉字长度就是 3n 字节
varchar(n):如果存汉字则长度是 3n + 2 字节,加的2字节用来存储字符串长度,因为varchar是变长字符串
数值类型
tinyint:1字节
smallint:2字节
int:4字节
bigint:8字节
时间类型
date:3字节
timestamp:4字节
datetime:8字节
如果字段允许为 NULL,需要1字节记录是否为 NULL
索引最大长度是768字节,当字符串过长时,mysql会做一个类似左前缀索引的处理,将前半部分的字符提取出来做索
引。
9. ref列
这一列显示了在key列记录的索引中,表查找值所用到的列或常量,常见的有:const(常量),字段名(例:film.id)
10. rows列
这一列是mysql估计要读取并检测的行数,注意这个不是结果集里的行数。
11. filtered 列
该列是一个百分比的值,rows * filtered/100 可以估算出将要和 explain 中前一个表进行连接的行数(前一个表指
explain 中的id值比当前表id值小的表)。

12. Extra列
这一列展示的是额外信息。常见的重要值如下:
1)Using index:使用覆盖索引
覆盖索引定义:mysql执行计划explain结果里的key有使用索引,如果select后面查询的字段都可以从这个索引的树中获
取,这种情况一般可以说是用到了覆盖索引,extra里一般都有using index;覆盖索引一般针对的是辅助索引,整个查询
结果只通过辅助索引就能拿到结果,不需要通过辅助索引树找到主键,再通过主键去主键索引树里获取其它字段值
11 mmyyssqqll>> eexxppllaaiinn sseelleecctt ffiillmm__iidd ffrroomm ffiillmm__aaccttoorr wwhheerree ffiillmm__iidd == 11;;
2)Using where:使用 where 语句来处理结果,并且查询的列未被索引覆盖
11 mmyyssqqll>> eexxppllaaiinn sseelleecctt ** ffrroomm aaccttoorr wwhheerree nnaammee == ''aa'';;
3)Using index condition:查询的列不完全被索引覆盖,where条件中是一个前导列的范围;
11 mmyyssqqll>> eexxppllaaiinn sseelleecctt ** ffrroomm ffiillmm__aaccttoorr wwhheerree ffiillmm__iidd >> 11;;
4)Using temporary:mysql需要创建一张临时表来处理查询。出现这种情况一般是要进行优化的,首先是想到用索引
来优化。
1. actor.name没有索引,此时创建了张临时表来distinct
11 mmyyssqqll>> eexxppllaaiinn sseelleecctt ddiissttiinncctt nnaammee ffrroomm aaccttoorr;;
2. film.name建立了idx_name索引,此时查询时extra是using index,没有用临时表
11 mmyyssqqll>> eexxppllaaiinn sseelleecctt ddiissttiinncctt nnaammee ffrroomm ffiillmm;;
5)Using filesort:将用外部排序而不是索引排序,数据较小时从内存排序,否则需要在磁盘完成排序。这种情况下一般
也是要考虑使用索引来优化的。
1. actor.name未创建索引,会浏览actor整个表,保存排序关键字name和对应的id,然后排序name并检索行记录
11 mmyyssqqll>> eexxppllaaiinn sseelleecctt ** ffrroomm aaccttoorr oorrddeerr bbyy nnaammee;;
2. film.name建立了idx_name索引,此时查询时extra是using index

11 mmyyssqqll>> eexxppllaaiinn sseelleecctt ** ffrroomm ffiillmm oorrddeerr bbyy nnaammee;;
6)Select tables optimized away:使用某些聚合函数(比如 max、min)来访问存在索引的某个字段是
11 mmyyssqqll>> eexxppllaaiinn sseelleecctt mmiinn((iidd)) ffrroomm ffiillmm;;
索引最佳实践
11 示示例例表表::
22 CCRREEAATTEE TTAABBLLEE ``eemmppllooyyeeeess`` ((
33 ``iidd`` iinntt((1111)) NNOOTT NNUULLLL AAUUTTOO__IINNCCRREEMMEENNTT,,
44 ``nnaammee`` vvaarrcchhaarr((2244)) NNOOTT NNUULLLL DDEEFFAAUULLTT '''' CCOOMMMMEENNTT ''姓姓名名'',,
55 ``aaggee`` iinntt((1111)) NNOOTT NNUULLLL DDEEFFAAUULLTT ''00'' CCOOMMMMEENNTT ''年年龄龄'',,
66 ``ppoossiittiioonn`` vvaarrcchhaarr((2200)) NNOOTT NNUULLLL DDEEFFAAUULLTT '''' CCOOMMMMEENNTT ''职职位位'',,
77 ``hhiirree__ttiimmee`` ttiimmeessttaammpp NNOOTT NNUULLLL DDEEFFAAUULLTT CCUURRRREENNTT__TTIIMMEESSTTAAMMPP CCOOMMMMEENNTT ''入入职职时时间间'',,
88 PPRRIIMMAARRYY KKEEYY ((``iidd``)),,
99 KKEEYY ``iiddxx__nnaammee__aaggee__ppoossiittiioonn`` ((``nnaammee``,,``aaggee``,,``ppoossiittiioonn``)) UUSSIINNGG BBTTRREEEE
1100 )) EENNGGIINNEE==IInnnnooDDBB AAUUTTOO__IINNCCRREEMMEENNTT==44 DDEEFFAAUULLTT CCHHAARRSSEETT==uuttff88 CCOOMMMMEENNTT==''员员工工记记录录表表'';;
1111
1122 IINNSSEERRTT IINNTTOO eemmppllooyyeeeess((nnaammee,,aaggee,,ppoossiittiioonn,,hhiirree__ttiimmee)) VVAALLUUEESS((''LLiiLLeeii'',,2222,,''mmaannaaggeerr'',,NNOOWW(())));;
1133 IINNSSEERRTT IINNTTOO eemmppllooyyeeeess((nnaammee,,aaggee,,ppoossiittiioonn,,hhiirree__ttiimmee)) VVAALLUUEESS((''HHaannMMeeiimmeeii'',, 2233,,''ddeevv'',,NNOOWW(())));;
1144 IINNSSEERRTT IINNTTOO eemmppllooyyeeeess((nnaammee,,aaggee,,ppoossiittiioonn,,hhiirree__ttiimmee)) VVAALLUUEESS((''LLuuccyy'',,2233,,''ddeevv'',,NNOOWW(())));;
1.全值匹配
11 EEXXPPLLAAIINN SSEELLEECCTT ** FFRROOMM eemmppllooyyeeeess WWHHEERREE nnaammee== ''LLiiLLeeii'';;
11 EEXXPPLLAAIINN SSEELLEECCTT ** FFRROOMM eemmppllooyyeeeess WWHHEERREE nnaammee== ''LLiiLLeeii'' AANNDD aaggee == 2222;;
11 EEXXPPLLAAIINN SSEELLEECCTT ** FFRROOMM eemmppllooyyeeeess WWHHEERREE nnaammee== ''LLiiLLeeii'' AANNDD aaggee == 2222 AANNDD ppoossiittiioonn ==''mmaannaaggeerr'';;
2.最左前缀法则

如果索引了多列,要遵守最左前缀法则。指的是查询从索引的最左前列开始并且不跳过索引中的列。
11 EEXXPPLLAAIINN SSEELLEECCTT ** FFRROOMM eemmppllooyyeeeess WWHHEERREE nnaammee == ''BBiillll'' aanndd aaggee == 3311;;
22 EEXXPPLLAAIINN SSEELLEECCTT ** FFRROOMM eemmppllooyyeeeess WWHHEERREE aaggee == 3300 AANNDD ppoossiittiioonn == ''ddeevv'';;
33 EEXXPPLLAAIINN SSEELLEECCTT ** FFRROOMM eemmppllooyyeeeess WWHHEERREE ppoossiittiioonn == ''mmaannaaggeerr'';;
3.不在索引列上做任何操作(计算、函数、(自动or手动)类型转换),会导致索引失效而转向全表扫描
11 EEXXPPLLAAIINN SSEELLEECCTT ** FFRROOMM eemmppllooyyeeeess WWHHEERREE nnaammee == ''LLiiLLeeii'';;
22 EEXXPPLLAAIINN SSEELLEECCTT ** FFRROOMM eemmppllooyyeeeess WWHHEERREE lleefftt((nnaammee,,33)) == ''LLiiLLeeii'';;
给hire_time增加一个普通索引:
11 AALLTTEERR TTAABBLLEE ``eemmppllooyyeeeess`` AADDDD IINNDDEEXX ``iiddxx__hhiirree__ttiimmee`` ((``hhiirree__ttiimmee``)) UUSSIINNGG BBTTRREEEE ;;
11 EEXXPPLLAAIINN sseelleecctt ** ffrroomm eemmppllooyyeeeess wwhheerree ddaattee((hhiirree__ttiimmee)) ==''22001188--0099--3300'';;
转化为日期范围查询,有可能会走索引:
11 EEXXPPLLAAIINN sseelleecctt ** ffrroomm eemmppllooyyeeeess wwhheerree hhiirree__ttiimmee >>==''22001188--0099--3300 0000::0000::0000'' aanndd hhiirree__ttiimmee <<==''22001188--0099--3300 2233::
还原最初索引状态
11 AALLTTEERR TTAABBLLEE ``eemmppllooyyeeeess`` DDRROOPP IINNDDEEXX ``iiddxx__hhiirree__ttiimmee``;;
4.存储引擎不能使用索引中范围条件右边的列
11 EEXXPPLLAAIINN SSEELLEECCTT ** FFRROOMM eemmppllooyyeeeess WWHHEERREE nnaammee== ''LLiiLLeeii'' AANNDD aaggee == 2222 AANNDD ppoossiittiioonn ==''mmaannaaggeerr'';;
22 EEXXPPLLAAIINN SSEELLEECCTT ** FFRROOMM eemmppllooyyeeeess WWHHEERREE nnaammee== ''LLiiLLeeii'' AANNDD aaggee >> 2222 AANNDD ppoossiittiioonn ==''mmaannaaggeerr'';;
5.尽量使用覆盖索引(只访问索引的查询(索引列包含查询列)),减少 select * 语句
11 EEXXPPLLAAIINN SSEELLEECCTT nnaammee,,aaggee FFRROOMM eemmppllooyyeeeess WWHHEERREE nnaammee== ''LLiiLLeeii'' AANNDD aaggee == 2233 AANNDD ppoossiittiioonn ==''mmaannaaggeerr'';;
11 EEXXPPLLAAIINN SSEELLEECCTT ** FFRROOMM eemmppllooyyeeeess WWHHEERREE nnaammee== ''LLiiLLeeii'' AANNDD aaggee == 2233 AANNDD ppoossiittiioonn ==''mmaannaaggeerr'';;

6.mysql在使用不等于(!=或者<>),not in ,not exists 的时候无法使用索引会导致全表扫描
< 小于、 > 大于、 <=、>= 这些,mysql内部优化器会根据检索比例、表大小等多个因素整体评估是否使用索引
11 EEXXPPLLAAIINN SSEELLEECCTT ** FFRROOMM eemmppllooyyeeeess WWHHEERREE nnaammee !!== ''LLiiLLeeii'';;
7.is null,is not null 一般情况下也无法使用索引
11 EEXXPPLLAAIINN SSEELLEECCTT ** FFRROOMM eemmppllooyyeeeess WWHHEERREE nnaammee iiss nnuullll
8.like以通配符开头('$abc...')mysql索引失效会变成全表扫描操作
11 EEXXPPLLAAIINN SSEELLEECCTT ** FFRROOMM eemmppllooyyeeeess WWHHEERREE nnaammee lliikkee ''%%LLeeii''
11 EEXXPPLLAAIINN SSEELLEECCTT ** FFRROOMM eemmppllooyyeeeess WWHHEERREE nnaammee lliikkee ''LLeeii%%''
问题:解决like'%字符串%'索引不被使用的方法?
a)使用覆盖索引,查询字段必须是建立覆盖索引字段
11 EEXXPPLLAAIINN SSEELLEECCTT nnaammee,,aaggee,,ppoossiittiioonn FFRROOMM eemmppllooyyeeeess WWHHEERREE nnaammee lliikkee ''%%LLeeii%%'';;
b)如果不能使用覆盖索引则可能需要借助搜索引擎
9.字符串不加单引号索引失效
11 EEXXPPLLAAIINN SSEELLEECCTT ** FFRROOMM eemmppllooyyeeeess WWHHEERREE nnaammee == ''11000000'';;
22 EEXXPPLLAAIINN SSEELLEECCTT ** FFRROOMM eemmppllooyyeeeess WWHHEERREE nnaammee == 11000000;;
10.少用or或in,用它查询时,mysql不一定使用索引,mysql内部优化器会根据检索比例、表大小等多个因素整体评估
是否使用索引,详见范围查询优化
11 EEXXPPLLAAIINN SSEELLEECCTT ** FFRROOMM eemmppllooyyeeeess WWHHEERREE nnaammee == ''LLiiLLeeii'' oorr nnaammee == ''HHaannMMeeiimmeeii'';;

11.范围查询优化
给年龄添加单值索引
11 AALLTTEERR TTAABBLLEE ``eemmppllooyyeeeess`` AADDDD IINNDDEEXX ``iiddxx__aaggee`` ((``aaggee``)) UUSSIINNGG BBTTRREEEE ;;
11 eexxppllaaiinn sseelleecctt ** ffrroomm eemmppllooyyeeeess wwhheerree aaggee >>==11 aanndd aaggee <<==22000000;;
没走索引原因:mysql内部优化器会根据检索比例、表大小等多个因素整体评估是否使用索引。比如这个例子,可能是由
于单次数据量查询过大导致优化器最终选择不走索引
优化方法:可以将大的范围拆分成多个小范围
11 eexxppllaaiinn sseelleecctt ** ffrroomm eemmppllooyyeeeess wwhheerree aaggee >>==11 aanndd aaggee <<==11000000;;
22 eexxppllaaiinn sseelleecctt ** ffrroomm eemmppllooyyeeeess wwhheerree aaggee >>==11000011 aanndd aaggee <<==22000000;;
还原最初索引状态
11 AALLTTEERR TTAABBLLEE ``eemmppllooyyeeeess`` DDRROOPP IINNDDEEXX ``iiddxx__aaggee``;;
索引使用总结:
like KK%相当于=常量,%KK和%KK% 相当于范围
1 -- mysql5.7关闭ONLY_FULL_GROUP_BY报错
2 select version(), @@sql_mode;SET sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''));
文档:02-VIP-Explain详解与索引最佳实践

1 https://note.youdao.com/s/YoQZCEjl
