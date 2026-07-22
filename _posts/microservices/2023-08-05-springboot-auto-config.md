---

title: "SpringBoot自动配置底层源码解析"
description: "课程内容: 1. @EnableAutoConfiguration 源码解析 2. SpringBoot 常用条件注解源码解析 3."
author: hsc
date: 2023-08-05 00:00:00 +0800
categories: ['Java 后端', '微服务']
tags: ['微服务', 'SpringCloud', 'SpringBoot', 'Docker']
toc: true

---

课程内容:
1. @EnableAutoConfiguration 源码解析
2. SpringBoot 常用条件注解源码解析
3. SpringBoot 之 Mybatis 自动配置源码解析
4. SpringBoot 之 AOP 自动配置源码解析
1. 在解析 ImportSelector 时,所导入的配置类会被直接解析,而 DeferredImportSelector 导入的配置类会延迟进行解析(延迟在其他配置类都解析完之后)
2. DeferredImportSelector 支持分组,可以实现 getImportGroup 方法以及定义 Group 对象,就相当于指定了 DeferredImportSelector 所导入进来的配置类所属的组,比如 SpringBoot 就把所有自动配置类单独做了分组 AutoConfigurationGroup 常用条件注解 SpringBoot 中的常用条件注解有:
1. ConditionalOnBean:是否存在某个某类或某个名字的 Bean
2. ConditionalOnMissingBean:是否缺失某个某类或某个名字的 Bean
3. ConditionalOnSingleCandidate:是否符合指定类型的 Bean 只有一个
4. ConditionalOnClass:是否存在某个类
5. ConditionalOnMissingClass:是否缺失某个类
6. ConditionalOnExpression:指定的表达式返回的是 true 还是 false
7. ConditionalOnJava:判断 Java 版本
8. ConditionalOnWebApplication:当前应用是不是一个 Web 应用
9. ConditionalOnNotWebApplication:当前应用不是一个 Web 应用
10. ConditionalOnProperty:Environment 中是否存在某个属性当然我们也可以利用@Conditional 来自定义条件注解。

条件注解是可以写在类上和方法上的,如果某个条件注解写在了自动配置类上,那该自动配置类会不会生效就要看当前条件能不能符合,或者条件注解写在某个@Bean 修饰的方法上,那这个 Bean 生不生效就看当前条件符不符合。
具体原理是:
1. Spring 在解析某个自动配置类时,会先检查该自动配置类上是否有条件注解,如果有,则进一步判断该条件注解所指定的条件当前能不能满足,如果满足了则继续解析该配置类,如果不满足则不进行解析了,也就是配置类所定义的 Bean 都得不到解析,也就是相当于没有这些 Bean 了。
2. 同理,Spring 在解析某个@Bean 的方法时,也会先判断方法上是否有条件注解,然后进行解析,如果不满足条件,则该 Bean 不会生效我们可以发现,SpringBoot 的自动配置,实际上就是 SpringBoot 的源码中预先写好了一些配置类,预先定义好了一些 Bean,我们在用 SpringBoot 时,这些配置类就已经在我们项目的依赖中了,而这些自动配置类或自动配置 Bean 到底生不生效,就看具体所指定的条件了。
自定义条件注解 SpringBoot 中众多的条件注解,都是基于 Spring 中的@Conditional 来实现的,所以我们先来用一下@Conditional 注解。
先来看下@Conditional 注解的定义:
1 @Target({ElementType.TYPE, ElementType.METHOD})
2 @Retention(RetentionPolicy.RUNTIME)
3 @Documented4 public @interface Conditional {56 /**7 * All {@link Condition} classes that must {@linkplain Condition#matches match}8 * in order for the component to be registered.9 */10 Class<? extends Condition>[] value();
1112 }

根据定义我们在用@Conditional 注解时,需要指定一个或多个 Condition 的实现类,所以我们先来提供一个实现类:
1 public class ZhouyuCondition implements Condition {23 @Override4 public boolean matches(ConditionContext context, AnnotatedTypeMetadata metadata) {5 return false;
6 }78 }很明显,我们可以在 matches 方法中来定义条件逻辑:
1. ConditionContext:表示条件上下文,可以通过 ConditionContext 获取到当前的类加载器、 BeanFactory、Environment 环境变量对象
2. AnnotatedTypeMetadata:表示当前正在进行条件判断的 Bean 所对应的类信息,或方法信息(比如@Bean 定义的一个 Bean),可以通过 AnnotatedTypeMetadata 获取到当前类或方法相关的信息,从而就可以拿到条件注解的信息,当然如果一个 Bean 上使用了多个条件注解,那么在解析过程中都可以获取到,同时也能获取 Bean 上定义的其他注解信息@ConditionalOnClass 的底层工作原理先来看一个案例:
1 @Configuration2 @ConditionalOnClass(name = "com.zhouyu.Jetty")
3 @ConditionalOnMissingClass(value = "com.zhouyu.Tomcat")
4 public class ZhouyuConfiguration {567 }我们在 ZhouyuConfiguration 这个类上使用了两个条件注解:

### 1. @ConditionalOnClass(name = "com.zhouyu.Jetty"):条件是项目依赖中存在"com.zhouyu.Jetty"这个类,则表示符合条件
### 2. @ConditionalOnMissingClass(value = "com.zhouyu.Tomcat"):条件是项目依赖中不存在"com.zhouyu.Tomcat"这个类,则表示符合条件这两个注解对应的都是@Conditional(OnClassCondition.class),那在 OnClassCondition 类中是如何对这两个注解进行区分的呢?
Spring 在解析到 ZhouyuConfiguration 这个配置时,发现该类上用到了条件注解就会进行条件解析,相关源码如下:
12 // 这是 Spring 中的源码,不是 SpringBoot 中的 3 for (Condition condition : conditions) {4 ConfigurationPhase requiredPhase = null;
5 if (condition instanceof ConfigurationCondition) {6 requiredPhase = ((ConfigurationCondition)
condition).getConfigurationPhase();
7 }89 // 重点在这 10 if ((requiredPhase == null || requiredPhase == phase) &&!condition.matches(this.context, metadata)) {11 return true;
12 }13 }conditions 中保存了两个 OnClassCondition 对象,这段代码会依次调用 OnClassCondition 对象的 matches 方法进行条件匹配,一旦某一个条件不匹配就不会进行下一个条件的判断了,这里 return 的是 true,但是这段代码所在的方法叫做 shouldSkip,所以 true 表示忽略。
我们继续看 OnClassCondition 的 matches()方法的实现。
OnClassCondition 类继承了 FilteringSpringBootCondition,FilteringSpringBootCondition 类又继承了 SpringBootCondition,而 SpringBootCondition 实现了 Condition 接口,matches()方法也是在 SpringBootCondition 这个类中实现的:

1 @Override2 public final boolean matches(ConditionContext context, AnnotatedTypeMetadata metadata)
{3 // 获取当前解析的类名或方法名 4 String classOrMethodName = getClassOrMethodName(metadata);
5 try {6 // 进行具体的条件匹配,ConditionOutcome 表示匹配结果 7 ConditionOutcome outcome = getMatchOutcome(context, metadata);
89 // 日志记录匹配结果 10 logOutcome(classOrMethodName, outcome);
11 recordEvaluation(context, classOrMethodName, outcome);
1213 // 返回 true 或 false14 return outcome.isMatch();
15 }16 catch (NoClassDefFoundError ex) {17 // ...18 }19 catch (RuntimeException ex) {20 // ...21 }22 }所以具体的条件匹配逻辑在 getMatchOutcome 方法中,而 SpringBootCondition 类中的 getMatchOutcome 方法是一个抽象方法,具体的实现逻辑就在子类 OnClassCondition 中:
1 @Override2 public ConditionOutcome getMatchOutcome(ConditionContext context,AnnotatedTypeMetadata metadata) {3 ClassLoader classLoader = context.getClassLoader();
4 ConditionMessage matchMessage = ConditionMessage.empty();
56 // 拿到 ConditionalOnClass 注解中的 value 值,也就是要判断是否存在的类名 7 List<String> onClasses = getCandidates(metadata, ConditionalOnClass.class);
8 if (onClasses != null) {

9 // 判断 onClasses 中不存在的类 10 List<String> missing = filter(onClasses, ClassNameFilter.MISSING,classLoader);
11 // 如果有缺失的类,那就表示不匹配 12 if (!missing.isEmpty()) {13 returnConditionOutcome.noMatch(ConditionMessage.forCondition(ConditionalOnClass.class)
14.didNotFind("required class", "required classes").items(Style.QUOTE, missing));
15 }16 // 否则就表示匹配 17 matchMessage = matchMessage.andCondition(ConditionalOnClass.class)
18 .found("required class", "required classes")
19 .items(Style.QUOTE, filter(onClasses, ClassNameFilter.PRESENT,classLoader));
20 }2122 // 和上面类似,只不过是判断 onMissingClasses 是不是全部缺失,如果是则表示匹配 23 List<String> onMissingClasses = getCandidates(metadata,ConditionalOnMissingClass.class);
24 if (onMissingClasses != null) {25 List<String> present = filter(onMissingClasses,ClassNameFilter.PRESENT, classLoader);
26 if (!present.isEmpty()) {27 returnConditionOutcome.noMatch(ConditionMessage.forCondition(ConditionalOnMissingClass.class)
28.found("unwanted class", "unwanted classes").items(Style.QUOTE, present));
29 }30 matchMessage =matchMessage.andCondition(ConditionalOnMissingClass.class)
31 .didNotFind("unwanted class", "unwanted classes")
32 .items(Style.QUOTE, filter(onMissingClasses,ClassNameFilter.MISSING, classLoader));
33 }34 return ConditionOutcome.match(matchMessage);
35 }在 getMatchOutcome 方法中的逻辑为:
1. 如果类或方法上有@ConditionalOnClass 注解,则获取@ConditionalOnClass 注解中的 value 属性,也就是要判断是否存在的类名

### 2. 利用 ClassNameFilter.MISSING 来判断这些类是否缺失,把缺失的类的类名存入 missing 集合
### 3. 如果 missing 不为空,则表示有类缺失,则表示不匹配,并利用 ConditionMessage 记录哪些类是缺失的,直接 return,表示条件不匹配
### 4. 否则,则表示条件匹配,继续执行代码
### 5. 如果类或方法上有 ConditionalOnMissingClass 注解,则获取 ConditionalOnMissingClass 注解中的 value 属性,也就是要判断是否缺失的类名
### 6. 利用 ClassNameFilter.PRESENT 来判断这些类是否存在,把存在的类的类名存入 present 集合
### 7. 如果 present 不为空,则表示有类存在,则表示不匹配,并利用 ConditionMessage 记录哪些类是存在的,直接 return,表示条件不匹配
### 8. 否则,则表示条件匹配,继续执行代码
### 9. return,表示条件匹配因为 ConditionalOnClass 注解和 ConditionalOnMissingClass 注解的逻辑是比较类似的,所以在源码中都是在 OnClassCondition 这个类中实现的,假如一个类上即有@ConditionalOnClass,也有@ConditionalOnMissingClass,比如以下代码:
1 @Configuration2 @ConditionalOnClass(Tomcat.class)
3 @ConditionalOnMissingClass(value = "com.zhouyu.Tomcat")
4 public class ZhouyuConfiguration {567 }
1. 如果@ConditionalOnClass 条件匹配、@ConditionalOnMissingClass 条件也匹配,那么 getMatchOutcome 方法会执行两次
2. 如果@ConditionalOnClass 条件不匹配,那么 getMatchOutcome 方法会执行一次
3. 如果@ConditionalOnClass 条件匹配、@ConditionalOnMissingClass 条件不匹配,那么 getMatchOutcome 方法也只会执行一次,因为在 getMatchOutcome 方法处理了这种情况上面提到的 ClassNameFilter.MISSING 和 ClassNameFilter.PRESENT 也比较简单,代码如下:
1 protected enum ClassNameFilter {23 PRESENT {

45 @Override6 public boolean matches(String className, ClassLoaderclassLoader) {7 return isPresent(className, classLoader);
8 }910 },1112 MISSING {1314 @Override15 public boolean matches(String className, ClassLoaderclassLoader) {16 return !isPresent(className, classLoader);
17 }1819 };
2021 abstract boolean matches(String className, ClassLoader classLoader);
2223 static boolean isPresent(String className, ClassLoader classLoader) {24 if (classLoader == null) {25 classLoader = ClassUtils.getDefaultClassLoader();
26 }27 try {28 resolve(className, classLoader);
29 return true;
30 }31 catch (Throwable ex) {32 return false;
33 }34 }3536 }1 protected static Class<?> resolve(String className, ClassLoader classLoader) throwsClassNotFoundException {

2 if (classLoader != null) {3 return Class.forName(className, false, classLoader);
4 }5 return Class.forName(className);
6 }主要就是用类加载器,来判断类是否存在。
@ConditionalOnBean 的底层工作原理@ConditionalOnBean 和@ConditionalOnClass 的底层实现应该是差不多的,一个是判断 Bean 存不存在,一个是判断类存不存在,事实上也确实差不多。
首先@ConditionalOnBean 和@ConditionalOnMissingBean 对应的都是 OnBeanCondition 类,OnBeanCondition 类也是继承了 SpringBootCondition,所以 SpringBootCondition 类中的 getMatchOutcome 方法才是匹配逻辑:
1 @Override2 public ConditionOutcome getMatchOutcome(ConditionContext context, AnnotatedTypeMetadatametadata) {3 ConditionMessage matchMessage = ConditionMessage.empty();
4 MergedAnnotations annotations = metadata.getAnnotations();
56 // 如果存在 ConditionalOnBean 注解 7 if (annotations.isPresent(ConditionalOnBean.class)) {8 Spec<ConditionalOnBean> spec = new Spec<>(context, metadata,annotations, ConditionalOnBean.class);
9 MatchResult matchResult = getMatchingBeans(context, spec);
1011 // 如果某个 Bean 不存在 12 if (!matchResult.isAllMatched()) {13 String reason = createOnBeanNoMatchReason(matchResult);
14 returnConditionOutcome.noMatch(spec.message().because(reason));
15 }1617 // 所有 Bean 都存在

18 matchMessage = spec.message(matchMessage).found("bean","beans").items(Style.QUOTE,19matchResult.getNamesOfAllMatches());
20 }2122 // 如果存在 ConditionalOnSingleCandidate 注解 23 if (metadata.isAnnotated(ConditionalOnSingleCandidate.class.getName())) {24 Spec<ConditionalOnSingleCandidate> spec = newSingleCandidateSpec(context, metadata, annotations);
25 MatchResult matchResult = getMatchingBeans(context, spec);
2627 // Bean 不存在 28 if (!matchResult.isAllMatched()) {29 return ConditionOutcome.noMatch(spec.message().didNotFind("anybeans").atAll());
30 }3132 // Bean 存在 33 Set<String> allBeans = matchResult.getNamesOfAllMatches();
3435 // 如果只有一个 36 if (allBeans.size() == 1) {37 matchMessage = spec.message(matchMessage).found("a singlebean").items(Style.QUOTE, allBeans);
38 }39 else {40 // 如果有多个 41 List<String> primaryBeans =getPrimaryBeans(context.getBeanFactory(), allBeans,42spec.getStrategy() == SearchStrategy.ALL);
4344 // 没有主 Bean,那就不匹配 45 if (primaryBeans.isEmpty()) {46 return ConditionOutcome.noMatch(47 spec.message().didNotFind("a primary bean frombeans").items(Style.QUOTE, allBeans));
48 }49 // 有多个主 Bean,那就不匹配 50 if (primaryBeans.size() > 1) {

51 return ConditionOutcome52 .noMatch(spec.message().found("multipleprimary beans").items(Style.QUOTE, primaryBeans));
53 }5455 // 只有一个主 Bean56 matchMessage = spec.message(matchMessage)
57 .found("a single primary bean '" + primaryBeans.get(0)
+ "' from beans")
58 .items(Style.QUOTE, allBeans);
59 }60 }6162 // 存在 ConditionalOnMissingBean 注解 63 if (metadata.isAnnotated(ConditionalOnMissingBean.class.getName())) {64 Spec<ConditionalOnMissingBean> spec = new Spec<>(context, metadata,annotations,65ConditionalOnMissingBean.class);
66 MatchResult matchResult = getMatchingBeans(context, spec);
6768 //有任意一个 Bean 存在,那就条件不匹配 69 if (matchResult.isAnyMatched()) {70 String reason = createOnMissingBeanNoMatchReason(matchResult);
71 returnConditionOutcome.noMatch(spec.message().because(reason));
72 }7374 // 都不存在在,则匹配 75 matchMessage = spec.message(matchMessage).didNotFind("anybeans").atAll();
76 }77 return ConditionOutcome.match(matchMessage);
78 }逻辑流程为:
1. 当前在解析的类或方法上,是否有@ConditionalOnBean 注解,如果有则生成对应的 Spec 对象,该对象中包含了用户指定的,要判断的是否存在的 Bean 的类型
2. 调用 getMatchingBeans 方法进行条件判断,MatchResult 为条件判断结果

### 3. 只要判断出来某一个 Bean 不存在,则 return,表示条件不匹配
### 4. 只要所有 Bean 都存在,则继续执行下面代码
### 5. 当前在解析的类或方法上,是否有@ConditionalOnSingleCandidate 注解,如果有则生成对应的 SingleCandidateSpec 对象,该对象中包含了用户指定的,要判断的是否存在的 Bean 的类型(只能指定一个类型),并且该类型的 Bean 只能有一个
### 6. 调用 getMatchingBeans 方法进行条件判断,MatchResult 为条件判断结果
### 7. 指定类型的 Bean 如果不存在,则 return,表示条件不匹配
### 8. 如果指定类型的 Bean 存在,但是存在多个,那就看是否存在主 Bean(加了@primary 注解的 Bean),并且只能有一个主 Bean,如果没有,则 return,表示条件不匹配
### 9. 如果只有一个主 Bean,则表示条件匹配,继续执行下面代码
### 10. 当前在解析的类或方法上,是否有@ConditionalOnMissingBean 注解,如果有则生成对应的 Spec 对象,该对象中包含了用户指定的,要判断的是否缺失的 Bean 的类型
### 11. 调用 getMatchingBeans 方法进行条件判断,MatchResult 为条件判断结果
### 12. 只要有任意一个 Bean 存在,则 return,表示条件不匹配
### 13. 都存在,则表示条件匹配
### 14. 结束 getMatchingBeans 方法中会利用 BeanFactory 去获取指定类型的 Bean,如果没有指定类型的 Bean,
则会将该类型记录在 MatchResult 对象的 unmatchedTypes 集合中,如果有该类型的 Bean,则会把该 Bean 的 beanName 记录在 MatchResult 对象的 matchedNames 集合中,所以 MatchResult 对象中记录了,哪些类没有对应的 Bean,哪些类有对应的 Bean。
@ConditionalOnClass 和@ConditionalOnBean,这两个条件注解的工作原理就分析到这,总结以下流程就是:
1. Spring 在解析某个配置类,或某个 Bean 定义时
2. 如果发现它们上面用到了条件注解,就会取出所有的条件的条件注解,并生成对应的条件对象,比如 OnBeanCondition 对象、 OnClassCondition 对象
3. 从而依次调用条件对象的 matches 方法,进行条件匹配,看是否符合条件
4. 而条件匹配逻辑中,会拿到@ConditionalOnClass 和@ConditionalOnBean 等条件注解的信息,比如要判断哪些类存在、哪些 Bean 存在
5. 然后利用 ClassLaoder、BeanFactory 来进行判断
6. 最后只有所有条件注解的条件都匹配,那么当前配置类或 Bean 定义才算符合条件源码会有点难,还希望大家耐点性子,多看多调试源码。

Starter 机制那 SpringBoot 中的 Starter 和自动配置又有什么关系呢?
其实首先要明白一个 Starter,就是一个 Maven 依赖,当我们在项目的 pom.xml 文件中添加某个 Starter 依赖时,其实就是简单的添加了很多其他的依赖,比如:
1. spring-boot-starter-web:引入了 spring-boot-starter、spring-boot-starter-json、spring-boot-starter-
tomcat 等和 Web 开发相关的依赖包
2. spring-boot-starter-tomcat:引入了 tomcat-embed-core、tomcat-embed-el、tomcat-embed-websocket 等和 Tomcat 相关的依赖包
3. ...
如果硬要把 Starter 机制和自动配置联系起来,那就是通过@ConditionalOnClass 这个条件注解,因为这个条件注解的作用就是用来判断当前应用的依赖中是否存在某个类或某些类,比如:
1 @Configuration(proxyBeanMethods = false)
2 @ConditionalOnClass({ Servlet.class, Tomcat.class, UpgradeProtocol.class })
3 @ConditionalOnMissingBean(value = ServletWebServerFactory.class, search =SearchStrategy.CURRENT)
4 static class EmbeddedTomcat {56 @Bean7 TomcatServletWebServerFactory tomcatServletWebServerFactory(8 ObjectProvider<TomcatConnectorCustomizer> connectorCustomizers,9 ObjectProvider<TomcatContextCustomizer> contextCustomizers,10 ObjectProvider<TomcatProtocolHandlerCustomizer<?>> protocolHandlerCustomizers)
{11 TomcatServletWebServerFactory factory = new TomcatServletWebServerFactory();
1213 // orderedStream()调用时会去 Spring 容器中找到 TomcatConnectorCustomizer 类型的 Bean,默认是没有的,程序员可以自己定义 14 factory.getTomcatConnectorCustomizers()
15 .addAll(connectorCustomizers.orderedStream().collect(Collectors.toList()));
16 factory.getTomcatContextCustomizers()
17 .addAll(contextCustomizers.orderedStream().collect(Collectors.toList()));
18 factory.getTomcatProtocolHandlerCustomizers()
19.addAll(protocolHandlerCustomizers.orderedStream().collect(Collectors.toList()));
20 return factory;
21 }

2223 }上面代码中就用到了@ConditionalOnClass,用来判断项目中是否存在 Servlet.class、Tomcat.class、UpgradeProtocol.class 这三个类,如果存在就满足当前条件,如果项目中引入了 spring-boot-starter-tomcat,那就有这三个类,如果没有 spring-boot-starter-tomcat 那就可能没有这三个类(除非你自己单独引入了 Tomcat 相关的依赖)。
所以这就做到了,如果我们在项目中要用 Tomcat,那就依赖 spring-boot-starter-web 就够了,因为它默认依赖了 spring-boot-starter-tomcat,从而依赖了 Tomcat,从而 Tomcat 相关的 Bean 能生效。
而如果不想用 Tomcat,那就得这么写:
1 <dependency>2 <groupId>org.springframework.boot</groupId>3 <spanrtifactId>spring-boot-starter-web</artifactId>4 <exclusions>5 <exclusion>6 <groupId>org.springframework.boot</groupId>7 <spanrtifactId>spring-boot-starter-tomcat</artifactId>8 </exclusion>9 </exclusions>10 </dependency>1112 <dependency>13 <groupId>org.springframework.boot</groupId>14 <spanrtifactId>spring-boot-starter-jetty</artifactId>15 </dependency>得把 spring-boot-starter-tomcat 给排除掉,再添加上 spring-boot-starter-jetty 的依赖,这样 Tomcat 的 Bean 就不会生效,Jetty 的 Bean 就能生效,从而项目中用的就是 Jetty。
Spring Boot Tomcat 自动配置通过前面我们会 SpringBoot 的自动配置机制、 Starter 机制、启动过程的底层分析,我们拿一个实际的业务案例来串讲一下,那就是 SpringBoot 和 Tomcat 的整合。

我们知道,只要我们的项目添加的 starter 为:spring-boot-starter-web,那么我们启动项目时,SpringBoot 就会自动启动一个 Tomcat。
那么这是怎么做到的呢?
首先我们可以发现,在 spring-boot-starter-web 这个 starter 中,其实简介的引入了 spring-bootstarter-tomcat 这个 starter,这个 spring-boot-starter-tomcat 又引入了 tomcat-embed-core 依赖,所以只要我们项目中依赖了 spring-boot-starter-web 就相当于依赖了 Tomcat。
然后在 SpringBoot 众多的自动配置类中,有一个自动配置类叫做 ServletWebServerFactoryAutoConfiguration,定义为:
1 @Configuration(proxyBeanMethods = false)
2 @AutoConfigureOrder(Ordered.HIGHEST_PRECEDENCE)
3 @ConditionalOnClass(ServletRequest.class)
4 @ConditionalOnWebApplication(type = Type.SERVLET)
5 @EnableConfigurationProperties(ServerProperties.class)
6 @Import({ ServletWebServerFactoryAutoConfiguration.BeanPostProcessorsRegistrar.class,7 ServletWebServerFactoryConfiguration.EmbeddedTomcat.class,8 ServletWebServerFactoryConfiguration.EmbeddedJetty.class,9 ServletWebServerFactoryConfiguration.EmbeddedUndertow.class })
10 public class ServletWebServerFactoryAutoConfiguration {11 // ...12 }首先看这个自动配置类所需要的条件:
1. @ConditionalOnClass(ServletRequest.class):表示项目依赖中要有 ServletRequest 类(server api)
2. @ConditionalOnWebApplication(type = Type.SERVLET):表示项目应用类型得是 SpringMVC(讲启动过程的时候就知道如何判断一个 SpringBoot 应用的类型了)
在上面提到的 spring-boot-starter-web 中,其实还间接的引入了 spring-web、spring-webmvc 等依赖,这就使得第二个条件满足,而对于第一个条件的 ServletRequest 类,虽然它是 Servlet 规范中的类,但是在我们所依赖的 tomcat-embed-core 这个 jar 包中是存在这个类的,这是因为 Tomcat 在自己的源码中把 Servlet 规范中的一些代码也包含进去了,比如:

这就使得 ServletWebServerFactoryAutoConfiguration 这个自动配置的两个条件都符合,那么 Spring 就能去解析它,一解析它就发现这个自动配置类 Import 进来了三个类:
1. ServletWebServerFactoryConfiguration.EmbeddedTomcat.class
2. ServletWebServerFactoryConfiguration.EmbeddedJetty.class
3. ServletWebServerFactoryConfiguration.EmbeddedUndertow.class 很明显,Import 进来的这三个类应该是差不多,我们看 EmbeddedTomcat 这个类:
1 @Configuration(proxyBeanMethods = false)
2 @ConditionalOnClass({ Servlet.class, Tomcat.class, UpgradeProtocol.class })
3 @ConditionalOnMissingBean(value = ServletWebServerFactory.class, search =SearchStrategy.CURRENT)
4 static class EmbeddedTomcat {56 @Bean7 TomcatServletWebServerFactory tomcatServletWebServerFactory(8 ObjectProvider<TomcatConnectorCustomizer> connectorCustomizers,9 ObjectProvider<TomcatContextCustomizer> contextCustomizers,10 ObjectProvider<TomcatProtocolHandlerCustomizer<?>>protocolHandlerCustomizers) {11 TomcatServletWebServerFactory factory = newTomcatServletWebServerFactory();
1213 // orderedStream()调用时会去 Spring 容器中找到 TomcatConnectorCustomizer 类型的 Bean,默认是没有的,程序员可以自己定义 14 factory.getTomcatConnectorCustomizers()
15.addAll(connectorCustomizers.orderedStream().collect(Collectors.toList()));
16 factory.getTomcatContextCustomizers()
17.addAll(contextCustomizers.orderedStream().collect(Collectors.toList()));
18 factory.getTomcatProtocolHandlerCustomizers()
19.addAll(protocolHandlerCustomizers.orderedStream().collect(Collectors.toList()));
20 return factory;
21 }2223 }

可以发现这个类是一个配置类,所以 Spring 也会来解析它,不过它也有两个条件:
1. @ConditionalOnClass({ Servlet.class, Tomcat.class, UpgradeProtocol.class }):项目依赖中要有 Servlet.class、Tomcat.class、UpgradeProtocol.class 这三个类,这个条件比较容易理解,项目依赖中有 Tomcat 的类,那这个条件就符合。
2. @ConditionalOnMissingBean(value = ServletWebServerFactory.class, search =SearchStrategy.CURRENT),项目中没有 ServletWebServerFactory 类型的 Bean,因为这个配置类的内部就是定义了一个 TomcatServletWebServerFactory 类型的 Bean,TomcatServletWebServerFactory 实现了 ServletWebServerFactory 接口,所以这个条件注解的意思就是,如果程序员自己没有定义 ServletWebServerFactory 类型的 Bean,那么就符合条件,不然,如果程序员自己定义了 ServletWebServerFactory 类型的 Bean,那么条件就不符合,也就导致 SpringBoot 给我们定义的 TomcatServletWebServerFactory 这个 Bean 就不会生效,最终生效的就是程序员自己定义的。
所以,通常只要我们项目依赖中有 Tomcat 依赖,那就符合条件,那最终 Spring 容器中就会有 TomcatServletWebServerFactory 这个 Bean。
对于另外的 EmbeddedJetty 和 EmbeddedUndertow,也差不多,都是判断项目依赖中是否有 Jetty 和 Undertow 的依赖,如果有,那么对应在 Spring 容器中就会存在 JettyServletWebServerFactory 类型的 Bean、或者存在 UndertowServletWebServerFactory 类型的 Bean。
总结一下:
1. 有 Tomcat 依赖,就有 TomcatServletWebServerFactory 这个 Bean
2. 有 Jetty 依赖,就有 JettyServletWebServerFactory 这个 Bean
3. 有 Undertow 依赖,就有 UndertowServletWebServerFactory 这个 Bean 那么 SpringBoot 给我们配置的这几个 Bean 到底有什么用呢?
我们前面说到,TomcatServletWebServerFactory 实现了 ServletWebServerFactory 这个接口,这个接口的定义为:
1 public interface ServletWebServerFactory {2 WebServer getWebServer(ServletContextInitializer... initializers);
3 }

1 public interface WebServer {2 void start() throws WebServerException;
3 void stop() throws WebServerException;
4 int getPort();
5 }我们发现 ServletWebServerFactory 其实就是用来获得 WebServer 对象的,而 WebServer 拥有启动、停止、获取端口等方法,那么很自然,我们就发现 WebServer 其实指的就是 Tomcat、Jetty、Undertow,而 TomcatServletWebServerFactory 就是用来生成 Tomcat 所对应的 WebServer 对象,具体一点就是 TomcatWebServer 对象,并且在生成 TomcatWebServer 对象时会把 Tomcat 给启动起来,在源码中,调用 TomcatServletWebServerFactory 对象的 getWebServer()方法时就会启动 Tomcat。
我们再来看 TomcatServletWebServerFactory 这个 Bean 的定义:
1 @Bean2 TomcatServletWebServerFactory tomcatServletWebServerFactory(3 ObjectProvider<TomcatConnectorCustomizer> connectorCustomizers,4 ObjectProvider<TomcatContextCustomizer> contextCustomizers,5 ObjectProvider<TomcatProtocolHandlerCustomizer<?>> protocolHandlerCustomizers) {6 TomcatServletWebServerFactory factory = new TomcatServletWebServerFactory();
78 // orderedStream()调用时会去 Spring 容器中找到 TomcatConnectorCustomizer 类型的 Bean,默认是没有的,程序员可以自己定义 9 factory.getTomcatConnectorCustomizers()
10.addAll(connectorCustomizers.orderedStream().collect(Collectors.toList()));
11 factory.getTomcatContextCustomizers()
12.addAll(contextCustomizers.orderedStream().collect(Collectors.toList()));
13 factory.getTomcatProtocolHandlerCustomizers()
14.addAll(protocolHandlerCustomizers.orderedStream().collect(Collectors.toList()));
15 return factory;
16 }

要构造这个 Bean,Spring 会从 Spring 容器中获取到 TomcatConnectorCustomizer、TomcatContextCustomizer、TomcatProtocolHandlerCustomizer 这三个类型的 Bean,然后把它们添加到 TomcatServletWebServerFactory 对象中去,很明显这三种 Bean 是用来配置 Tomcat 的,比如:
1. TomcatConnectorCustomizer:是用来配置 Tomcat 中的 Connector 组件的
2. TomcatContextCustomizer:是用来配置 Tomcat 中的 Context 组件的
3. TomcatProtocolHandlerCustomizer:是用来配置 Tomcat 中的 ProtocolHandler 组件的也就是我们可以通过定义 TomcatConnectorCustomizer 类型的 Bean,来对 Tomcat 进行配置,比如:
1 @SpringBootApplication2 public class MyApplication {34 @Bean5 public TomcatConnectorCustomizer tomcatConnectorCustomizer(){6 return new TomcatConnectorCustomizer() {7 @Override8 public void customize(Connector connector) {9 connector.setPort(8888);
10 }11 };
12 }1314 public static void main(String[] args) {15 SpringApplication.run(MyApplication.class);
16 }1718 }这样 Tomcat 就会绑定 8888 这个端口。
有了 TomcatServletWebServerFactory 这个 Bean 之后,在 SpringBoot 的启动过程中,会执行 ServletWebServerApplicationContext 的 onRefresh()方法,而这个方法会调用 createWebServer()
方法,而这个方法中最为重要的两行代码为:
1 ServletWebServerFactory factory = getWebServerFactory();

2 this.webServer = factory.getWebServer(getSelfInitializer());
很明显,getWebServerFactory()负责获取具体的 ServletWebServerFactory 对象,要么是 TomcatServletWebServerFactory 对象,要么是 JettyServletWebServerFactory 对象,要么是 UndertowServletWebServerFactory 对象,注意只能获取到一个,然后调用该对象的 getWebServer 方法,启动对应的 Tomcat、或者 Jetty、或者 Undertow。
getWebServerFactory 方法中的逻辑比较简单,获取 Spring 容器中的 ServletWebServerFactory 类型的 Bean 对象,如果没有获取到则抛异常,如果找到多个也抛异常,也就是在 Spring 容器中只能有一个 ServletWebServerFactory 类型的 Bean 对象。
拿到 TomcatServletWebServerFactory 对象后,就调用它的 getWebServer 方法,而在这个方法中就会生成一个 Tomcat 对象,并且利用前面的 TomcatConnectorCustomizer 等等会 Tomcat 对象进行配置,最后启动 Tomcat。
这样在启动应用时就完成了 Tomcat 的启动,到此我们通过这个案例也看到了具体的 Starter 机制、自动配置的具体使用。
自动配置类 ServletWebServerFactoryAutoConfiguration 中,还会定义一个 ServletWebServerFactoryCustomizer 类型的 Bean,定义为:
1 @Bean2 public ServletWebServerFactoryCustomizerservletWebServerFactoryCustomizer(ServerProperties serverProperties,3ObjectProvider<WebListenerRegistrar> webListenerRegistrars,4ObjectProvider<CookieSameSiteSupplier> cookieSameSiteSuppliers) {5 return new ServletWebServerFactoryCustomizer(serverProperties,6webListenerRegistrars.orderedStream().collect(Collectors.toList()),7cookieSameSiteSuppliers.orderedStream().collect(Collectors.toList()));
8 }

这个 Bean 会接收一个 ServerProperties 的 Bean,ServerProperties 的 Bean 对应的就是 properties 文件中前缀为 server 的配置,我们可以利用 ServerProperties 对象的 getPort 方法获取到我们所配置的 server.port 的值。
而 ServletWebServerFactoryCustomizer 是针对一个 ServletWebServerFactory 的自定义器,也就是用来配置 TomcatServletWebServerFactory 这个 Bean 的,到时候 ServletWebServerFactoryCustomizer 就会利用 ServerProperties 对象来对 TomcatServletWebServerFactory 对象进行设置。
在 ServletWebServerFactoryAutoConfiguration 这个自动配置上,除开 Import 了 EmbeddedTomcat、EmbeddedJetty、EmbeddedUndertow 这三个配置类,还 Import 了一个 ServletWebServerFactoryAutoConfiguration.BeanPostProcessorsRegistrar.class,这个 BeanPostProcessorsRegistrar 会向 Spring 容器中注册一个 WebServerFactoryCustomizerBeanPostProcessor 类型的 Bean。
WebServerFactoryCustomizerBeanPostProcessor 是一个 BeanPosrtProcessor,它专门用来处理类型为 WebServerFactory 的 Bean 对象,而我们的 TomcatServletWebServerFactory、JettyServletWebServerFactory、UndertowServletWebServerFactory 也都实现了这个接口,所以不管当前项目依赖的情况,只要在 Spring 在创建比如 TomcatServletWebServerFactory 这个 Bean 时,WebServerFactoryCustomizerBeanPostProcessor 就会对它进行处理,处理的逻辑为:
1. 从 Spring 容器中拿到 WebServerFactoryCustomizer 类型的 Bean,也就是前面说的 ServletWebServerFactoryCustomizer 对象
2. 然后调用 ServletWebServerFactoryCustomizer 对象的 customize 方法,把 TomcatServletWebServerFactory 对象传入进去
3. customize 方法中就会从 ServerProperties 对象获取各种配置,然后设置给 TomcatServletWebServerFactory 对象比如:
这样当 TomcatServletWebServerFactory 这个 Bean 对象创建完成后,它里面的很多属性,比如 port,就已经是程序员所配置的值了,后续执行 getWebServer 方法时,就直接获取自己的属性,比如 port 属性,设置给 Tomcat,然后再利用 TomcatConnectorCustomizer 等进行处理,最后启动 Tomcat。
到此,SpringBoot 整合 Tomcat 的核心原理就分析完了,主要涉及的东西有:

### 1. spring-boot-starter-web:会自动引入 Tomcat、SpringMVC 的依赖
### 2. ServletWebServerFactoryAutoConfiguration:自动配置类
### 3. ServletWebServerFactoryAutoConfiguration.BeanPostProcessorsRegistrar:用来注册 WebServerFactoryCustomizerBeanPostProcessor
### 4. ServletWebServerFactoryConfiguration.EmbeddedTomcat:配置 TomcatServletWebServerFactory
### 5. ServletWebServerFactoryConfiguration.EmbeddedJetty:配置 JettyServletWebServerFactory
### 6. ServletWebServerFactoryConfiguration.EmbeddedUndertow:配置 UndertowServletWebServerFactory
### 7. ServletWebServerFactoryCustomizer:用来配置 ServletWebServerFactory
### 8. WebServerFactoryCustomizerBeanPostProcessor:是一个 BeanPostProcessor,利用 ServletWebServerFactoryCustomizer 来配置 ServletWebServerFactory
### 9. ServletWebServerApplicationContext 中的 onRefresh()方法:负责启动 TomcatSpring Boot AOP 自动配置 1 @Configuration(proxyBeanMethods = false)
23 // spring.aop.auto=true 时开启 AOP,或者没有配置 spring.aop.auto 时默认也是开启 4 @ConditionalOnProperty(prefix = "spring.aop", name = "auto", havingValue = "true",matchIfMissing = true)
5 public class AopAutoConfiguration {67 @Configuration(proxyBeanMethods = false)
8 @ConditionalOnClass(Advice.class)
9 static class AspectJAutoProxyingConfiguration {1011 @Configuration(proxyBeanMethods = false)
12 // 开启 AOP 的注解,使用 JDK 动态代理 13 @EnableAspectJAutoProxy(proxyTargetClass = false)
14 // spring.aop.proxy-target-class=false 时才生效 15 @ConditionalOnProperty(prefix = "spring.aop", name = "proxy-targetclass", havingValue = "false")
16 static class JdkDynamicAutoProxyConfiguration {1718 }1921 @Configuration(proxyBeanMethods = false)
22 // 开启 AOP 的注解,使用 CGLIB 动态代理 23 @EnableAspectJAutoProxy(proxyTargetClass = true)
24 // spring.aop.proxy-target-class=true 时生效,或者没有配置 spring.aop.proxy-target-class 时默认也生效 25 @ConditionalOnProperty(prefix = "spring.aop", name = "proxy-targetclass", havingValue = "true",26 matchIfMissing = true)
27 static class CglibAutoProxyConfiguration {2829 }3031 }3233 @Configuration(proxyBeanMethods = false)
34 // 没有 aspectj 的依赖,但是又要使用 cglib 动态代理 35 @ConditionalOnMissingClass("org.aspectj.weaver.Advice")
36 @ConditionalOnProperty(prefix = "spring.aop", name = "proxy-target-class",havingValue = "true",37 matchIfMissing = true)
38 static class ClassProxyingConfiguration {3940 @Bean41 static BeanFactoryPostProcessorforceAutoProxyCreatorToUseClassProxying() {42 return (beanFactory) -> {43 if (beanFactory instanceof BeanDefinitionRegistry) {44 BeanDefinitionRegistry registry =(BeanDefinitionRegistry) beanFactory;
45 // 注册 InfrastructureAdvisorAutoProxyCreator 从而开启 Spring AOP46 // @EnableAspectJAutoProxy 会注册 AnnotationAwareAspectJAutoProxyCreator,也会开启 Spring AOP 但是同时有用解析 AspectJ 注解的功能 47AopConfigUtils.registerAutoProxyCreatorIfNecessary(registry);
48AopConfigUtils.forceAutoProxyCreatorToUseClassProxying(registry);
49 }50 };
51 }5253 }

5455 }56Spring Boot Mybatis 自动配置 Mybatis 的自动配置类为 MybatisAutoConfiguration,该类中配置了一个 SqlSessionFactory 和 AutoConfiguredMapperScannerRegistrar。
SqlSessionFactory 这个 Bean 是 Mybatis 需要配置的,AutoConfiguredMapperScannerRegistrar 会注册并配置一个 MapperScannerConfigurer。
1 public static class AutoConfiguredMapperScannerRegistrar2 implements BeanFactoryAware, EnvironmentAware, ImportBeanDefinitionRegistrar {34 private BeanFactory beanFactory;
5 private Environment environment;
67 @Override8 public void registerBeanDefinitions(AnnotationMetadata importingClassMetadata,BeanDefinitionRegistry registry) {910 if (!AutoConfigurationPackages.has(this.beanFactory)) {11 logger.debug("Could not determine auto-configuration package, automatic mapperscanning disabled.");
12 return;
13 }1415 logger.debug("Searching for mappers annotated with @Mapper");
1617 // 获取 AutoConfigurationPackages Bean 从而获取 SpringBoot 的扫描路径 18 List<String> packages = AutoConfigurationPackages.get(this.beanFactory);
19 if (logger.isDebugEnabled()) {20 packages.forEach(pkg -> logger.debug("Using auto-configuration base package'{}'", pkg));
21 }

2223 BeanDefinitionBuilder builder =BeanDefinitionBuilder.genericBeanDefinition(MapperScannerConfigurer.class);
24 builder.addPropertyValue("processPropertyPlaceHolders", true);
2526 // 限制了接口上得加 Mapper 注解 27 builder.addPropertyValue("annotationClass", Mapper.class);
28 builder.addPropertyValue("basePackage",StringUtils.collectionToCommaDelimitedString(packages));
29 BeanWrapper beanWrapper = new BeanWrapperImpl(MapperScannerConfigurer.class);
30 Set<String> propertyNames =Stream.of(beanWrapper.getPropertyDescriptors()).map(PropertyDescriptor::getName)
31 .collect(Collectors.toSet());
32 if (propertyNames.contains("lazyInitialization")) {33 // Need to mybatis-spring 2.0.2+34 builder.addPropertyValue("lazyInitialization", "${mybatis.lazyinitialization:false}");
35 }36 if (propertyNames.contains("defaultScope")) {37 // Need to mybatis-spring 2.0.6+38 builder.addPropertyValue("defaultScope", "${mybatis.mapper-default-scope:}");
39 }4041 // for spring-native42 boolean injectSqlSession = environment.getProperty("mybatis.inject-sql-sessionon-mapper-scan", Boolean.class,43 Boolean.TRUE);
44 if (injectSqlSession && this.beanFactory instanceof ListableBeanFactory) {45 ListableBeanFactory listableBeanFactory = (ListableBeanFactory)
this.beanFactory;
46 Optional<String> sqlSessionTemplateBeanName = Optional47 .ofNullable(getBeanNameForType(SqlSessionTemplate.class,listableBeanFactory));
48 Optional<String> sqlSessionFactoryBeanName = Optional49 .ofNullable(getBeanNameForType(SqlSessionFactory.class,listableBeanFactory));
50 if (sqlSessionTemplateBeanName.isPresent() ||!sqlSessionFactoryBeanName.isPresent()) {51 builder.addPropertyValue("sqlSessionTemplateBeanName",52 sqlSessionTemplateBeanName.orElse("sqlSessionTemplate"));
53 } else {54 builder.addPropertyValue("sqlSessionFactoryBeanName",sqlSessionFactoryBeanName.get());

55 }56 }57 builder.setRole(BeanDefinition.ROLE_INFRASTRUCTURE);
5859 registry.registerBeanDefinition(MapperScannerConfigurer.class.getName(),builder.getBeanDefinition());
60 }6162 @Override63 public void setBeanFactory(BeanFactory beanFactory) {64 this.beanFactory = beanFactory;
65 }6667 @Override68 public void setEnvironment(Environment environment) {69 this.environment = environment;
70 }7172 private String getBeanNameForType(Class<?> type, ListableBeanFactory factory) {73 String[] beanNames = factory.getBeanNamesForType(type);
74 return beanNames.length > 0 ? beanNames[0] : null;
75 }7677 }
