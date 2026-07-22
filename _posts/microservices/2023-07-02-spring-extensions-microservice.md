---


title: "Spring扩展点在微服务组件中的应用"
description: "掌握 Spring 主线流程源码掌握 Spring Boot 主线流程源码熟悉 Spring Cloud&Spring Cloud Alibaba 中间件核心功"
author: hsc
date: 2023-07-02 00:00:00 +0800
categories: ['Java 后端', '微服务']
tags: ['微服务', 'SpringCloud', 'SpringBoot', 'Nacos', 'Sentinel', 'Docker']
toc: true


---

掌握 Spring 主线流程源码掌握 Spring Boot 主线流程源码熟悉 Spring Cloud&Spring Cloud Alibaba 中间件核心功能源码
1. Spring 扩展点梳理 BeanFactoryPostProcessorBeanDefinitionRegistryPostProcessorBeanPostProcessorInstantiationAwareBeanPostProcessorAbstractAutoProxyCreator@ImportImportBeanDefinitionRegistrarImportSelectorAwareApplicationContextAwareBeanFactoryAwareInitializingBean || @PostConstructFactoryBeanSmartInitializingSingletonApplicationListenerLifecycleSmartLifecycleLifecycleProcessorHandlerInterceptorMethodInterceptorIoC 工作原理 https://www.processon.com/view/link/5cd10507e4b085d010929d02

Bean 生命周期主线流程:
2. Spring 扩展点在微服务组件中的应用场景
2.1 整合 NacosApplicationListener 扩展场景——监听容器中发布的事件思考: 为什么整合 Nacos 注册中心后,服务启动就会自动注册,Nacos 是如何实现自动服务注册的?
NacosAutoServiceRegistration

1 # 对 ApplicationListener 的扩展 2 AbstractAutoServiceRegistration#onApplicationEvent3 # 服务注册 4 》NacosServiceRegistry#registerNacos 注册中心源码分析 https://www.processon.com/view/link/5ea27ca15653bb6efc68eb8c

Lifecycle 扩展场景——管理具有启动、停止生命周期需求的对象 NacosWatch1 #对 SmartLifecycle 的扩展 2 NacosWatch#start3 #订阅服务接收实例更改的事件 4 》NamingService#subscribe 扩展: Eureka Server 端上下文的初始化是在 SmartLifecycle#start 中实现的 EurekaServerInitializerConfigurationEureka Server 源码分析:
#### 2.2 整合 Ribbon、LoadBalancerSmartInitializingSingleton 扩展场景—— 对容器中的 Bean 对象进行定制处理思考:为什么@Bean 修饰的 RestTemplate 加上@LoadBalanced 就能实现负载均衡功能?
1 @Bean2 @LoadBalanced3 public RestTemplate restTemplate() {4 return new RestTemplate();
5 }LoadBalancerAutoConfiguration 对 SmartInitializingSingleton 的扩展,为所有用@LoadBalanced 修饰的 restTemplate(利用了@Qualifier)绑定实现了负载均衡逻辑的拦截器 LoadBalancerInterceptor

LoadBalancerInterceptorRibbon 源码分析:
#### 2.3 整合 FeignFactoryBean 的扩展场景——将接口生成的代理对象交给 Spring 管理思考:为什么 Feign 接口可以通过@Autowired 直接注入使用?Feign 接口是如何交给 Spring 管理的?

1 @FeignClient(value = "mall-order",path = "/order")
2 public interface OrderFeignService {34 @RequestMapping("/findOrderByUserId/{userId}")
5 R findOrderByUserId(@PathVariable("userId") Integer userId);
6 }78 @RestController9 @RequestMapping("/user")
10 public class UserController {1112 @Autowired13 OrderFeignService orderFeignService;
1415 @RequestMapping(value = "/findOrderByUserId/{id}")
16 public R findOrderByUserId(@PathVariable("id") Integer id) {17 //feign 调用 18 R result = orderFeignService.findOrderByUserId(id);
19 return result;
20 }21 }FeignClientsRegistrarFeignClientFactorybean

Feign 源码分析:
2.4 整合 sentinelHandlerInterceptor 扩展场景——对 mvc 请求增强 AbstractSentinelInterceptor

1 # Webmvc 接口资源保护入口 2 AbstractSentinelInterceptor#preHandleSmartInitializingSingleton&FactoryBean 结合场景——根据类型动态装配对象 SentinelDataSourceHandler1 #Sentinel 持久化读数据源设计,利用了 SmartInitializingSingleton 扩展点 2 SentinelDataSourceHandler#afterSingletonsInstantiated3 # 注册一个 FactoryBean 类型的数据源 4 》SentinelDataSourceHandler#registerBean5 》》NacosDataSourceFactoryBean#getObject6 # 利用 FactoryBean 获取到读数据源 7 》》new NacosDataSource(properties, groupId, dataId, converter)

NacosDataSourceFactoryBeansentinel 规则持久化源码分析:
2.5 整合 seataAbstractAutoProxyCreator&MethodInterceptor 结合场景——实现方法增强 GlobalTransactionScanner

GlobalTransactionalInterceptorSeata 源码分析:
3.使用 AI 高效学习微服务组件源码 idea 插件推荐 TONGYI Lingma 通义灵码,是一款基于通义大模型的智能编码辅助工具,提供行级/函数级实时续写、自然语言生成代码、单元测试生成、代码注释生成、代码解释、研发智能问答、异常报错排查等能力,并针对阿里云 SDK/API 的使用场景调优,为开发者带来高效、流畅的编码体验。

Baidu Comate 文心快码 - 百度智能编码助手,您的人工智能编程伙伴。这款基于人工智能的智能代码生成工具,让您的编码更快、更好、更简单!文心快码由 ERNIE-Code 驱动,该模型基于百度多年积累的非敏感代码数据以及来自 GitHub 的顶级公开代码数据进行训练。它能自动生成完整且更贴合特定场景的代码行或代码块,助力每一位开发者轻松完成开发任务。
MarsCode AIMarsCode AI 是豆包旗下的智能编程助手,提供以智能代码补全为代表的核心能力,支持主流编程语言及 IDE,能在编码过程中提供单行或整个函数的建议,同时支持在用户编码过程中提供代码解释、单测生成、问题修复、技术问答等辅助功能,提升编码效率与质量。
SpringBoot + Spring AI Alibaba 实现 AI 智能体应用开发 Spring 官方开源了 Spring AI 框架,用来简化 Spring 开发者开发智能体应用的过程。随后阿里巴巴开源了 Spring AI Alibaba,它基于 Spring AI,同时与阿里云百炼大模型服务、通义系列大模型做了深度集成与最佳实践。基于 Spring AI Alibaba,Java 开发者可以非常方便地开发 AI 智能体应用。
官网地址:https://java2ai.com/接入 DeepSeek:
SpringBoot + Spring AI Alibaba 整合阿里云百炼 DeepSeek 大模型,小白也能轻松上手
