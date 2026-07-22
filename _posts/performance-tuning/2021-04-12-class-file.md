---


title: "class文件结构参照表全集"
description: "Class 文件结构类型 名称 数量 u4 固定值(0xCAFEBABE) Magic Number(魔数) 1u2(2 个字节) 次版本号 1u2(2 个字节"
author: hsc
date: 2021-04-12 00:00:00 +0800
categories: ['Java 后端', '性能调优']
tags: ['性能调优', 'MySQL', 'MySQL优化', '索引优化']
toc: true


---

Class 文件结构类型 名称 数量 u4 固定值(0xCAFEBABE) Magic Number(魔数) 1u2(2 个字节) 次版本号 1u2(2 个字节) 主版本号 1u2(2 个字节) constant_pool_cout(常量个数) 1cp_info(N 个字节) constant_pool(常量池表) constant_pool_cout-1u2(2 个字节) access_flag(访问标记符号) 1u2(2 个字节) This class Name 1U2(2 个字节) super class name 1u2(2 个字节) Interfaces_count(接口数) 1u2(二个字节) interfaces(接口名称) Interfaces_countu2(二个字节) fields_count 1field_info(n 个字节) fileds(字段表) fields_countu2(二个字节) methods_count(方法个数) 1method_info(N 个字节) 方法表 methods_countattruibute_count(附加属性 u2(二个字节) 1 个数)
attribute_info(n 个字节) attrubites(附加属性表) attruibute_count 类的访问权限查询手册 flag_name value descACC_PUBLIC 0x0001 public 修饰符号 ACC_FINAL Ox0010 没有子类通过 invokeSpecial 指 ACC_SUPER Ox0020 令可以调用父类的方法 ACC_INTERFACE 0x0200 标识是一个接口 ACC_ABSTRACT 0x0400 表示是一个抽象类该 class 是动态生成的没 ACC_SYNTHETIC 0x1000 有源文件 ACC_ANNOTATION 0x2000 是一个注解类型 ACC_ENUM 0x4000 表示是一个枚举类型 ACC_PRIVATE 0x0002 表示私有的 Field_info 字段表结构类型 名称 数量 u2(1 个) access_flag(权限修饰符) 1u2 name_index(字段名称索引) 1u2 descciptor_index(字段描述索引) 1u2 attribute_count(属性表个数) 1attribute_info attributes attribute_countMethod_info 字段表结构类型 名称 数量 u2 access_flag(权限修饰符) 1u2 name_index(方法名称索引) 1u2 descciptor_index(方法描述索引) 1u2 attribute_count(属性表个数) 1attribute_info attributes attribute_count￼ Method_info 中 attribute_info 结构类型 名称 数量 u2 attribute_name_index 1u4 attribute_length 1u1 info[attribute_length] 1
