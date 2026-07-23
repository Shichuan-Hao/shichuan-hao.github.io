---
title: SpringMVC重点功能底层源码解析
categories: [Java, SpringMVC, 框架源码]
tags: [SpringMVC, 参数解析, 消息转换器, HttpMessageConverter, 文件上传, 拦截器, '@ResponseBody', '@EnableWebMvc']
author: hsc
date: 2022-06-04 00:00:00 +0800
description: 深入SpringMVC重点功能源码解析，涵盖参数解析器、HttpMessageConverter、文件上传、拦截器、@EnableWebMvc自动配置等核心机制。
mindmap: https://www.processon.com/view/link/63e9f3e6234df52a1e9303fb
---

# SpringMVC重点功能底层源码解析

## 一、参数解析与类型转换

### 1.1 @RequestParam 参数解析

`RequestParamMethodArgumentResolver` 解析 `@RequestParam` 标注的参数。

```java
public class RequestParamMethodArgumentResolver implements HandlerMethodArgumentResolver {
    @Override
    public boolean supportsParameter(MethodParameter parameter) {
        // 1. 有@RequestParam注解
        // 2. 有@RequestPart但无Part类型参数
        // 3. 简单类型（String/int等）会自动用这个resolver
    }
    
    @Override
    public Object resolveArgument(...) {
        // 1. 从 request.getParameterValues() 获取值
        // 2. 类型转换（TypeConverter）
        // 3. 返回
    }
}
```

### 1.2 类型转换器

Spring 提供了 `TypeConverter` 进行类型转换（String → Integer、Date 等）。可通过 `@InitBinder` 自定义：

```java
@InitBinder
public void initBinder(WebDataBinder binder) {
    binder.registerCustomEditor(Date.class, new CustomDateEditor(sdf, true));
}
```

---

## 二、@ResponseBody 与 HttpMessageConverter

### 2.1 流程

```java
@ResponseBody
@RequestMapping("/test")
public User test() {
    return new User("zhouyu");
}
```

执行流程：

```
1. RequestResponseBodyMethodProcessor.handleReturnValue()
2. 选一个合适的 HttpMessageConverter
3. 调用 converter.write(user, response.getOutputStream())
```

### 2.2 MessageConverter 选择规则

```
遍历所有 HttpMessageConverter：
    ├── converter.canWrite(clazz, mediaType)？
    │   ├── 匹配返回类型？
    │   ├── 匹配 produces 指定的 MediaType？
    │   └── 若有Accept头，匹配Accept中的MediaType？
    └── 匹配 → 使用该converter写回响应
```

| Converter | 支持的类型 |
|-----------|----------|
| `MappingJackson2HttpMessageConverter` | 对象 → JSON（`application/json`） |
| `StringHttpMessageConverter` | 字符串 → text（支持所有 MediaType） |
| `ByteArrayHttpMessageConverter` | 字节数组 |

### 2.3 自定义 MessageConverter

```java
public class ZhouyuHttpMessageConverter extends AbstractHttpMessageConverter<User> {
    @Override
    protected boolean supports(Class cls) {
        return User.class == cls;  // 只能处理User类型
    }
    
    @Override
    protected List<MediaType> getSupportedMediaTypes() {
        return List.of(MediaType.ALL);  // 支持所有类型
    }
    
    @Override
    protected void writeInternal(User user, HttpOutputMessage outputMessage) {
        StreamUtils.copy(user.getName(), Charset.defaultCharset(), outputMessage.getBody());
    }
    
    @Override
    protected User readInternal(...) { return null; }
}
```

配置：

```xml
<mvc:annotation-driven>
    <mvc:message-converters>
        <bean class="com.zhouyu.ZhouyuHttpMessageConverter"/>
        <bean class="org.springframework.http.converter.json.MappingJackson2HttpMessageConverter"/>
    </mvc:message-converters>
</mvc:annotation-driven>
```

---

## 三、文件上传

### 3.1 MultipartResolver

```java
public interface MultipartResolver {
    boolean isMultipart(HttpServletRequest request);
    MultipartHttpServletRequest resolveMultipart(HttpServletRequest request);
}
```

Spring 检测到 `multipart/form-data` 时自动解析。

### 3.2 文件上传流程

```
1. MultipartResolver 判断是否为 multipart/form-data 请求
2. 是 → 封装为 StandardMultipartHttpServletRequest
3. 获取所有 Part → 遍历
4. 判断每个 Part：
   ├── 文件 → 封装为 StandardMultipartFile → 存入 multipartFiles
   └── 文本 → 名字存入 multipartParameterNames
5. 参数解析时：
   └── 参数类型是 MultipartFile → 从 multipartFiles 获取
```

### 3.3 文件+参数混合请求

`multipart/form-data` 中的文本字段通过 `@RequestParam` 获取，文件字段通过 `@RequestPart`（或 `MultipartFile` 参数）获取。

```java
@PostMapping("/upload")
public String upload(@RequestParam String name, @RequestPart MultipartFile file) {
    ...
}
```

---

## 四、拦截器（HandlerInterceptor）

```java
public interface HandlerInterceptor {
    default boolean preHandle(HttpServletRequest request, HttpServletResponse response, 
                              Object handler) { return true; }
    
    default void postHandle(HttpServletRequest request, HttpServletResponse response,
                            Object handler, ModelAndView modelAndView) { }
    
    default void afterCompletion(HttpServletRequest request, HttpServletResponse response,
                                 Object handler, Exception ex) { }
}
```

**执行顺序**：[查看流程图](https://www.processon.com/view/link/63e9f3e6234df52a1e9303fb)

```
preHandle1 → preHandle2 → Controller → postHandle2 → postHandle1 → afterCompletion2 → afterCompletion1
```

### 注册拦截器

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new MyInterceptor())
                .addPathPatterns("/**")
                .excludePathPatterns("/login");
    }
}
```

### 源码实现

`@EnableWebMvc` → `@Import(DelegatingWebMvcConfiguration.class)` → 在创建 `RequestMappingHandlerMapping` 时调用 `getInterceptors()`：

```java
@Bean
public RequestMappingHandlerMapping requestMappingHandlerMapping() {
    RequestMappingHandlerMapping mapping = createRequestMappingHandlerMapping();
    mapping.setInterceptors(getInterceptors());
    return mapping;
}

// getInterceptors() → addInterceptors() → 遍历所有 WebMvcConfigurer
```

---

## 五、@EnableWebMvc 干了什么

```java
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
@Documented
@Import(DelegatingWebMvcConfiguration.class)
public @interface EnableWebMvc { }
```

`DelegatingWebMvcConfiguration`：
1. 继承了 `WebMvcConfigurationSupport`
2. 定义了核心Bean（`RequestMappingHandlerMapping`、`RequestMappingHandlerAdapter` 等）
3. 注入所有 `WebMvcConfigurer` 实现 → 通过 `setConfigurers()` 收集

**WebMvcConfigurerComposite** 通过**委派模式**把调用转发给所有 WebMvcConfigurer。

---

## 六、SpringBoot中WebMvc的自动配置

SpringBoot的 `WebMvcAutoConfiguration`：

```
条件注解判断：@ConditionalOnMissingBean(WebMvcConfigurationSupport.class)
    ├── 无 → 自动配置生效
    └── 有（用户加了@EnableWebMvc）→ 自动配置失效

原因：@EnableWebMvc 继承了 WebMvcConfigurationSupport
```

---

## 七、总结

```
SpringMVC 重点功能全景：

参数解析：
├── HandlerMethodArgumentResolver（20+个实现）
├── TypeConverter 类型转换
└── @InitBinder 自定义转换

返回值处理：
├── HandlerMethodReturnValueHandler
├── HttpMessageConverter 系列
└── @ResponseBody → Jackson2 → JSON

文件上传：
└── MultipartResolver → Part → MultipartFile

拦截器：
└── HandlerInterceptor → pre→controller→post→after

自动配置：
├── WebMvcConfigurer → 扩展配置（不会覆盖默认）
└── @EnableWebMvc → 完全接管配置
```
