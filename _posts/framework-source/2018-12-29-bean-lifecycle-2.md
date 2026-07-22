---
title: "-Spring之Bean生命周期源码解析（下）【耗时整理‖cunlove.cn】"
description: "【有道云笔记】05-Spring之Bean生命周期源码解析(下).md https://note.youdao.com/s/9gIT5JYl Bean的销毁过程 Bean销毁是发送在Spring容器关闭过程中的。 在Spring容器关闭时,比如: AnnotationConfigApplicationContext context = new AnnotationConfigApplicat..."
author: hsc
date: 2018-12-29 00:00:00 +0800
categories: ['Java 后端', '框架源码']
tags: ['Spring', 'MyBatis', '源码分析', '框架']
toc: true
---

> 本文整理自《二、框架源码专题》课程笔记，共 2 页。

【有道云笔记】05-Spring之Bean生命周期源码解析(下).md
https://note.youdao.com/s/9gIT5JYl
Bean的销毁过程
Bean销毁是发送在Spring容器关闭过程中的。
在Spring容器关闭时,比如:
AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(AppConfig.clas
s);
UserService userService = (UserService) context.getBean("userService");
userService.test();
// 容器关闭
context.close();
在Bean创建过程中,在最后(初始化之后),有一个步骤会去判断当前创建的Bean是不是DisposableBean:
1. 当前Bean是否实现了DisposableBean接口
2. 或者,当前Bean是否实现了AutoCloseable接口
3. BeanDefinition中是否指定了destroyMethod
4. 调用DestructionAwareBeanPostProcessor.requiresDestruction(bean)进行判断
i. ApplicationListenerDetector中直接使得ApplicationListener是DisposableBean
ii. InitDestroyAnnotationBeanPostProcessor中使得拥有@PreDestroy注解了的方法就是
DisposableBean
5. 把符合上述任意一个条件的Bean适配成DisposableBeanAdapter对象,并存入disposableBeans中(一
个LinkedHashMap)
在Spring容器关闭过程时:
1. 首先发布ContextClosedEvent事件
2. 调用lifecycleProcessor的onCloese()方法
3. 销毁单例Bean
i. 遍历disposableBeans
a. 把每个disposableBean从单例池中移除
b. 调用disposableBean的destroy()
c. 如果这个disposableBean还被其他Bean依赖了,那么也得销毁其他Bean
d. 如果这个disposableBean还包含了inner beans,将这些Bean从单例池中移除掉 (inner bean参
考https://docs.spring.io/spring-framework/docs/current/spring-framework-
reference/core.html#beans-inner-beans)
ii. 清空manualSingletonNames,是一个Set,存的是用户手动注册的单例Bean的beanName
iii. 清空allBeanNamesByType,是一个Map,key是bean类型,value是该类型所有的beanName数组
iv. 清空singletonBeanNamesByType,和allBeanNamesByType类似,只不过只存了单例Bean

这里涉及到一个设计模式:适配器模式
在销毁时,Spring会找出实现了DisposableBean接口的Bean。
但是我们在定义一个Bean时,如果这个Bean实现了DisposableBean接口,或者实现了AutoCloseable接口,
或者在BeanDefinition中指定了destroyMethodName,那么这个Bean都属于“DisposableBean”,这些
Bean在容器关闭时都要调用相应的销毁方法。
所以,这里就需要进行适配,将实现了DisposableBean接口、或者AutoCloseable接口等适配成实现了
DisposableBean接口,所以就用到了DisposableBeanAdapter。
会把实现了AutoCloseable接口的类封装成DisposableBeanAdapter,而DisposableBeanAdapter实现了
DisposableBean接口。
