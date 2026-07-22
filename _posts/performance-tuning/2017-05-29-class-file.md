---
title: "class文件结构参照表全集"
description: "Class文件结构 类型 名称 数量 u4固定值(0xCAFEBABE) Magic Number(魔数) 1 u2(2个字节) 次版本号 1 u2(2个字节) 主版本号 1 u2(2个字节) constant_pool_cout(常量个数) 1 cp_info(N个字节) constant_pool(常量池表) constant_pool_cout-1 u2(2个字节) access_fl..."
author: hsc
date: 2017-05-29 00:00:00 +0800
categories: ['Java 后端', '性能调优']
tags: ['性能调优', 'JVM', 'MySQL', 'Tomcat', 'GC']
toc: true
---

> 本文整理自《一、性能调优专题》课程笔记，共 1 页。

Class文件结构
类型 名称 数量
u4固定值(0xCAFEBABE) Magic Number(魔数) 1
u2(2个字节) 次版本号 1
u2(2个字节) 主版本号 1
u2(2个字节) constant_pool_cout(常量个数) 1
cp_info(N个字节) constant_pool(常量池表) constant_pool_cout-1
u2(2个字节) access_flag(访问标记符号) 1
u2(2个字节) This class Name 1
U2(2个字节) super class name 1
u2(2个字节) Interfaces_count(接口数) 1
u2(二个字节) interfaces(接口名称) Interfaces_count
u2(二个字节) fields_count 1
field_info(n个字节) fileds(字段表) fields_count
u2(二个字节) methods_count(方法个数) 1
method_info(N个字节) 方法表 methods_count
attruibute_count(附加属性
u2(二个字节) 1
个数)
attribute_info(n个字节) attrubites(附加属性表) attruibute_count
类的访问权限查询手册
flag_name value desc
ACC_PUBLIC 0x0001 public修饰符号
ACC_FINAL Ox0010 没有子类
通过invokeSpecial指
ACC_SUPER Ox0020
令可以调用父类的方法
ACC_INTERFACE 0x0200 标识是一个接口
ACC_ABSTRACT 0x0400 表示是一个抽象类
该class是动态生成的没
ACC_SYNTHETIC 0x1000
有源文件
ACC_ANNOTATION 0x2000 是一个注解类型
ACC_ENUM 0x4000 表示是一个枚举类型
ACC_PRIVATE 0x0002 表示私有的
Field_info 字段表结构
类型 名称 数量
u2(1个) access_flag(权限修饰符) 1
u2 name_index(字段名称索引) 1
u2 descciptor_index(字段描述索引) 1
u2 attribute_count(属性表个数) 1
attribute_info attributes attribute_count
Method_info 字段表结构
类型 名称 数量
u2 access_flag(权限修饰符) 1
u2 name_index(方法名称索引) 1
u2 descciptor_index(方法描述索引) 1
u2 attribute_count(属性表个数) 1
attribute_info attributes attribute_count
￼ Method_info中attribute_info 结构
类型 名称 数量
u2 attribute_name_index 1
u4 attribute_length 1
u1 info[attribute_length] 1
