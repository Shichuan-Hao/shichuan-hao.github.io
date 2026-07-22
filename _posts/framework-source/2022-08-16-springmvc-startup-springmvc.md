---


title: "SpringMVC启动与请求处理流程解析"
description: "课程内容: 1、Spring MVC 处理请求的基本流程分析 2、四种 Handler 的作用与源码实现 3、三种 HandlerMapping 的作用与源码实"
author: hsc
date: 2022-08-16 00:00:00 +0800
categories: ['Java 后端', '框架源码']
tags: ['Spring', 'MyBatis', 'IOC', 'SpringBoot']
toc: true


---

课程内容:
1、Spring MVC 处理请求的基本流程分析 2、四种 Handler 的作用与源码实现 3、三种 HandlerMapping 的作用与源码实现 4、四种 HandlerAdapter 的作用与源码实现 5、方法参数解析器的作用及源码实现 6、方法返回值处理器的作用及源码实现 19-SpringMVC 启动与请求处理流程解析

原理流程图:https://www.processon.com/view/link/63f1d5cc2f69f86c1f96ee9cSpringMVC 的作用毋庸置疑,虽然我们现在都是用 SpringBoot,但是 SpringBoot 中仍然是在使用 SpringMVC 来处理请求。
我们在使用 SpringMVC 时,传统的方式是通过定义 web.xml,比如:
1 <web-app>23 <servlet>4 <servlet-name>app</servlet-name>5 <servletclass>org.springframework.web.servlet.DispatcherServlet</servlet-class>6 <init-param>7 <param-name>contextConfigLocation</param-name>8 <param-value>/WEB-INF/spring.xml</param-value>9 </init-param>10 <load-on-startup>1</load-on-startup>11 </servlet>1213 <servlet-mapping>14 <servlet-name>app</servlet-name>15 <url-pattern>/app/*</url-pattern>16 </servlet-mapping>1718 </web-app>

我们只要定义这样的一个 web.xml,然后启动 Tomcat,那么我们就能正常使用 SpringMVC 了。
SpringMVC 中,最为核心的就是 DispatcherServlet,在启动 Tomcat 的过程中:
1. Tomcat 会先创建 DispatcherServlet 对象
2. 然后调用 DispatcherServlet 对象的 init()
而在 init()方法中,会创建一个 Spring 容器,并且添加一个 ContextRefreshListener 监听器,该监听器会监听 ContextRefreshedEvent 事件(Spring 容器启动完成后就会发布这个事件),也就是说 Spring 容器启动完成后,就会执行 ContextRefreshListener 中的 onApplicationEvent()方法,从而最终会执行 DispatcherServlet 中的 initStrategies(),这个方法中会初始化更多内容:
1 protected void initStrategies(ApplicationContext context) {2 initMultipartResolver(context);
3 initLocaleResolver(context);
4 initThemeResolver(context);
56 initHandlerMappings(context);
7 initHandlerAdapters(context);
89 initHandlerExceptionResolvers(context);
10 initRequestToViewNameTranslator(context);
11 initViewResolvers(context);
12 initFlashMapManager(context);
13 }其中最为核心的就是 HandlerMapping 和 HandlerAdapter。
什么是 Handler?
Handler 表示请求处理器,在 SpringMVC 中有四种 Handler:
1. 实现了 Controller 接口的 Bean 对象
2. 实现了 HttpRequestHandler 接口的 Bean 对象
3. 添加了@RequestMapping 注解的方法
4. 一个 HandlerFunction 对象

比如实现了 Controller 接口的 Bean 对象:
1 @Component("/test")
2 public class ZhouyuBeanNameController implements Controller {34 @Override5 public ModelAndView handleRequest(HttpServletRequest request,HttpServletResponse response) throws Exception {6 System.out.println("zhouyu");
7 return new ModelAndView();
8 }9 }实现了 HttpRequestHandler 接口的 Bean 对象:
1 @Component("/test")
2 public class ZhouyuBeanNameController implements HttpRequestHandler {34 @Override5 public void handleRequest(HttpServletRequest request, HttpServletResponseresponse) throws ServletException, IOException {6 System.out.println("zhouyu");
7 }8 }添加了@RequestMapping 注解的方法:

1 @RequestMapping2 @Component3 public class ZhouyuController {45 @Autowired6 private ZhouyuService zhouyuService;
78 @RequestMapping(method = RequestMethod.GET, path = "/test")
9 @ResponseBody10 public String test(String username) {11 return "zhouyu";
12 }1314 }一个 HandlerFunction 对象(以下代码中有两个):
1 @ComponentScan("com.zhouyu")
2 @Configuration3 public class AppConfig {45 @Bean6 public RouterFunction<ServerResponse> person() {7 return route()
8 .GET("/app/person", request ->ServerResponse.status(HttpStatus.OK).body("Hello GET"))
9 .POST("/app/person", request ->ServerResponse.status(HttpStatus.OK).body("Hello POST"))
10 .build();
11 }1213 }什么是 HandlerMapping?
HandlerMapping 负责去寻找 Handler,并且保存路径和 Handler 之间的映射关系。

因为有不同类型的 Handler,所以在 SpringMVC 中会由不同的 HandlerMapping 来负责寻找 Handler,比如:
1. BeanNameUrlHandlerMapping:负责 Controller 接口和 HttpRequestHandler 接口
2. RequestMappingHandlerMapping:负责@RequestMapping 的方法
3. RouterFunctionMapping:负责 RouterFunction 以及其中的 HandlerFunctionBeanNameUrlHandlerMapping 的寻找流程:
1. 找出 Spring 容器中所有的 beanName
2. 判断 beanName 是不是以“/”开头
3. 如果是,则把它当作一个 Handler,并把 beanName 作为 key,bean 对象作为 value 存入 handlerMap 中
4. handlerMap 就是一个 MapRequestMappingHandlerMapping 的寻找流程:
1. 找出 Spring 容器中所有 beanType
2. 判断 beanType 是不是有@Controller 注解,或者是不是有@RequestMapping 注解
3. 判断成功则继续找 beanType 中加了@RequestMapping 的 Method
4. 并解析@RequestMapping 中的内容,比如 method、path,封装为一个 RequestMappingInfo 对象
5. 最后把 RequestMappingInfo 对象做为 key,Method 对象封装为 HandlerMethod 对象后作为 value,存入 registry 中
6. registry 就是一个 MapRouterFunctionMapping 的寻找流程会有些区别,但是大体是差不多的,相当于是一个 path 对应一个 HandlerFunction。
各个 HandlerMapping 除开负责寻找 Handler 并记录映射关系之外,自然还需要根据请求路径找到对应的 Handler,在源码中这三个 HandlerMapping 有一个共同的父类 AbstractHandlerMappingAbstractHandlerMapping 实现了 HandlerMapping 接口,并实现了 getHandler(HttpServletRequestrequest)方法。
AbstractHandlerMapping 会负责调用子类的 getHandlerInternal(HttpServletRequest request)方法从而找到请求对应的 Handler,然后 AbstractHandlerMapping 负责将 Handler 和应用中所配置的 HandlerInterceptor 整合成为一个 HandlerExecutionChain 对象。

所以寻找 Handler 的源码实现在各个 HandlerMapping 子类中的 getHandlerInternal()中,根据请求路径找到 Handler 的过程并不复杂,因为路径和 Handler 的映射关系已经存在 Map 中了。
比较困难的点在于,当 DispatcherServlet 接收到一个请求时,该利用哪个 HandlerMapping 来寻找 Handler 呢?看源码:
1 protected HandlerExecutionChain getHandler(HttpServletRequest request) throwsException {2 if (this.handlerMappings != null) {3 for (HandlerMapping mapping : this.handlerMappings) {4 HandlerExecutionChain handler = mapping.getHandler(request);
5 if (handler != null) {6 return handler;
7 }8 }9 }10 return null;
11 }很简单,就是遍历,找到就返回,默认顺序为:
所以 BeanNameUrlHandlerMapping 的优先级最高,比如:
1 @Component("/test")
2 public class ZhouyuBeanNameController implements Controller {34 @Override5 public ModelAndView handleRequest(HttpServletRequest request,HttpServletResponse response) throws Exception {6 System.out.println("Hello zhouyu");
7 return new ModelAndView();
8 }9 }

1 @RequestMapping(method = RequestMethod.GET, path = "/test")
2 @ResponseBody3 public String test(String username) {4 return "Hi zhouyu";
5 }请求路径都是/test,但是最终是 Controller 接口的会生效。
什么是 HandlerAdapter?
找到了 Handler 之后,接下来就该去执行了,比如执行下面这个 test()
1 @RequestMapping(method = RequestMethod.GET, path = "/test")
2 @ResponseBody3 public String test(String username) {4 return "zhouyu";
5 }但是由于有不同种类的 Handler,所以执行方式是不一样的,再来总结一下 Handler 的类型:
1. 实现了 Controller 接口的 Bean 对象,执行的是 Bean 对象中的 handleRequest()
2. 实现了 HttpRequestHandler 接口的 Bean 对象,执行的是 Bean 对象中的 handleRequest()
3. 添加了@RequestMapping 注解的方法,具体为一个 HandlerMethod,执行的就是当前加了注解的方法
4. 一个 HandlerFunction 对象,执行的是 HandlerFunction 对象中的 handle()
所以,按逻辑来说,找到 Handler 之后,我们得判断它的类型,比如代码可能是这样的:

1 Object handler = mappedHandler.getHandler();
2 if (handler instanceof Controller) {3 ((Controller)handler).handleRequest(request, response);
4 } else if (handler instanceof HttpRequestHandler) {5 ((HttpRequestHandler)handler).handleRequest(request, response);
6 } else if (handler instanceof HandlerMethod) {7 ((HandlerMethod)handler).getMethod().invoke(...);
8 } else if (handler instanceof HandlerFunction) {9 ((HandlerFunction)handler).handle(...);
10 }但是 SpringMVC 并不是这么写的,还是采用的适配模式,把不同种类的 Handler 适配成一个 HandlerAdapter,后续再执行 HandlerAdapter 的 handle()方法就能执行不同种类 Hanlder 对应的方法。
针对不同的 Handler,会有不同的适配器:
1. HttpRequestHandlerAdapter
2. SimpleControllerHandlerAdapter
3. RequestMappingHandlerAdapter
4. HandlerFunctionAdapter 适配逻辑为:
1 protected HandlerAdapter getHandlerAdapter(Object handler) throws ServletException {2 if (this.handlerAdapters != null) {3 for (HandlerAdapter adapter : this.handlerAdapters) {4 if (adapter.supports(handler)) {5 return adapter;
6 }7 }8 }9 throw new ServletException("No adapter for handler [" + handler +10 "]: The DispatcherServlet configuration needs toinclude a HandlerAdapter that supports this handler");
11 }传入 handler,遍历上面四个 Adapter,谁支持就返回谁,比如判断的代码依次为:

1 public boolean supports(Object handler) {2 return (handler instanceof HttpRequestHandler);
3 }45 public boolean supports(Object handler) {6 return (handler instanceof Controller);
7 }89 public final boolean supports(Object handler) {10 return (handler instanceof HandlerMethod && supportsInternal((HandlerMethod)
handler));
11 }1213 public boolean supports(Object handler) {14 return handler instanceof HandlerFunction;
15 }根据 Handler 适配出了对应的 HandlerAdapter 后,就执行具体 HandlerAdapter 对象的 handle()方法了,比如:
HttpRequestHandlerAdapter 的 handle():
1 public ModelAndView handle(HttpServletRequest request, HttpServletResponse response,Object handler)
2 throws Exception {3 ((HttpRequestHandler) handler).handleRequest(request, response);
4 return null;
5 }SimpleControllerHandlerAdapter 的 handle():

1 public ModelAndView handle(HttpServletRequest request, HttpServletResponse response,Object handler)
2 throws Exception {3 return ((Controller) handler).handleRequest(request, response);
4 }HandlerFunctionAdapter 的 handle():
1 HandlerFunction<?> handlerFunction = (HandlerFunction<?>) handler;
2 serverResponse = handlerFunction.handle(serverRequest);
因为这三个接收的直接就是 Requeset 对象,不用 SpringMVC 做额外的解析,所以比较简单,比较复杂的是 RequestMappingHandlerAdapter,它执行的是加了@RequestMapping 的方法,而这种方法的写法可以是多种多样,SpringMVC 需要根据方法的定义去解析 Request 对象,从请求中获取出对应的数据然后传递给方法,并执行。
@RequestMapping 方法参数解析当 SpringMVC 接收到请求,并找到了对应的 Method 之后,就要执行该方法了,不过在执行之前需要根据方法定义的参数信息,从请求中获取出对应的数据,然后将数据传给方法并执行。
一个 HttpServletRequest 通常有:
1. request parameter
2. request attribute
3. request session
4. reqeust header
5. reqeust body 比如如下几个方法:
1 public String test(String username) {2 return "zhouyu";
3 }

表示要从 request parameter 中获取 key 为 username 的 value1 public String test(@RequestParam("uname") String username) {2 return "zhouyu";
3 }表示要从 request parameter 中获取 key 为 uname 的 value1 public String test(@RequestAttribute String username) {2 return "zhouyu";
3 }表示要从 request attribute 中获取 key 为 username 的 value1 public String test(@SessionAttribute String username) {2 return "zhouyu";
3 }表示要从 request session 中获取 key 为 username 的 value1 public String test(@RequestHeader String username) {2 return "zhouyu";
3 }表示要从 request header 中获取 key 为 username 的 value

1 public String test(@RequestBody String username) {2 return "zhouyu";
3 }表示获取整个请求体所以,我们发现 SpringMVC 要去解析方法参数,看该参数到底是要获取请求中的哪些信息。
而这个过程,源码中是通过 HandlerMethodArgumentResolver 来实现的,比如:
1. RequestParamMethodArgumentResolver:负责处理@RequestParam
2. RequestHeaderMethodArgumentResolver:负责处理@RequestHeader
3. SessionAttributeMethodArgumentResolver:负责处理@SessionAttribute
4. RequestAttributeMethodArgumentResolver:负责处理@RequestAttribute
5. RequestResponseBodyMethodProcessor:负责处理@RequestBody
6. 还有很多其他的...
而在判断某个参数该由哪个 HandlerMethodArgumentResolver 处理时,也是很粗暴:
1 private HandlerMethodArgumentResolver getArgumentResolver(MethodParameter parameter) {23 HandlerMethodArgumentResolver result = this.argumentResolverCache.get(parameter);
4 if (result == null) {5 for (HandlerMethodArgumentResolver resolver : this.argumentResolvers) {6 if (resolver.supportsParameter(parameter)) {7 result = resolver;
8 this.argumentResolverCache.put(parameter, result);
9 break;
10 }11 }12 }13 return result;
1415 }就是遍历所有的 HandlerMethodArgumentResolver,哪个能支持处理当前这个参数就由哪个处理。

比如:
1 @RequestMapping(method = RequestMethod.GET, path = "/test")
2 @ResponseBody3 public String test(@RequestParam @SessionAttribute String username) {4 System.out.println(username);
5 return "zhouyu";
6 }以上代码的 username 将对应 RequestParam 中的 username,而不是 session 中的,因为在源码中 RequestParamMethodArgumentResolver 更靠前。
当然 HandlerMethodArgumentResolver 也会负责从 request 中获取对应的数据,对应的是 resolveArgument()方法。
比如 RequestParamMethodArgumentResolver:

1 protected Object resolveName(String name, MethodParameter parameter, NativeWebRequestrequest) throws Exception {2 HttpServletRequest servletRequest =request.getNativeRequest(HttpServletRequest.class);
34 if (servletRequest != null) {5 Object mpArg = MultipartResolutionDelegate.resolveMultipartArgument(name,parameter, servletRequest);
6 if (mpArg != MultipartResolutionDelegate.UNRESOLVABLE) {7 return mpArg;
8 }9 }1011 Object arg = null;
12 MultipartRequest multipartRequest =request.getNativeRequest(MultipartRequest.class);
13 if (multipartRequest != null) {14 List<MultipartFile> files = multipartRequest.getFiles(name);
15 if (!files.isEmpty()) {16 arg = (files.size() == 1 ? files.get(0) : files);
17 }18 }19 if (arg == null) {20 String[] paramValues = request.getParameterValues(name);
21 if (paramValues != null) {22 arg = (paramValues.length == 1 ? paramValues[0] : paramValues);
23 }24 }25 return arg;
26 }27 核心是:

1 if (arg == null) {2 String[] paramValues = request.getParameterValues(name);
3 if (paramValues != null) {4 arg = (paramValues.length == 1 ? paramValues[0] : paramValues);
5 }6 }按同样的思路,可以找到方法中每个参数所要求的值,从而执行方法,得到方法的返回值。
@RequestMapping 方法返回值解析而方法返回值,也会分为不同的情况。比如有没有加@ResponseBody 注解,如果方法返回一个 String:
1. 加了@ResponseBody 注解:表示直接将这个 String 返回给浏览器
2. 没有加@ResponseBody 注解:表示应该根据这个 String 找到对应的页面,把页面返回给浏览器在 SpringMVC 中,会利用 HandlerMethodReturnValueHandler 来处理返回值:
1. RequestResponseBodyMethodProcessor:处理加了@ResponseBody 注解的情况
2. ViewNameMethodReturnValueHandler:处理没有加@ResponseBody 注解并且返回值类型为 String 的情况
3. ModelMethodProcessor:处理返回值是 Model 类型的情况
4. 还有很多其他的...
我们这里只讲 RequestResponseBodyMethodProcessor,因为它会处理加了@ResponseBody 注解的情况,也是目前我们用得最多的情况。
RequestResponseBodyMethodProcessor 相当于会把方法返回的对象直接响应给浏览器,如果返回的是一个字符串,那么好说,直接把字符串响应给浏览器,那如果返回的是一个 Map 呢?是一个 User 对象呢?该怎么把这些复杂对象响应给浏览器呢?
处理这块,SpringMVC 会利用 HttpMessageConverter 来处理,比如默认情况下,SpringMVC 会有 4 个 HttpMessageConverter:
1. ByteArrayHttpMessageConverter:处理返回值为字节数组的情况,把字节数组返回给浏览器
2. StringHttpMessageConverter:处理返回值为字符串的情况,把字符串按指定的编码序列号后返回给浏览器
3. SourceHttpMessageConverter:处理返回值为 XML 对象的情况,比如把 DOMSource 对象返回给浏览器
4. AllEncompassingFormHttpMessageConverter:处理返回值为 MultiValueMap 对象的情况

StringHttpMessageConverter 的源码也比较简单:
1 protected void writeInternal(String str, HttpOutputMessage outputMessage) throwsIOException {2 HttpHeaders headers = outputMessage.getHeaders();
3 if (this.writeAcceptCharset && headers.get(HttpHeaders.ACCEPT_CHARSET) == null) {4 headers.setAcceptCharset(getAcceptedCharsets());
5 }6 Charset charset = getContentTypeCharset(headers.getContentType());
7 StreamUtils.copy(str, charset, outputMessage.getBody());
8 }先看有没有设置 Content-Type,如果没有设置则取默认的,默认为 ISO-8859-1,所以默认情况下返回中文会乱码,可以通过以下来中方式来解决:
1 @RequestMapping(method = RequestMethod.GET, path = "/test", produces ={"application/json;charset=UTF-8"})
2 @ResponseBody3 public String test() {4 return "周瑜";
5 }

1 @ComponentScan("com.zhouyu")
2 @Configuration3 @EnableWebMvc4 public class AppConfig implements WebMvcConfigurer {56 @Override7 public void configureMessageConverters(List<HttpMessageConverter<?>>converters) {8 StringHttpMessageConverter messageConverter = newStringHttpMessageConverter();
9 messageConverter.setDefaultCharset(StandardCharsets.UTF_8);
10 converters.add(messageConverter);
11 }12 }不过以上四个 Converter 是不能处理 Map 对象或 User 对象的,所以如果返回的是 Map 或 User 对象,那么得单独配置一个 Converter,比如 MappingJackson2HttpMessageConverter,这个 Converter 比较强大,能把 String、Map、User 对象等等都能转化成 JSON 格式。
1 @ComponentScan("com.zhouyu")
2 @Configuration3 @EnableWebMvc4 public class AppConfig implements WebMvcConfigurer {56 @Override7 public void configureMessageConverters(List<HttpMessageConverter<?>>converters) {8 MappingJackson2HttpMessageConverter messageConverter = newMappingJackson2HttpMessageConverter();
9 messageConverter.setDefaultCharset(StandardCharsets.UTF_8);
10 converters.add(messageConverter);
11 }12 }具体转化的逻辑就是 Jackson2 的转化逻辑。

总结以上就是整个 SpringMVC 从启动到处理请求,从接收请求到执行方法的整体流程。
