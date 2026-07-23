---
title: SpringMVC启动与请求处理流程解析
categories: [Java, SpringMVC, 框架源码]
tags: [SpringMVC, DispatcherServlet, RequestMappingHandlerMapping, HandlerAdapter, 九大组件, 请求处理全流程]
author: hsc
date: 2022-06-02 00:00:00 +0800
description: 深入SpringMVC启动与请求处理流程源码，拆解DispatcherServlet初始化、九大组件策略模式以及完整请求处理机制。
mindmap:
---

# SpringMVC启动与请求处理流程解析

## 一、SpringMVC 核心流程图

[完整流程图 - ProcessOn](https://www.processon.com/view/link/5fd9af73e0b34d011deef15f)

---

## 二、SpringMVC 九大组件

`DispatcherServlet` 在初始化时会初始化九大组件，全部默认从 `DispatcherServlet.properties` 中加载。

| 组件 | Bean名称 | 作用 |
|------|---------|------|
| **HandlerMapping** | handlerMapping | 找到处理器 |
| **HandlerAdapter** | handlerAdapter | 执行处理器 |
| **HandlerExceptionResolver** | handlerExceptionResolver | 异常处理 |
| **ViewResolver** | viewResolver | 视图解析 |
| **RequestToViewNameTranslator** | viewNameTranslator | 请求→视图名转换 |
| **MultipartResolver** | multipartResolver | 文件上传解析 |
| **FlashMapManager** | flashMapManager | Flash属性管理 |
| **LocaleResolver** | localeResolver | 国际化 |
| **ThemeResolver** | themeResolver | 主题解析 |

> 策略模式：九大组件都有接口，可自定义实现替换默认。

---

## 三、核心组件详解

### 3.1 HandlerMapping — 找到处理器

**本质**：根据请求找到对应的 `Handler（Controller中的method）` 和 `Interceptor` 列表。

```java
public interface HandlerMapping {
    HandlerExecutionChain getHandler(HttpServletRequest request) throws Exception;
}
```

返回 `HandlerExecutionChain` = `HandlerMethod` + `HandlerInterceptor[]`。

常见实现：
- `RequestMappingHandlerMapping`：处理 `@RequestMapping` 注解
- `BeanNameUrlHandlerMapping`：处理 `beanName="/xxx"` 路径映射
- `SimpleUrlHandlerMapping`：直接配置URL→Handler映射

### 3.2 HandlerAdapter — 执行处理器

**本质**：真正"执行"请求的适配器。

```java
public interface HandlerAdapter {
    boolean supports(Object handler);
    ModelAndView handle(HttpServletRequest request, HttpServletResponse response, Object handler);
}
```

| 适配器 | 处理 |
|--------|------|
| `RequestMappingHandlerAdapter` | 处理 `@RequestMapping` 方法 |
| `HttpRequestHandlerAdapter` | 处理 `HttpRequestHandler` |
| `SimpleControllerHandlerAdapter` | 处理 `Controller` 接口（老版） |

### 3.3 HandlerExceptionResolver — 异常处理

```java
public interface HandlerExceptionResolver {
    ModelAndView resolveException(HttpServletRequest request, HttpServletResponse response,
                                   Object handler, Exception ex);
}
```

### 3.4 ViewResolver — 视图解析

```java
public interface ViewResolver {
    View resolveViewName(String viewName, Locale locale) throws Exception;
}
```

根据 ModelAndView 中的视图名解析为 View 对象。

---

## 四、请求处理全流程

```
DispatcherServlet.doDispatch()
    │
    ├── 1. checkMultipart() → 是否文件上传
    │
    ├── 2. getHandler() → HandlerMapping 找 Handler
    │   └── RequestMappingHandlerMapping.getHandler()
    │       ├── 遍历所有的 handlerMethods
    │       └── 匹配 URL → 返回 HandlerExecutionChain
    │
    ├── 3. getHandlerAdapter(handler) → 找适配器
    │   └── 调用 supports(handler) → 匹配则返回
    │
    ├── 4. mappedHandler.applyPreHandle() → 执行拦截器 preHandle
    │
    ├── 5. ha.handle() → HandlerAdapter.handle()
    │   └── RequestMappingHandlerAdapter.handleInternal()
    │       ├── 解析参数（HandlerMethodArgumentResolver）
    │       ├── 反射调用 controller method
    │       └── 解析返回值（HandlerMethodReturnValueHandler）
    │
    ├── 6. mappedHandler.applyPostHandle() → 拦截器 postHandle
    │
    └── 7. processDispatchResult() → 处理返回结果
        └── applyDefaultViewName → ViewResolver 解析视图 → 渲染
```

### 核心源码

```java
protected void doDispatch(HttpServletRequest request, HttpServletResponse response) throws Exception {
    HttpServletRequest processedRequest = request;
    HandlerExecutionChain mappedHandler = null;
    
    try {
        ModelAndView mv = null;
        Exception dispatchException = null;
        
        // 1. 获取Handler
        mappedHandler = getHandler(processedRequest);
        if (mappedHandler == null) { noHandlerFound(); return; }
        
        // 2. 获取HandlerAdapter
        HandlerAdapter ha = getHandlerAdapter(mappedHandler.getHandler());
        
        // 3. 执行拦截器 preHandle
        if (!mappedHandler.applyPreHandle(processedRequest, response)) { return; }
        
        // 4. 真正执行Handler
        mv = ha.handle(processedRequest, response, mappedHandler.getHandler());
        
        // 5. 拦截器 postHandle
        mappedHandler.applyPostHandle(processedRequest, response, mv);
        
    } catch (Exception ex) { ... }
    
    // 6. 处理返回结果
    processDispatchResult(processedRequest, response, mappedHandler, mv, dispatchException);
}
```

---

## 五、请求处理源码详解

### 5.1 RequestMappingHandlerMapping 如何保存URL映射

启动时会扫描所有 `@Controller` 和 `@RequestMapping`，存入 `MappingRegistry`：

```
MappingRegistry:
├── registry (MultiValueMap)：URL → MappingRegistration
│   ├── /test[GET] → handlerMethod (test())
│   └── /test[POST] → handlerMethod (save())
├── corsLookup：跨域配置
├── handlerMethods：MappingRegistration → HandlerMethod
└── nameLookup：name → HandlerMethod
```

查询URL时：`urlLookup.get(urlPath)` + 匹配HTTP方法 + 匹配Pattern。

### 5.2 参数解析器

`HandlerMethodArgumentResolver` — 将 HTTP 请求参数转换为 Controller 方法参数：

| 解析器 | 处理的注解/类型 |
|--------|---------------|
| `RequestParamMethodArgumentResolver` | `@RequestParam` |
| `PathVariableMethodArgumentResolver` | `@PathVariable` |
| `RequestResponseBodyMethodProcessor` | `@RequestBody` |
| `ModelAttributeMethodProcessor` | `@ModelAttribute` |
| `ServletRequestMethodArgumentResolver` | `HttpServletRequest` 等 |

### 5.3 返回值处理器

`HandlerMethodReturnValueHandler`：

| 处理器 | 处理的返回值 |
|--------|------------|
| `ModelAndViewMethodReturnValueHandler` | `ModelAndView` |
| `RequestResponseBodyMethodProcessor` | `@ResponseBody` |
| `ViewNameMethodReturnValueHandler` | 字符串（视图名） |

---

## 六、DispatcherServlet 继承结构

```
HttpServlet
  └── HttpServletBean → init()模板方法
      └── FrameworkServlet → initServletBean() → initWebApplicationContext()
          └── DispatcherServlet → onRefresh() → initStrategies() → 初始化九大组件
```

---

## 七、总结

```
SpringMVC 请求处理全流程：

DispatcherServlet.init() → 初始化九大组件
    ↓
doDispatch(request, response)
    ├── getHandler() → HandlerMapping 匹配 URL
    ├── getHandlerAdapter() → 找适配器
    ├── HandlerAdapter.handle()
    │   ├── argumentResolvers 解析参数
    │   ├── method.invoke() 反射调用
    │   └── returnValueHandlers 处理返回值
    ├── applyPreHandle / applyPostHandle → 拦截器
    └── processDispatchResult → 视图渲染/JSON响应
```
