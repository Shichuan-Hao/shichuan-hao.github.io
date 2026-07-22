---


title: "Spring之配置类解析源码解析"
description: "Spring 之配置类解析源码解析.md..."
author: hsc
date: 2022-05-17 00:00:00 +0800
categories: ['Java 后端', '框架源码']
tags: ['Spring', 'MyBatis', 'IOC']
toc: true


---

11-Spring 之配置类解析源码解析.md

解析配置类解析配置类流程图:https://www.processon.com/view/link/5f9512d5e401fd06fda0b2dd 解析配置类思维脑图:https://www.processon.com/view/link/614c83cae0b34d7b342f6d14
1. 在启动 Spring 时,需要传入一个 AppConfig.class 给 ApplicationContext,ApplicationContext 会根据 AppConfig 类封装为一个 BeanDefinition,这种 BeanDefinition 我们把它称为配置类 BeanDefinition。
2. ConfigurationClassPostProcessor 中会把配置类 BeanDefinition 取出来
3. 构造一个 ConfigurationClassParser 用来解析配置类 BeanDefinition,并且会生成一个配置类对象 ConfigurationClass
4. 如果配置类上存在@Component 注解,那么解析配置类中的内部类(这里有递归,如果内部类也是配置类的话)
5. 如果配置类上存在@PropertySource 注解,那么则解析该注解,并得到 PropertySource 对象,并添加到 environment 中去
6. 如果配置类上存在@ComponentScan 注解,那么则解析该注解,进行扫描,扫描得到一系列的 BeanDefinition 对象,然后判断这些 BeanDefinition 是不是也是配置类 BeanDefinition(只要存在@Component 注解就是配置类,所以基本上扫描出来的都是配置类),如果是则继续解析该配置类,
(也有递归),并且会生成对应的 ConfigurationClass
7. 如果配置类上存在@Import 注解,那么则判断 Import 的类的类型:
i. 如果是 ImportSelector,那么调用执行 selectImports 方法得到类名,然后在把这个类当做配置类进行解析**(也是递归)**ii. 如果是 ImportBeanDefinitionRegistrar,那么则生成一个 ImportBeanDefinitionRegistrar 实例对象,并添加到配置类对象中(ConfigurationClass)的 importBeanDefinitionRegistrars 属性中。
8. 如果配置类上存在@ImportResource 注解,那么则把导入进来的资源路径存在配置类对象中的 importedResources 属性中。
9. 如果配置类中存在@Bean 的方法,那么则把这些方法封装为 BeanMethod 对象,并添加到配置类对象中的 beanMethods 属性中。
10. 如果配置类实现了某些接口,则看这些接口内是否定义了@Bean 的默认方法
11. 如果配置类有父类,则把父类当做配置类进行解析
12. AppConfig 这个配置类会对应一个 ConfigurationClass,同时在解析的过程中也会生成另外的一些 ConfigurationClass,接下来就利用 reader 来进一步解析 ConfigurationClassi. 如果 ConfigurationClass 是通过@Import 注解导入进来的,则把这个类生成一个 BeanDefinition,同时解析这个类上@Scope,@Lazy 等注解信息,并注册 BeanDefinitionii. 如果 ConfigurationClass 中存在一些 BeanMethod,也就是定义了一些@Bean,那么则解析这些@Bean,并生成对应的 BeanDefinition,并注册 iii. 如果 ConfigurationClass 中导入了一些资源文件,比如 xx.xml,那么则解析这些 xx.xml 文件,得到并注册 BeanDefinitioniv. 如果 ConfigurationClass 中导入了一些 ImportBeanDefinitionRegistrar,那么则执行对应的 registerBeanDefinitions 进行 BeanDefinition 的注册总结一下

### 1. 解析 AppConfig 类,生成对应的 ConfigurationClass
### 2. 再扫描,扫描到的类都会生成对应的 BeanDefinition,并且同时这些类也是 ConfigurationClass
### 3. 再解析 ConfigurationClass 的其他信息,比如@ImportResource 注解的处理,@Import 注解的处理,
@Bean 注解的处理
