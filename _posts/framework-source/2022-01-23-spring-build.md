---


title: "Spring源码编译教程"
description: "讲的是最新的 Spring 版本,我之前用的是 2019 的某个 IDEA 版本,但是我尝试过后发现编译不成功,所以改用了最新版本 IDEA 版本 2021.1.3"
author: hsc
date: 2022-01-23 00:00:00 +0800
categories: ['Java 后端', '框架源码']
tags: ['Spring', 'MyBatis']
toc: true


---

讲的是最新的 Spring 版本,我之前用的是 2019 的某个 IDEA 版本,但是我尝试过后发现编译不成功,所以改用了最新版本 IDEA 版本 2021.1.3,所以对于大家而言也尽量用这个版本,用其他 IDEA 版本可能会遇到各种各样的问题,解决问题会比较费时间,所以为了节省大家和我的时间,请大家用 2021.1.3 这个 IDEA 版本。
Spring 带注释源码地址:
git clone 的地址为:https://gitee.com/dadudu1024/spring-framework-5.3.10.git 附上 2021.1.3 版的百度网盘链接:
链接:https://pan.baidu.com/s/1X79-2bFGtkL0763QjAya3w 提取码:uk7w 此链接中还有 IDEA 破解所需要的工具包,和一个.gradle.zip 压缩包(后续会用到,我是用的 360 压缩软件进行压缩的,建议大家也用这个软件来解压,有同学反馈用其他软件可能解压会遇到问题,上面网盘链接里有一个.gradle 的压缩包和一个未压缩的.gradle 文件夹),还有一个 JDK1.8 的安装包(因为如果用稍微老一点的 1.8 小版本,也会出现奇葩问题,所以也尽量用我提供的这个 JDK)
附上 IDEA 破解教程链接:https://www.exception.site/essay/idea-reset-eval2021.1.3IDEA 版本截图:

下载 Spring 源码所需要的依赖百度网盘链接:https://pan.baidu.com/s/1X79-2bFGtkL0763QjAya3w 提取码:uk7w 下载得到.gradle.zip 压缩包,并解压,比如解压到 D 盘因为 Spring 源码存在很多依赖包,如果大家自行下载,会需要下很久(1 小时都有可能),所以我直接把我电脑上的依赖包给到大家。
Spring 是通过 gradle 来编译源码下载依赖的,.gradle 文件夹可以理解为 gradle 的仓库(和 mave 类似,不懂 gradle 的先这么理解),而我给大家的这个仓库,只包含了 Spring 源码所需要的依赖。

下载 Spring 源码 git clone 的地址为:https://gitee.com/dadudu1024/spring-framework-5.3.10.git 建议直接用 IDEA 的 git 来下载源码:
输入地址,点击 Clone,就会开始下载源码工程(因为是从 gitee 上下载,所以会比从 github 上下载快很多)。
一旦下载完成,IDEA 就会自动下载 gradle,下载完 gradle 就会开始下载 Spring 源码依赖,但是我们已经有现成的了,所以可以直接取消这个过程。
修改 IDEA 的 gradle 配置首先把 gradle user home 改为.gradle 压缩包的解压之后的文件路径,比如 D:\.gradle 然后把 Build and run suing 和 Run tests using 都改为 IntelliJ IDEA,其他都不用动,改为之后如下图:
改完之后点击 Apply,再点击 OK,会自动触发 gradle 的重新编译。
如果没有触发可以,点击

正常情况下,此时 gradle 编译将比较快,会有一个索引文件过程,但是不需要额外的下载 gradle 和依赖了。
编译成功截图:
运行代码编译成功后,在左侧可以看到如下模块,其中有一个 tuling 模块,这是我写的一个模块,可以直接运行,在它下面有一个 Test 类,直接运行 main 方法。
问题 1 第一次运行可能会比较慢,在运行过程也可能会出现问题,比如那么请运行一下:
如果 build 之后出现了错误,比如:
没关系,请忽略,继续往下走。
再次执行 Test 类中的 main 方法,可能就直接运行成功了:
到此,恭喜你,你已经成功的编译好了 Spring 源码,可以直接查看并进行调试了。

问题 2 如果出现了:
报错的 CoroutinesUtils 是一个 kotlin 中的类,解决办法:
点击 File -> Project Structure -> Libraries -> “+” -> Java,然后选择 spring-framework/springcore/kotlin-coroutines/build/libs/kotlin-coroutines-5.2.4.BUILD-SNAPSHOT.jar,在弹出的对话框中选择 spring-core.main,在重新运行 Test 类中的 main 方法即可,注意我图中是报错的模块 spring-core,所以操作的是 spring-core.main,如果是其他模块报类似的错,就做类似的操作。
问题 3 需要重新安装电脑上的 git,并且最好是按照最新版本的 git(上面网盘中有按照文件),安装的时候注意以下页面选择第二项:
