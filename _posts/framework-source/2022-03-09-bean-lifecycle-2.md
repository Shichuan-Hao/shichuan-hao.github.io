---



title: "Spring之Bean生命周期源码解析（下）"
description: "Spring 之 Bean 生命周期源码解析(下).md"
author: hsc
date: 2022-03-09 00:00:00 +0800
categories: ['Java 后端', '框架源码']
tags: ['Spring', 'MyBatis', 'IOC']
toc: true



---

05-Spring 之 Bean 生命周期源码解析(下).md

Bean 的销毁过程 Bean 销毁是发送在 Spring 容器关闭过程中的。
在 Spring 容器关闭时,比如:
AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(AppConfig.class);
UserService userService = (UserService) context.getBean("userService");
userService.test();
// 容器关闭 context.close();
在 Bean 创建过程中,在最后(初始化之后),有一个步骤会去判断当前创建的 Bean 是不是 DisposableBean:
1. 当前 Bean 是否实现了 DisposableBean 接口
2. 或者,当前 Bean 是否实现了 AutoCloseable 接口
3. BeanDefinition 中是否指定了 destroyMethod
4. 调用 DestructionAwareBeanPostProcessor.requiresDestruction(bean)进行判断 i. ApplicationListenerDetector 中直接使得 ApplicationListener 是 DisposableBeanii. InitDestroyAnnotationBeanPostProcessor 中使得拥有@PreDestroy 注解了的方法就是 DisposableBean
5. 把符合上述任意一个条件的 Bean 适配成 DisposableBeanAdapter 对象,并存入 disposableBeans 中(一个 LinkedHashMap)
在 Spring 容器关闭过程时:
1. 首先发布 ContextClosedEvent 事件
2. 调用 lifecycleProcessor 的 onCloese()方法
3. 销毁单例 Beani. 遍历 disposableBeansa. 把每个 disposableBean 从单例池中移除 b. 调用 disposableBean 的 destroy()
c. 如果这个 disposableBean 还被其他 Bean 依赖了,那么也得销毁其他 Beand. 如果这个 disposableBean 还包含了 inner beans,将这些 Bean 从单例池中移除掉 (inner bean 参考 https://docs.spring.io/spring-framework/docs/current/spring-frameworkreference/core.html#beans-inner-beans)
ii. 清空 manualSingletonNames,是一个 Set,存的是用户手动注册的单例 Bean 的 beanNameiii. 清空 allBeanNamesByType,是一个 Map,key 是 bean 类型,value 是该类型所有的 beanName 数组 iv. 清空 singletonBeanNamesByType,和 allBeanNamesByType 类似,只不过只存了单例 Bean

这里涉及到一个设计模式:适配器模式在销毁时,Spring 会找出实现了 DisposableBean 接口的 Bean。
但是我们在定义一个 Bean 时,如果这个 Bean 实现了 DisposableBean 接口,或者实现了 AutoCloseable 接口,或者在 BeanDefinition 中指定了 destroyMethodName,那么这个 Bean 都属于“DisposableBean”,这些 Bean 在容器关闭时都要调用相应的销毁方法。
所以,这里就需要进行适配,将实现了 DisposableBean 接口、或者 AutoCloseable 接口等适配成实现了 DisposableBean 接口,所以就用到了 DisposableBeanAdapter。
会把实现了 AutoCloseable 接口的类封装成 DisposableBeanAdapter,而 DisposableBeanAdapter 实现了 DisposableBean 接口。
