---


title: "SpringMVC重点功能底层源码解析"
description: "课程内容: 1、方法参数解析源码分析 2、文件上传 MultipartFile 源码解析 3、方法返回值解析源码分析 4、视图解析核心源码分析 5、Spring"
author: hsc
date: 2022-08-28 00:00:00 +0800
categories: ['Java 后端', '框架源码']
tags: ['Spring', 'MyBatis', 'IOC']
toc: true


---

课程内容:
1、方法参数解析源码分析 2、文件上传 MultipartFile 源码解析 3、方法返回值解析源码分析 4、视图解析核心源码分析 5、SpringMVC 拦截器源码解析 6、@EnableWebMvc 源码解析 7、WebApplicationInitializer 使用方式 8、SpringMVC 父子容器介绍与源码分析 20-SpringMVC 重点功能底层源码解析

SpringMVC 处理请求核心流程图:https://www.processon.com/view/link/63f4cf1176e6143857799c2a 课堂疑问 1:
当我们使用@RequestParam,并且没有注册 StringToUserEditor 时,但是 User 中提供了一个 String 类型参数的构造方法时:
1 @RequestMapping(method = RequestMethod.GET, path = "/test")
2 @ResponseBody3 public String test(@RequestParam("name") User user) {4 return user.getName();
5 }

1 public class User {23 private String name;
45 public User(String name) {6 this.name = name;
7 }89 public String getName() {10 return name;
11 }1213 public void setName(String name) {14 this.name = name;
15 }16 }SpringMVC 在进行把 String 转成 User 对象时,会先判断有没有 User 类型对应的 StringToUserEditor,如果有就会利用它来把 String 转成 User 对象,如果没有则会找 User 类中有没有 String 类型参数的构造方法,如果有则用该构造方法来构造出 User 对象。
对应的源码方法为:
org.springframework.beans.TypeConverterDelegate#convertIfNecessary(java.lang.String,java.lang.Object, java.lang.Object, java.lang.Class<T>,org.springframework.core.convert.TypeDescriptor)

课堂疑问 2:
如果方法返回的是 byte[]:
1 @RequestMapping(method = RequestMethod.GET, path = "/test")
2 @ResponseBody3 public byte[] test() {4 byte[] bytes = new byte[1024];
5 return bytes;
6 }这种情况会直接使用 ByteArrayHttpMessageConverter 来处理,会直接把 byte[]写入响应中:

1 public class ByteArrayHttpMessageConverter extendsAbstractHttpMessageConverter<byte[]> {23 /**4 * Create a new instance of the {@code ByteArrayHttpMessageConverter}.5 */6 public ByteArrayHttpMessageConverter() {7 super(MediaType.APPLICATION_OCTET_STREAM, MediaType.ALL);
8 }91011 @Override12 public boolean supports(Class<?> clazz) {13 return byte[].class == clazz;
14 }1516 // ...1718 @Override19 protected void writeInternal(byte[] bytes, HttpOutputMessage outputMessage)
throws IOException {20 StreamUtils.copy(bytes, outputMessage.getBody());
21 }2223 }SpringMVC 父子容器我们可以在 web.xml 文件中这么来定义:

1 <web-app>23 <listener>4 <listenerclass>org.springframework.web.context.ContextLoaderListener</listener-class>5 </listener>67 <context-param>8 <param-name>contextConfigLocation</param-name>9 <param-value>/WEB-INF/spring.xml</param-value>10 </context-param>1112 <servlet>13 <servlet-name>app</servlet-name>14 <servletclass>org.springframework.web.servlet.DispatcherServlet</servlet-class>15 <init-param>16 <param-name>contextConfigLocation</param-name>17 <param-value>/WEB-INF/spring-mvc.xml</param-value>18 </init-param>19 <load-on-startup>1</load-on-startup>20 </servlet>2122 <servlet-mapping>23 <servlet-name>app</servlet-name>24 <url-pattern>/app/*</url-pattern>25 </servlet-mapping>2627 </web-app>2829 在这个 web.xml 文件中,我们定义了一个 listener 和 servlet。
父容器的创建 ContextLoaderListener 的作用是用来创建一个 Spring 容器,就是我们说的 SpringMVC 父子容器中的父容器,执行流程为:
1. Tomcat 启动,解析 web.xml 时

### 2. 发现定义了一个 ContextLoaderListener,Tomcat 就会执行该 listener 中的 contextInitialized()方法,该方法就会去创建要给 Spring 容器
### 3. 从 ServletContext 中获取 contextClass 参数值,该参数表示所要创建的 Spring 容器的类型,可以在 web.xml 中通过<context-param>来进行配置
### 4. 如果没有配置该参数,那么则会从 ContextLoader.properties 文件中读取 org.springframework.web.context.WebApplicationContext 配置项的值,SpringMVC 默认提供了一个 ContextLoader.properties 文件,内容为 org.springframework.web.context.support.XmlWebApplicationContext
### 5. 所以 XmlWebApplicationContext 就是要创建的 Spring 容器类型
### 6. 确定好类型后,就用反射调用无参构造方法创建出来一个 XmlWebApplicationContext 对象
### 7. 然后继续从 ServletContext 中获取 contextConfigLocation 参数的值,也就是一个 spring 配置文件的路径
### 8. 把 spring 配置文件路径设置给 Spring 容器,然后调用 refresh(),从而启动 Spring 容器,从而解析 spring 配置文件,
从而扫描生成 Bean 对象等
9. 这样 Spring 容器就创建出来了
10. 有了 Spring 容器后,就会把 XmlWebApplicationContext 对象作为 attribute 设置到 ServletContext 中去,key 为 WebApplicationContext.ROOT_WEB_APPLICATION_CONTEXT_ATTRIBUTE
11. 把 Spring 容器存到 ServletContext 中的原因,是为了给 Servlet 创建出来的子容器来作为父容器的子容器的创建 Tomcat 启动过程中,执行完 ContextLoaderListener 的 contextInitialized()之后,就会创建 DispatcherServlet 了,web.xml 中定义 DispatcherServlet 时,load-on-startup 为 1,表示在 Tomcat 启动过程中要把这个 DispatcherServlet 创建并初始化出来,而这个过程是比较费时间的,所以要把 load-on-
startup 设置为 1,如果不为 1,会在 servlet 接收到请求时才来创建和初始化,这样会导致请求处理比较慢。
1. Tomcat 启动,解析 web.xml 时
2. 创建 DispatcherServlet 对象
3. 调用 DispatcherServlet 的 init()
4. 从而调用 initServletBean()
5. 从而调用 initWebApplicationContext(),这个方法也会去创建一个 Spring 容器(就是子容器)
6. initWebApplicationContext()执行过程中,会先从 ServletContext 拿出 ContextLoaderListener 所创建的 Spring 容器(父容器),记为 rootContext
7. 然后读取 contextClass 参数值,可以在 servlet 中的<init-param>标签来定义想要创建的 Spring 容器类型,默认为 XmlWebApplicationContext
8. 然后创建一个 Spring 容器对象,也就是子容器
9. 将 rootContext 作为 parent 设置给子容器(父子关系的绑定)

### 10. 然后读取 contextConfigLocation 参数值,得到所配置的 Spring 配置文件路径
### 11. 然后就是调用 Spring 容器的 refresh()方法
### 12. 从而完成了子容器的创建 SpringMVC 初始化子容器创建完后,还会调用一个 DispatcherServlet 的 onRefresh()方法,这个方法会从 Spring 容器中获取一些特殊类型的 Bean 对象,并设置给 DispatcherServlet 对象中对应的属性,比如 HandlerMapping、HandlerAdapter。
流程为:
1. 会先从 Spring 容器中获取 HandlerMapping 类型的 Bean 对象,如果不为空,那么就获取出来的 Bean 对象赋值给 DispatcherServlet 的 handlerMappings 属性
2. 如果没有获取到,则会从 DispatcherServlet.properties 文件中读取配置,从而得到 SpringMVC 默认给我们配置的 HandlerMappingDispatcherServlet.properties 文件内容为:

1 # Default implementation classes for DispatcherServlet's strategy interfaces.2 # Used as fallback when no matching beans are found in the DispatcherServlet context.3 # Not meant to be customized by application developers.45 org.springframework.web.servlet.LocaleResolver=org.springframework.web.servlet.i18n.AcceptHeaderLocaleResolver67 org.springframework.web.servlet.ThemeResolver=org.springframework.web.servlet.theme.FixedThemeResolver89 org.springframework.web.servlet.HandlerMapping=org.springframework.web.servlet.handler.BeanNameUrlHandlerMapping,\10 org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerMapping,\11 org.springframework.web.servlet.function.support.RouterFunctionMapping1213 org.springframework.web.servlet.HandlerAdapter=org.springframework.web.servlet.mvc.HttpRequestHandlerAdapter,\14 org.springframework.web.servlet.mvc.SimpleControllerHandlerAdapter,\15 org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerAdapter,\16 org.springframework.web.servlet.function.support.HandlerFunctionAdapter171819 org.springframework.web.servlet.HandlerExceptionResolver=org.springframework.web.servlet.mvc.method.annotation.ExceptionHandlerExceptionResolver,\20 org.springframework.web.servlet.mvc.annotation.ResponseStatusExceptionResolver,\21 org.springframework.web.servlet.mvc.support.DefaultHandlerExceptionResolver2223 org.springframework.web.servlet.RequestToViewNameTranslator=org.springframework.web.servlet.view.DefaultRequestToViewNameTranslator2425 org.springframework.web.servlet.ViewResolver=org.springframework.web.servlet.view.InternalResourceViewResolver2627 org.springframework.web.servlet.FlashMapManager=org.springframework.web.servlet.support.SessionFlashMapManager 默认提供了 3 个 HandlerMapping,4 个 HandlerAdapter,这些概念在后续 DispatcherServlet 处理请求时都是会用到的。

值得注意的是,从配置文件读出这些类后,是会利用 Spring 容器去创建出来对应的 Bean 对象,而不是一个普通的 Java 对象,而如果是 Bean 对象,那么就会触发 Bean 的初始化逻辑,比如 RequestMappingHandlerAdapter,后续在分析请求处理逻辑时,会发现这个类是非常重要的,而它就实现了 InitializingBean 接口,从而 Bean 对象在创建时会执行 afterPropertiesSet()方法。
RequestMappingHandlerAdapter 初始化我们先可以简单理解 RequestMappingHandlerAdapter,它的作用就是在收到请求时来调用请求对应的方法的,所以它需要去解析方法参数,方法返回值。
在 RequestMappingHandlerAdapter 的 afterPropertiesSet()方法中,又会做以下事情(这些事情大家可能现在看不懂,可以后面回头再来看,我先列在这):
1. 从 Spring 容器中找到加了@ControllerAdvice 的 Bean 对象 a. 解析出 Bean 对象中加了@ModelAttribute 注解的 Method 对象,并存在 modelAttributeAdviceCache 这个 Map 中 b. 解析出 Bean 对象中加了@InitBinder 注解的 Method 对象,并存在 initBinderAdviceCache 这个 Map 中 c. 如果 Bean 对象实现了 RequestBodyAdvice 接口或者 ResponseBodyAdvice 接口,那么就把这个 Bean 对象记录在 requestResponseBodyAdvice 集合中
1. 从 Spring 容器中获取用户定义的 HandlerMethodArgumentResolver,以及 SpringMVC 默认提供的,整合为一个 HandlerMethodArgumentResolverComposite 对象,HandlerMethodArgumentResolver 是用来解析方法参数的
2. 从 Spring 容器中获取用户定义的 HandlerMethodReturnValueHandler,以及 SpringMVC 默认提供的,整合为一个 HandlerMethodReturnValueHandlerComposite 对象,HandlerMethodReturnValueHandler 是用来解析方法返回值的以上是 RequestMappingHandlerAdapter 这个 Bean 的初始化逻辑。
RequestMappingHandlerMapping 初始化 RequestMappingHandlerMapping 的作用是,保存我们定义了哪些@RequestMapping 方法及对应的访问路径,而 RequestMappingHandlerMapping 的初始化就是去找到这些映射关系:
1. 找出容器中定义的所有的 beanName
2. 根据 beanName 找出 beanType
3. 判断 beanType 上是否有@Controller 注解或@RequestMapping 注解,如果有那么就表示这个 Bean 对象是一个 Handler

### 4. 如果是一个 Handler,就通过反射找出加了@RequestMapping 注解的 Method,并解析@RequestMapping 注解上定义的参数信息,得到一个对应的 RequestMappingInfo 对象,然后结合 beanType 上@RequestMapping 注解所定义的 path,以及当前 Method 上@RequestMapping 注解所定义的 path,进行整合,则得到了当前这个 Method 所对应的访问路径,并设置到 RequestMappingInfo 对象中去
### 5. 所以,一个 RequestMappingInfo 对象就对应了一个加了@RequestMapping 注解的 Method,并且请求返回路径也记录在了 RequestMappingInfo 对象中
### 6. 把当前 Handler,也就是 beanType 中的所有 RequestMappingInfo 都找到后,就会存到 MappingRegistry 对象中
### 7. 在存到 MappingRegistry 对象过程中,会像把 Handler,也就是 beanType,以及 Method,生成一个 HandlerMethod 对象,其实就是表示一个方法
### 8. 然后获取 RequestMappingInfo 对象中的 path
### 9. 把 path 和 HandlerMethod 对象存在一个 Map 中,属性叫做 pathLookup
### 10. 这样在处理请求时,就可以同请求路径找到 HandlerMethod,然后找到 Method,然后执行了 WebApplicationInitializer 的方式除开使用 web.xml 外,我们还可以直接定义一个 WebApplicationInitializer 来使用 SpringMVC,比如:
1 public class MyWebApplicationInitializer implements WebApplicationInitializer {23 @Override4 public void onStartup(ServletContext servletContext) {56 // Load Spring web application configuration7 AnnotationConfigWebApplicationContext context = newAnnotationConfigWebApplicationContext();
8 context.register(AppConfig.class);
910 // Create and register the DispatcherServlet11 DispatcherServlet servlet = new DispatcherServlet(context);
12 ServletRegistration.Dynamic registration = servletContext.addServlet("app",servlet);
13 registration.setLoadOnStartup(1);
14 registration.addMapping("/*");
15 }16 }

1 @ComponentScan("com.zhouyu")
2 @Configuration3 public class AppConfig {4 }这种方法我们也能使用 SpringMVC,流程为:
1. Tomcat 启动过程中就会调用到我们所写的 onStartup()
2. 从而创建一个 Spring 容器
3. 从而创建一个 DispatcherServlet 对象并初始化
4. 而 DispatcherServlet 初始化所做的事情和上述是一样的那为什么 Tomcat 启动时能调用到 MyWebApplicationInitializer 中的 onStartup()呢?
这个跟 Tomcat 的提供的扩展机制有关,在 SpringMVC 中有这样一个类:
1 @HandlesTypes(WebApplicationInitializer.class)
2 public class SpringServletContainerInitializer implements ServletContainerInitializer {34 @Override5 public void onStartup(@Nullable Set<Class<?>> webAppInitializerClasses,ServletContext servletContext)
6 throws ServletException {7 // ...8 }910 }这个类实现了 javax.servlet.ServletContainerInitializer 接口,并且在 SpringMVC 中还有这样一个文件:
META-INF/services/Tomcatjavax.servlet.ServletContainerInitializer,文件内容为 org.springframework.web.SpringServletContainerInitializer。

很明显,是 SPI,所以 Tomcat 在启动过程中会找到这个 SpringServletContainerInitializer,并执行 onStartup(),并且还会找到@HandlesTypes 注解中所指定的 WebApplicationInitializer 接口的实现类,并传递给 onStartup()方法,这其中就包括了我们自己定义的 MyWebApplicationInitializer。
在 SpringServletContainerInitializer 的 onStartup()中就会调用 MyWebApplicationInitializer 的 onStartup()
方法了:

1 @HandlesTypes(WebApplicationInitializer.class)
2 public class SpringServletContainerInitializer implements ServletContainerInitializer {34 @Override5 public void onStartup(@Nullable Set<Class<?>> webAppInitializerClasses,ServletContext servletContext)
6 throws ServletException {78 List<WebApplicationInitializer> initializers = Collections.emptyList();
910 if (webAppInitializerClasses != null) {11 initializers = new ArrayList<>(webAppInitializerClasses.size());
12 for (Class<?> waiClass : webAppInitializerClasses) {13 // 过滤掉接口、抽象类 14 if (!waiClass.isInterface() &&!Modifier.isAbstract(waiClass.getModifiers()) &&15WebApplicationInitializer.class.isAssignableFrom(waiClass)) {16 try {17 // 实例化 18initializers.add((WebApplicationInitializer)
19ReflectionUtils.accessibleConstructor(waiClass).newInstance());
20 }21 catch (Throwable ex) {22 throw new ServletException("Failed toinstantiate WebApplicationInitializer class", ex);
23 }24 }25 }26 }2728 if (initializers.isEmpty()) {29 servletContext.log("No Spring WebApplicationInitializer typesdetected on classpath");
30 return;
31 }3233 servletContext.log(initializers.size() + " SpringWebApplicationInitializers detected on classpath");

34 AnnotationAwareOrderComparator.sort(initializers);
35 // 调用 initializer.onStartup()
36 for (WebApplicationInitializer initializer : initializers) {37 initializer.onStartup(servletContext);
38 }39 }4041 }方法参数解析在 RequestMappingHandlerAdapter 的初始化逻辑中会设置一些默认的 HandlerMethodArgumentResolver,他们就是用来解析各种类型的方法参数的。
比如:
1. RequestParamMethodArgumentResolver,用来解析加了@RequestParam 注解的参数,或者什么都没加的基本类型参数(非基本类型的会被 ServletModelAttributeMethodProcessor 处理)
2. PathVariableMethodArgumentResolver,用来解析加了@PathVariable 注解的参数
3. RequestHeaderMethodArgumentResolver,用来解析加了@RequestHeader 注解的参数比如 RequestParamMethodArgumentResolver 中是这么处理的:
1 protected Object resolveName(String name, MethodParameter parameter, NativeWebRequestrequest) throws Exception {2 HttpServletRequest servletRequest =request.getNativeRequest(HttpServletRequest.class);
34 // ...56 if (arg == null) {7 String[] paramValues = request.getParameterValues(name);
8 if (paramValues != null) {9 arg = (paramValues.length == 1 ? paramValues[0] : paramValues);
10 }11 }12 return arg;
13 }

很简单了,就是把请求中对应的 parameterValue 拿出来,最为参数值传递给方法。
其他的类似,都是从请求中获取相对应的信息传递给参数。
但是需要注意的是,我们从请求中获取的值可能很多时候都是字符串,那如果参数类型不是 String,该怎么办呢?这就需要进行类型转换了,比如代码是这么写的:
1 @RequestMapping(method = RequestMethod.GET, path = "/test")
2 @ResponseBody3 public String test(@RequestParam User user) {4 System.out.println(user.getName());
5 return "hello zhouyu";
6 }表示要获取请求中 user 对应的 parameterValue,但是我们发请求时是这么发的:
1http://localhost:8080/tuling-web/app/test?user=zhouyu 那么 SpringMVC 就需要将字符串 zhouyu 转换成为 User 对象,这就需要我们自定义类型转换器了,比如:

1 /**2 * 作者:周瑜大都督 3 */4 public class StringToUserEditor extends PropertyEditorSupport {56 @Override7 public void setAsText(String text) throws IllegalArgumentException {8 User user = new User();
9 user.setName(text);
10 this.setValue(user);
11 }12 }1 @InitBinder2 public void initBinder(WebDataBinder binder) {3 binder.registerCustomEditor(User.class, new StringToUserEditor());
4 }Spring 默认提供的 Converter:
org.springframework.core.convert.support.DefaultConversionService#addCollectionConvertersMultipartFile 解析文件上传代码如下:
1 @RequestMapping(method = RequestMethod.POST, path = "/test")
2 @ResponseBody3 public String test(MultipartFile file) {4 System.out.println(file.getName());
5 return "hello zhouyu";
6 }

要理解 SpringMVC 的文件上传,我们得先回头看看直接基于 Servlet 的文件上传,代码如下:

1 @WebServlet(name = "uploadFileServlet", urlPatterns = "/uploadFile")
2 @MultipartConfig3 public class UploadFileServlet extends HttpServlet {45 public void doPost(HttpServletRequest request, HttpServletResponse response)
throws ServletException, IOException {67 Collection<Part> parts = request.getParts();
89 for (Part part : parts) {10 //content-disposition 对于的内容为:form-data; name="file";
filename="zhouyu.xlsx"
11 String header = part.getHeader("content-disposition");
1213 String fileName = getFileName(header);
1415 if (fileName != null) {16 part.write("D://upload" + File.separator + fileName);
17 } else {18 System.out.println(part.getName());
19 }2021 }2223 response.setCharacterEncoding("utf-8");
24 response.setContentType("text/html;charset=utf-8");
25 PrintWriter out = response.getWriter();
26 out.println("上传成功");
27 out.flush();
28 out.close();
29 }3031 public String getFileName(String header) {32 String[] arr = header.split(";");
33 if (arr.length < 3) return null;
34 String[] arr2 = arr[2].split("=");
35 String fileName = arr2[1].substring(arr2[1].lastIndexOf("\\") +1).replaceAll("\"", "");
36 return fileName;
37 }

3839 }可以看到第一行代码是:
1 Collection<Part> parts = request.getParts();
从 request 中拿到了一个 Part 集合,而这个集合中 Part 可以表示一个文件,也可以表示一个字符串。
比如发送这么一个请求:
那么这个请求中就会有两个 Part,一个 Part 表示文件,一个 Part 表示文本。
有了这个知识点,我们再来看 Controller 中的代码:
1 @RequestMapping(method = RequestMethod.POST, path = "/test")
2 @ResponseBody3 public String test(MultipartFile file, String test) {4 System.out.println(file.getName());
5 System.out.println(test);
6 return "hello zhouyu";
7 }方法中的两个参数分别表示:

### 1. file 对应的是文件 Part
### 2. test 对应的就是文本 Part 那有同学可能会有疑问,假如我请求是这么发的呢:
表达里面的 test=tuling,请求 parameter 中的 test=zhouyu,那最终 test 等于哪个呢?
答案是两个:

那如果我只想获取表达里的 test 呢?可以用@RequestPart 注解:
当接收到一个请求后:
1. SpringMVC 利用 MultipartResolver 来判断当前请求是不是一个 multipart/form-data 请求
2. 如果是会把这个请求封装为 StandardMultipartHttpServletRequest 对象
3. 并且获取请求中所有的 Part,并且遍历每个 Part
4. 判断 Part 是文件还是文本
5. 如果是文件,会把 Part 封装为一个 StandardMultipartFile 对象(实现了 MultipartFile 接口),并且会把 StandardMultipartFile 对象添加到 multipartFiles 中
6. 如果是文本,会把 Part 的名字添加到 multipartParameterNames 中
7. 然后在解析某个参数时
8. 如果参数类型是 MultipartFile,会根据参数名字从 multipartFiles 中获取出 StandardMultipartFile 对象,最终把这个对象传给方法方法返回值解析在 RequestMappingHandlerAdapter 的初始化逻辑中会设置一些默认的 HandlerMethodReturnValueHandler,他们就是用来解析各种类型的方法返回值的。
比如:
1. ModelAndViewMethodReturnValueHandler,处理的就是返回值类为 ModelAndView 的情况
2. RequestResponseBodyMethodProcessor,处理的就是方法上或类上加了@ResponseBody 的情况

### 3. ViewNameMethodReturnValueHandler,处理的就是返回值为字符串的请求(无@ResponseBody)
我们重点看 RequestResponseBodyMethodProcessor。
假如代码如下:
1 @Controller2 public class ZhouyuController {34 @RequestMapping(method = RequestMethod.GET, path = "/test")
5 @ResponseBody6 public User test() {7 User user = new User();
8 user.setName("zhouyu");
9 return user;
10 }1112 }方法返回的是 User 对象,那么怎么把这个 User 对象返回给浏览器来展示呢?那得看当前请求设置的 Accept 请求头,比如我用 Chrome 浏览器发送请求,默认给我设置的就是:Accept:
text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9 表示当前这个请求接收的内容格式,比如 html 格式、 xml 格式、各种图片格式等等。
如果我们的方法返回的是一个字符串,那么就对应 html 格式,就没问题,而如果我们不是返回的字符串,那我们就转成字符串,通常就是 JSON 格式的字符串。
所以,我们需要将 User 对象转换成 JSON 字符串,默认 SpringMVC 是不能转换的,此时请求会报错:
而要完成这件事情,我们需要添加一个 MappingJackson2HttpMessageConverter,通过它就能把 User 对象或者 Map 对象等转成一个 JSON 字符串。

XML 的添加方式:
1 <mvc:annotation-driven>2 <mvc:message-converters>3 <beanclass="org.springframework.http.converter.json.MappingJackson2HttpMessageConverter"/>4 </mvc:message-converters>5 </mvc:annotation-driven>记得要引入 Jackson2 的依赖:
1 <!https://mvnrepository.com/artifact/com.fasterxml.jackson.core/jackson-databind<!2 <dependency>3 <groupId>com.fasterxml.jackson.core</groupId>4 <spanrtifactId>jackson-databind</artifactId>5 <version>2.13.2</version>6 </dependency>7 我们看一下 MappingJackson2HttpMessageConverter 的构造方法:
1 public MappingJackson2HttpMessageConverter() {2 this(Jackson2ObjectMapperBuilder.json().build());
3 }456 public MappingJackson2HttpMessageConverter(ObjectMapper objectMapper) {7 super(objectMapper, MediaType.APPLICATION_JSON, new MediaType("application","*+json"));
8 }

表示 MappingJackson2HttpMessageConverter 支持的 MediaType 为"application/json"、"application/*+json"。
所以如果我们明确指定方法返回的 MediaType 为"text/plain",那么 MappingJackson2HttpMessageConverter 就不能处理了,比如:
1 @RequestMapping(method = RequestMethod.GET, path = "/test", produces = "text/plain")
2 @ResponseBody3 public User test() {4 User user = new User();
5 user.setName("zhouyu");
6 return user;
7 }以上代码表示,需要把一个 User 对象转成一个纯文本字符串,默认是没有这种转换器的。
一个 HttpMessageConverter 中有一个 canWrite()方法,表示这个 HttpMessageConverter 能把什么类型转成什么 MediaType 返回给浏览器。
比如 SpringMVC 自带一个 StringHttpMessageConverter,它能够把一个 String 对象返回给浏览器,支持所有的 MediaType。
那为了支持把 User 对象转成纯文本,我们可以自定义 ZhouyuHttpMessageConverter:

1 /**2 * 作者:周瑜大都督 3 */4 public class ZhouyuHttpMessageConverter extends AbstractHttpMessageConverter<User> {56 @Override7 public List<MediaType> getSupportedMediaTypes() {8 ArrayList<MediaType> mediaTypes = new ArrayList<>();
9 mediaTypes.add(MediaType.ALL);
10 return mediaTypes;
11 }1213 @Override14 protected boolean supports(Class clazz) {15 return User.class == clazz;
16 }1718 @Override19 protected User readInternal(Class<? extends User> clazz, HttpInputMessageinputMessage) throws IOException, HttpMessageNotReadableException {20 return null;
21 }2223 @Override24 protected void writeInternal(User user, HttpOutputMessage outputMessage)
throws IOException, HttpMessageNotWritableException {25 StreamUtils.copy(user.getName(), Charset.defaultCharset(),outputMessage.getBody());
26 }27 }我定义的这个 HttpMessageConverter 就能够把 User 对象转成纯文本。
拦截器解析我们可以使用 HandlerInterceptor 来拦截请求:

1 package org.springframework.web.servlet;
23 import javax.servlet.http.HttpServletRequest;
4 import javax.servlet.http.HttpServletResponse;
56 import org.springframework.lang.Nullable;
7 import org.springframework.web.method.HandlerMethod;
89 public interface HandlerInterceptor {1011 default boolean preHandle(HttpServletRequest request, HttpServletResponseresponse, Object handler)
12 throws Exception {1314 return true;
15 }161718 default void postHandle(HttpServletRequest request, HttpServletResponseresponse, Object handler,19 @Nullable ModelAndView modelAndView) throws Exception {20 }212223 default void afterCompletion(HttpServletRequest request, HttpServletResponseresponse, Object handler,24 @Nullable Exception ex) throws Exception {25 }2627 }28 具体执行顺序看下图:
1 @Retention(RetentionPolicy.RUNTIME)
2 @Target(ElementType.TYPE)
3 @Documented4 @Import(DelegatingWebMvcConfiguration.class)
5 public @interface EnableWebMvc {6 }导入了一个 DelegatingWebMvcConfiguration 配置类,这个配置类定义了很多个 Bean,比如 RequestMappingHandlerMapping,后续在创建 RequestMappingHandlerMapping 这个 Bean 对象时,会调用 DelegatingWebMvcConfiguration 的 getInterceptors()方法来获取拦截器:
1 @Bean2 @SuppressWarnings("deprecation")
3 public RequestMappingHandlerMapping requestMappingHandlerMapping(...) {45 RequestMappingHandlerMapping mapping = createRequestMappingHandlerMapping();
6 mapping.setInterceptors(getInterceptors(conversionService, resourceUrlProvider));
7 // ...8 return mapping;
9 }而在 getInterceptors()方法中会调用 addInterceptors()方法,从而会调用 WebMvcConfigurerComposite 的 addInterceptors()方法,然后会遍历调用 WebMvcConfigurer 的 addInterceptors()方法来添加拦截器:
1 public void addInterceptors(InterceptorRegistry registry) {2 for (WebMvcConfigurer delegate : this.delegates) {3 delegate.addInterceptors(registry);
4 }5 }那么 delegates 集合中的值是哪来的呢?在 DelegatingWebMvcConfiguration 中进行了一次 set 注入:

1 @Autowired(required = false)
2 public void setConfigurers(List<WebMvcConfigurer> configurers) {3 if (!CollectionUtils.isEmpty(configurers)) {4 this.configurers.addWebMvcConfigurers(configurers);
5 }6 }78 public void addWebMvcConfigurers(List<WebMvcConfigurer> configurers) {9 if (!CollectionUtils.isEmpty(configurers)) {10 this.delegates.addAll(configurers);
11 }12 }所以就是把 Spring 容器中的 WebMvcConfigurer 的 Bean 添加到了 delegates 集合中。
所以,我们可以配置 WebMvcConfigurer 类型的 Bean,并通过 addInterceptors()方法来给 SpringMvc 添加拦截器。
同理我们可以利用 WebMvcConfigurer 中的其他方法来对 SpringMvc 进行配置,比如 1 @ComponentScan("com.zhouyu")
2 @Configuration3 @EnableWebMvc4 public class AppConfig implements WebMvcConfigurer {56 @Override7 public void configurePathMatch(PathMatchConfigurer configurer) {8 configurer.addPathPrefix("/zhouyu", t -> t.equals(ZhouyuController.class));
9 }1011 @Override12 public void addInterceptors(InterceptorRegistry registry) {1314 }15 }

所以@EnableWebMvc 的作用是提供了可以让程序员通过定义 WebMvcConfigurer 类型的 Bean 来对 SpringMVC 进行配置的功能。
另外值得注意的是,如果加了@EnableWebMvc 注解,那么 Spring 容器中会有三个 HandlerMapping 类型的 Bean:
1. RequestMappingHandlerMapping
2. BeanNameUrlHandlerMapping
3. RouterFunctionMapping 如果没有加@EnableWebMvc 注解,那么 Spring 容器中默认也会有三个 HandlerMapping 类型的 Bean:
1. BeanNameUrlHandlerMapping
2. RequestMappingHandlerMapping
3. RouterFunctionMapping 就顺序不一样而已,源码中是根据 DispatcherServlet.properties 文件来配置有哪些 HandlerMapping 的。

1 private void initHandlerMappings(ApplicationContext context) {2 this.handlerMappings = null;
34 // 默认为 true,获取 HandlerMapping 类型的 Bean5 if (this.detectAllHandlerMappings) {6 // Find all HandlerMappings in the ApplicationContext,including ancestor contexts.7 Map<String, HandlerMapping> matchingBeans =8BeanFactoryUtils.beansOfTypeIncludingAncestors(context, HandlerMapping.class, true,false);
9 if (!matchingBeans.isEmpty()) {10 this.handlerMappings = new ArrayList<>(matchingBeans.values());
11 // We keep HandlerMappings in sorted order.12AnnotationAwareOrderComparator.sort(this.handlerMappings);
13 }14 }15 // 获取名字叫 handlerMapping 的 Bean16 else {17 try {18 HandlerMapping hm =context.getBean(HANDLER_MAPPING_BEAN_NAME, HandlerMapping.class);
19 this.handlerMappings = Collections.singletonList(hm);
20 }21 catch (NoSuchBeanDefinitionException ex) {22 // Ignore, we'll add a default HandlerMapping later.23 }24 }2526 // 如果从 Spring 容器中没有找到 HandlerMapping 类型的 Bean27 // 就根据 DispatcherServlet.properties 配置来创建 HandlerMapping 类型的 Bean28 // 默认就有这么一个文件,会创建出来三个 HandlerMapping 的 Bean29 if (this.handlerMappings == null) {30 this.handlerMappings = getDefaultStrategies(context,HandlerMapping.class);
31 if (logger.isTraceEnabled()) {32 logger.trace("No HandlerMappings declared for servlet'" + getServletName() +33 "': using default strategies fromDispatcherServlet.properties");

34 }35 }3637 for (HandlerMapping mapping : this.handlerMappings) {38 if (mapping.usesPathPatterns()) {39 this.parseRequestPath = true;
40 break;
41 }42 }43 }由于加和不加@EnableWebMvc 注解之后的 HandlerMapping 顺序不一样,可能会导致一些问题(工作中很难遇到):
1 @Component("/test")
2 public class BeanNameUrlController implements Controller {3 @Override4 public ModelAndView handleRequest(HttpServletRequest request,HttpServletResponse response) throws Exception {5 System.out.println("BeanNameUrlController");
6 return null;
7 }8 }

1 @RestController2 public class ZhouyuController {34 @GetMapping("/test")
5 public String test() {6 System.out.println("ZhouyuController");
7 return null;
8 }910 }这两个 Controller 访问路径是一样的,但是负责处理的 HandlerMapping 是不一样的,
1. BeanNameUrlController 对应的是 BeanNameUrlHandlerMapping
2. ZhouyuController 对应的是 RequestMappingHandlerMapping 如果加了@EnableWebMvc 注解,顺序为:
1. RequestMappingHandlerMapping
2. BeanNameUrlHandlerMapping
3. RouterFunctionMapping 会先由 RequestMappingHandlerMapping 处理/test 请求,最终执行的是 ZhouyuController 中的 test 如果没有加@EnableWebMvc 注解,顺序为:
1. BeanNameUrlHandlerMapping
2. RequestMappingHandlerMapping
3. RouterFunctionMapping 会先由 BeanNameUrlHandlerMapping 处理/test 请求,最终执行的是 BeanNameUrlController 中的 test 注意,一个 HandlerMapping 处理完请求后就不会再让其他 HandlerMapping 来处理请求了。
