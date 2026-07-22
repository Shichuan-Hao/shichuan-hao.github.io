---


title: "Spring 6.0及SpringBoot 3.0新特性解析"
description: "课程内容: 1、GraalVM 介绍与基本使用 2、Spring Boot 3.0 新特性介绍与实战 3、Docker SpringBoot3.0 新特性实战"
author: hsc
date: 2022-07-24 00:00:00 +0800
categories: ['Java 后端', '框架源码']
tags: ['Spring', 'MyBatis', 'IOC', 'AOP', 'SpringBoot']
toc: true


---

课程内容:
1、GraalVM 介绍与基本使用 2、Spring Boot 3.0 新特性介绍与实战 3、Docker SpringBoot3.0 新特性实战 4、RuntimeHints 介绍与实战 5、Spring AOT 作用与核心原理源码分析 17-Spring 6.0 及 SpringBoot 3.0 新特性解析

GraalVM 体验 https://github.com/spring-projects/spring-framework/wiki/What%27s-New-in-Spring-Framework-6.x 最核心的就是 Spring AOT。
GraalVM 文章推荐:https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzI3MDI5MjI1Nw==&action=getalbum&album_id=2761361634840969217&scene=173&from_msgid=2247484273&from_itemidx=1&count=3&nolastread=1#wechat_redirect 下载压缩包打开 https://github.com/graalvm/graalvm-ce-builds/releases,按 JDK 版本下载 GraalVM 对应的压缩包,请下载 Java 17 对应的版本,不然后面运行 SpringBoot3 可能会有问题。
下载完后,就解压,

配置环境变量新开一个 cmd 测试:

安装 Visual Studio Build Tools 因为需要 C 语言环境,所以需要安装 Visual Studio Build Tools。
打开 visualstudio.microsoft.com,下载 Visual Studio Installer。
选择 C++桌面开发,和 Windows 11 SDK,然后进行下载和安装,安装后重启操作系统。

要使用 GraalVM,不能使用普通的 windows 自带的命令行窗口,得使用 VS 提供的 x64 Native ToolsCommand Prompt for VS 2019,如果没有可以执行 C:\Program Files (x86)\MicrosoftVisual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat 脚本来安装。
安装完之后其实就可以在 x64 Native Tools Command Prompt for VS 2019 中去使用 nativeimage 命令去进行编译了。
但是,如果后续在编译过程中编译失败了,出现以下错误:
那么可以执行 cl.exe,如果是中文,那就得修改为英文。
通过 Visual Studio Installer 来修改,比如:

可能一开始只选择了中文,手动选择英文,去掉中文,然后安装即可。
再次检查这样就可以正常的编译了。
Hello World 实战新建一个简单的 Java 工程:

我们可以直接把 graalvm 当作普通的 jdk 的使用我们也可以利用 native-image 命令来将字节码编译为二进制可执行文件。
打开 x64 Native Tools Command Prompt for VS 2019,进入工程目录下,并利用 javac 将 java 文件编译为 class 文件:javac -d . src/com/zhouyu/App.java

此时的 class 文件因为有 main 方法,所以用 java 命令可以运行我们也可以利用 native-image 来编译:
编译需要一些些。。。。。。。时间。

编译完了之后就会在当前目录生成一个 exe 文件:
我们可以直接运行这个 exe 文件:

并且运行这个 exe 文件是不需要操作系统上安装了 JDK 环境的。
我们可以使用-o 参数来指定 exe 文件的名字:
1 native-image com.zhouyu.App -o appGraalVM 的限制 GraalVM 在编译成二进制可执行文件时,需要确定该应用到底用到了哪些类、哪些方法、哪些属性,从而把这些代码编译为机器指令(也就是 exe 文件)。但是我们一个应用中某些类可能是动态生成的,也就是应用运行后才生成的,为了解决这个问题,GraalVM 提供了配置的方式,可以让我们在编译时告诉 GraalVM 哪些类会动态生成类,比如我们可以通过 proxy-config.json、reflect-config.json 来进行配置。
SpringBoot 3.0 实战然后新建一个 Maven 工程,添加 SpringBoot 依赖 1 <parent>2 <groupId>org.springframework.boot</groupId>3 <spanrtifactId>spring-boot-starter-parent</artifactId>4 <version>3.0.0</version>5 </parent>67 <dependencies>8 <dependency>9 <groupId>org.springframework.boot</groupId>10 <spanrtifactId>spring-boot-starter-web</artifactId>11 </dependency>12 </dependencies>以及 SpringBoot 的插件

1 <build>2 <plugins>3 <plugin>4 <groupId>org.graalvm.buildtools</groupId>5 <spanrtifactId>native-maven-plugin</artifactId>6 </plugin>7 <plugin>8 <groupId>org.springframework.boot</groupId>9 <spanrtifactId>spring-boot-maven-plugin</artifactId>10 </plugin>11 </plugins>12 </build>以及一些代码 1 @RestController2 public class ZhouyuController {34 @Autowired5 private UserService userService;
67 @GetMapping("/demo")
8 public String test() {9 return userService.test();
10 }1112 }

1 package com.zhouyu;
23 import org.springframework.stereotype.Component;
45 @Component6 public class UserService {78 public String test(){9 return "hello zhouyu";
10 }11 }121 package com.zhouyu;
23 import org.springframework.boot.SpringApplication;
4 import org.springframework.boot.autoconfigure.SpringBootApplication;
56 @SpringBootApplication7 public class MyApplication {8 public static void main(String[] args) {9 SpringApplication.run(MyApplication.class, args);
10 }11 }12 这本身就是一个普通的 SpringBoot 工程,所以可以使用我们之前的方式使用,同时也支持利用 nativeimage 命令把整个 SpringBoot 工程编译成为一个 exe 文件。
同样在 x64 Native Tools Command Prompt for VS 2019 中,进入到工程目录下,执行 mvn Pnative native:compile 进行编译就可以了,就能在 target 下生成对应的 exe 文件,后续只要运行 exe 文件就能启动应用了。
在执行命令之前,请确保环境变量中设置的时 graalvm 的路径。

编译完成截图:

这样,我们就能够直接运行这个 exe 来启动我们的 SpringBoot 项目了。
Docker SpringBoot3.0 实战我们可以直接把 SpringBoot 应用对应的本地可执行文件构建为一个 Docker 镜像,这样就能跨操作系统运行了。
Buildpacks,类似 Dockerfile 的镜像构建技术注意要安装 docker,并启动 docker 注意这种方式并不要求你机器上安装了 GraalVM,会由 SpringBoot 插件利用/paketo-buildpacks/nativeimage 来生成本地可执行文件,然后打入到容器中 Docker 镜像名字中不能有大写字母,我们可以配置镜像的名字:
1 <properties>2 <maven.compiler.source>17</maven.compiler.source>3 <maven.compiler.target>17</maven.compiler.target>4 <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>5 <spring-boot.build-image.imageName>springboot3demo</spring-boot.buildimage.imageName>6 </properties>然后执行:
1 mvn -Pnative spring-boot:build-image 来生成 Docker 镜像,成功截图:

执行完之后,就能看到 docker 镜像了:
然后就可以运行容器了:
1 docker run --rm -p 8080:8080 springboot3demo 如果要传参数,可以通过-e1 docker run --rm -p 8080:8080 -e methodName=test springboot3demo 不过代码中,得通过以下代码获取:
1 String methodName = System.getenv("methodName")

建议工作中直接使用 Environment 来获取参数:
RuntimeHints 假如应用中有如下代码:
1 /**2 * 作者:周瑜大都督 3 */4 public class ZhouyuService {56 public String test(){7 return "zhouyu";
8 }9 }

1 @Component2 public class UserService {34 public String test(){56 String result = "";
7 try {8 Method test = ZhouyuService.class.getMethod("test", null);
9 result = (String) test.invoke(ZhouyuService.class.newInstance(), null);
10 } catch (NoSuchMethodException e) {11 throw new RuntimeException(e);
12 } catch (InvocationTargetException e) {13 throw new RuntimeException(e);
14 } catch (IllegalAccessException e) {15 throw new RuntimeException(e);
16 } catch (InstantiationException e) {17 throw new RuntimeException(e);
18 }1920 return result;
21 }2223 }在 UserService 中,通过反射的方式使用到了 ZhouyuService 的无参构造方法(ZhouyuService.class.newInstance()),如果我们不做任何处理,那么打成二进制可执行文件后是运行不了的,可执行文件中是没有 ZhouyuService 的无参构造方法的,会报如下错误:

我们可以通过 Spring 提供的 Runtime Hints 机制来间接的配置 reflect-config.json。
方式一:RuntimeHintsRegistrar 提供一个 RuntimeHintsRegistrar 接口的实现类,并导入到 Spring 容器中就可以了:

1 @Component2 @ImportRuntimeHints(UserService.ZhouyuServiceRuntimeHints.class)
3 public class UserService {45 public String test(){67 String result = "";
8 try {9 Method test = ZhouyuService.class.getMethod("test", null);
10 result = (String) test.invoke(ZhouyuService.class.newInstance(), null);
11 } catch (NoSuchMethodException e) {12 throw new RuntimeException(e);
13 } catch (InvocationTargetException e) {14 throw new RuntimeException(e);
15 } catch (IllegalAccessException e) {16 throw new RuntimeException(e);
17 } catch (InstantiationException e) {18 throw new RuntimeException(e);
19 }202122 return result;
23 }2425 static class ZhouyuServiceRuntimeHints implements RuntimeHintsRegistrar {2627 @Override28 public void registerHints(RuntimeHints hints, ClassLoader classLoader) {29 try {30hints.reflection().registerConstructor(ZhouyuService.class.getConstructor(),ExecutableMode.INVOKE);
31 } catch (NoSuchMethodException e) {32 throw new RuntimeException(e);
33 }34 }35 }36 }

方式二:@RegisterReflectionForBinding1 @RegisterReflectionForBinding(ZhouyuService.class)
2 public String test(){34 String result = "";
5 try {6 Method test = ZhouyuService.class.getMethod("test", null);
7 result = (String) test.invoke(ZhouyuService.class.newInstance(), null);
8 } catch (NoSuchMethodException e) {9 throw new RuntimeException(e);
10 } catch (InvocationTargetException e) {11 throw new RuntimeException(e);
12 } catch (IllegalAccessException e) {13 throw new RuntimeException(e);
14 } catch (InstantiationException e) {15 throw new RuntimeException(e);
16 }171819 return result;
20 }注意如果代码中的 methodName 是通过参数获取的,那么 GraalVM 在编译时就不能知道到底会使用到哪个方法,那么 test 方法也要利用 RuntimeHints 来进行配置。

1 @Component2 @ImportRuntimeHints(UserService.ZhouyuServiceRuntimeHints.class)
3 public class UserService {45 public String test(){67 String methodName = System.getProperty("methodName");
89 String result = "";
10 try {11 Method test = ZhouyuService.class.getMethod(methodName, null);
12 result = (String) test.invoke(ZhouyuService.class.newInstance(), null);
13 } catch (NoSuchMethodException e) {14 throw new RuntimeException(e);
15 } catch (InvocationTargetException e) {16 throw new RuntimeException(e);
17 } catch (IllegalAccessException e) {18 throw new RuntimeException(e);
19 } catch (InstantiationException e) {20 throw new RuntimeException(e);
21 }222324 return result;
25 }2627 static class ZhouyuServiceRuntimeHints implements RuntimeHintsRegistrar {2829 @Override30 public void registerHints(RuntimeHints hints, ClassLoader classLoader) {31 try {32hints.reflection().registerConstructor(ZhouyuService.class.getConstructor(),ExecutableMode.INVOKE);
33hints.reflection().registerMethod(ZhouyuService.class.getMethod("test"),ExecutableMode.INVOKE);
34 } catch (NoSuchMethodException e) {35 throw new RuntimeException(e);
36 }37 }

38 }39 }或者使用了 JDK 动态代理:
1 public String test() throws ClassNotFoundException {23 String className = System.getProperty("className");
4 Class<?> aClass = Class.forName(className);
56 Object o = Proxy.newProxyInstance(UserService.class.getClassLoader(), newClass[]{aClass}, new InvocationHandler() {7 @Override8 public Object invoke(Object proxy, Method method, Object[] args) throwsThrowable {9 return method.getName();
10 }11 });
1213 return o.toString();
14 }那么也可以利用 RuntimeHints 来进行配置要代理的接口:
1 public void registerHints(RuntimeHints hints, ClassLoader classLoader) {2 hints.proxies().registerJdkProxy(UserInterface.class);
3 }方式三:@Reflective 对于反射用到的地方,我们可以直接加一个@Reflective,前提是 ZhouyuService 得是一个 Bean:

1 @Component2 public class ZhouyuService {34 @Reflective5 public ZhouyuService() {6 }78 @Reflective9 public String test(){10 return "zhouyu";
11 }12 }以上 Spring6 提供的 RuntimeHints 机制,我们可以使用该机制更方便的告诉 GraalVM 我们额外用到了哪些类、接口、方法等信息,最终 Spring 会生成对应的 reflect-config.json、proxy-config.json 中的内容,GraalVM 就知道了。
Spring AOT 的源码实现流程图:https://www.processon.com/view/link/63edeea8440e433d3d6a88b2SpringBoot 3.0 插件实现原理上面的 SpringBoot3.0 实战过程中,我们在利用 image-native 编译的时候,target 目录下会生成一个 spring-aot 文件夹:

这个 spring-aot 文件夹是编译的时候 spring boot3.0 的插件生成的,resources/META-INF/native-image 文件夹中的存放的就是 graalvm 的配置文件。
当我们执行 mvn -Pnative native:compile 时,实际上执行的是插件 native-maven-plugin 的逻辑。
我们可以执行 mvn help:describe -Dplugin=org.graalvm.buildtools:native-mavenplugin -Ddetail 来查看这个插件的详细信息。

发现 native:compile 命令对应的实现类为 NativeCompileMojo,并且会先执行 package 这个命令,从而会执行 process-aot 命令,因为 spring-boot-maven-plugin 插件中有如下配置:

我们可以执行 mvn help:describe -Dplugin=org.springframework.boot:spring-bootmaven-plugin -Ddetail 发现对应的 phase 为:prepare-package,所以会在打包之前执行 ProcessAotMojo。
所以,我们在运行 mvn -Pnative native:compile 时,会先编译我们自己的 java 代码,然后执行 executeAot()方法(会生成一些 Java 文件并编译成 class 文件,以及 GraalVM 的配置文件),然后才执行利用 GraalVM 打包出二进制可执行文件。
对应的源码实现:

maven 插件在编译的时候,就会调用到 executeAot()这个方法,这个方法会:
1. 先执行 org.springframework.boot.SpringApplicationAotProcessor 的 main 方法
2. 从而执行 SpringApplicationAotProcessor 的 process()
3. 从而执行 ContextAotProcessor 的 doProcess(),从而会生成一些 Java 类并放在 spring-aot/main/sources 目录下,
详情看后文
4. 然后把生成在 spring-aot/main/sources 目录下的 Java 类进行编译,并把对应 class 文件放在项目的编译目录下 target/classes
5. 然后把 spring-aot/main/resources 目录下的 graalvm 配置文件复制到 target/classes
6. 然后把 spring-aot/main/classes 目录下生成的 class 文件复制到 target/classesSpring AOT 核心原理以下只是一些关键源码,详细内容请看直播视频。
prepareApplicationContext 会直接启动我们的 SpringBoot,并在触发 contextLoaded 事件后,返回所创建的 Spring 对象,注意此时还没有扫描 Bean。

1 protected ClassName performAotProcessing(GenericApplicationContext applicationContext)
{2 FileSystemGeneratedFiles generatedFiles = createFileSystemGeneratedFiles();
34 DefaultGenerationContext generationContext = newDefaultGenerationContext(createClassNameGenerator(), generatedFiles);
56 ApplicationContextAotGenerator generator = newApplicationContextAotGenerator();
78 // 会进行扫描,并且根据扫描得到的 BeanDefinition 生成对应的 Xx_BeanDefinitions.java 文件 9 // 并返回 com.zhouyu.MyApplication__ApplicationContextInitializer10 ClassName generatedInitializerClassName =generator.processAheadOfTime(applicationContext, generationContext);
1112 // 因为后续要通过反射调用 com.zhouyu.MyApplication__ApplicationContextInitializer 的构造方法 13 // 所以将相关信息添加到 reflect-config.json 对应的 RuntimeHints 中去 14 registerEntryPointHint(generationContext, generatedInitializerClassName);
1516 // 生成 source 目录下的 Java 文件 17 generationContext.writeGeneratedContent();
1819 // 将 RuntimeHints 中的内容写入 resource 目录下的 Graalvm 的各个配置文件中 20 writeHints(generationContext.getRuntimeHints());
21writeNativeImageProperties(getDefaultNativeImageArguments(getApplicationClass().getName()));
2223 return generatedInitializerClassName;
24 }

1 public ClassName processAheadOfTime(GenericApplicationContext applicationContext,2GenerationContext generationContext) {3 return withCglibClassHandler(new CglibClassHandler(generationContext), () -> {45 // 会进行扫描,并找到 beanType 是代理类的请求,把代理类信息设置到 RuntimeHints 中 6applicationContext.refreshForAotProcessing(generationContext.getRuntimeHints());
78 // 拿出 Bean 工厂,扫描得到的 BeanDefinition 对象在里面 9 DefaultListableBeanFactory beanFactory =applicationContext.getDefaultListableBeanFactory();
1011 ApplicationContextInitializationCodeGenerator codeGenerator =12 newApplicationContextInitializationCodeGenerator(generationContext);
1314 // 核心 15 newBeanFactoryInitializationAotContributions(beanFactory).applyTo(generationContext,codeGenerator);
1617 return codeGenerator.getGeneratedClass().getName();
18 });
19 }1 BeanFactoryInitializationAotContributions(DefaultListableBeanFactory beanFactory) {2 // 把 aot.factories 文件的加载器以及 BeanFactory,封装成为一个 Loader 对象,然后传入 3 this(beanFactory, AotServices.factoriesAndBeans(beanFactory));
4 }

1 BeanFactoryInitializationAotContributions(DefaultListableBeanFactory beanFactory,2AotServices.Loader loader) {34 // getProcessors()中会从 aot.factories 以及 beanfactory 中拿出 BeanFactoryInitializationAotProcessor 类型的 Bean 对象 5 // 同时还会添加一个 RuntimeHintsBeanFactoryInitializationAotProcessor6 this.contributions = getContributions(beanFactory, getProcessors(loader));
7 }1 private List<BeanFactoryInitializationAotContribution> getContributions(2 DefaultListableBeanFactory beanFactory,3 List<BeanFactoryInitializationAotProcessor> processors) {45 List<BeanFactoryInitializationAotContribution> contributions = new ArrayList<>();
67 // 逐个调用 BeanFactoryInitializationAotProcessor 的 processAheadOfTime()开始处理 8 for (BeanFactoryInitializationAotProcessor processor : processors) {9 BeanFactoryInitializationAotContribution contribution =processor.processAheadOfTime(beanFactory);
10 if (contribution != null) {11 contributions.add(contribution);
12 }13 }14 return Collections.unmodifiableList(contributions);
15 }总结一下,在 SpringBoot 项目编译时,最终会通过 BeanFactoryInitializationAotProcessor 来生成 Java 文件,或者设置 RuntimeHints,后续会把写入 Java 文件到磁盘,将 RuntimeHints 中的内容写入 GraalVM 的配置文件,再后面会编译 Java 文件,再后面就会基于生成出来的 GraalVM 配置文件打包出二进制可执行文件了。
所以我们要看 Java 文件怎么生成的,RuntimeHints 如何收集的就看具体的 BeanFactoryInitializationAotProcessor 就行了。

比如:
1. 有一个 BeanRegistrationsAotProcessor,它就会负责生成 Xx_BeanDefinition.java 以及 Xx__ApplicationContextInitializer.java、Xx__BeanFactoryRegistrations.java 中的内容
2. 还有一个 RuntimeHintsBeanFactoryInitializationAotProcessor,它负责从 aot.factories 文件以及 BeanFactory 中获取 RuntimeHintsRegistrar 类型的对象,以及会找到@ImportRuntimeHints 所导入的 RuntimeHintsRegistrar 对象,
最终就是从这些 RuntimeHintsRegistrar 中设置 RuntimeHints。
Spring Boot3.0 启动流程在 run()方法中,SpringBoot 会创建一个 Spring 容器,但是 SpringBoot3.0 中创建容器逻辑为:
1 private ConfigurableApplicationContext createContext() {2 if (!AotDetector.useGeneratedArtifacts()) {3 return new AnnotationConfigServletWebServerApplicationContext();
4 }5 return new ServletWebServerApplicationContext();
6 }如果没有使用 AOT,那么就会创建 AnnotationConfigServletWebServerApplicationContext,它里面会添加 ConfigurationClassPostProcessor,从而会解析配置类,从而会扫描。
而如果使用了 AOT,则会创建 ServletWebServerApplicationContext,它就是一个空容器,它里面没有 ConfigurationClassPostProcessor,所以后续不会触发扫描了。
创建完容器后,就会找到 MyApplication__ApplicationContextInitializer,开始向容器中注册 BeanDefinition。
后续就是创建 Bean 对象了。
