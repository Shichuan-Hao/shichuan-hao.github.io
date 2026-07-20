---
title: Ollama 本地部署 DeepSeek R1 模型
description: Ollama 本地部署 DeepSeek R1 模型
author: hsc
date: 2024-06-18 12:27:00 +0800
categories: [AI Agent]
tags: [DeepSeek, Ollama, DeepSeek R1]
---

## Ollama 项目介绍

`Ollama` 是在 Github 上的开源项目，其项目定位是：<hl=red>一个本地运行大模型的集成框架</hl>。

目前主要针对主流的 <hl=red>LLaMA</hl> 架构的开源大模型设计，通过将模型权重、配置文件和必要数据封装进由<hl=red>Modelfile</hl>定义的包中，从而实现大模型的下载，启动和本地运行的自动化部署及推流流程。

此外，<hl=red>Ollama</hl> 内置了一系列针对大模型运行和推理的优化策略，目前作为一个非常热门的<color=red>大模型托管平台</color>，基本主流的大模型应用开发框架如 `LangChain`、`AutoGen`、`Microsoft GraphRAG`及热门项目`AnythingLLM`、`OpenWebUI` 等高度集成。

> `Ollama` 通过将大模型运行的所有必要组件（如权重文件、配置设置和相关数据）封装在一个单一的文件或包中，`Modelfile` 允许用户更容易地下载、安装、配置和启动模型。这种方法类似于其它软件或应用程序的安装包，它们将所有必要的文件打包在一起，以便用户可以通过简单的安装过程将软件添加到他们的系统中。<br/>
Ollama 项目地址：[https://github.com/Ollama/ollama](https://github.com/Ollama/ollama) <br/>
Ollama 官方地址：[https://ollama.com/](https://ollama.com/)

![Ollama 官方地址](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502131249751.png)

Ollama 项目支持跨平台部署，目前已兼容 Mac、Linux 和 Windows 操作系统。特别地对 Mac 和 Windows 用户提供了非常直观的预览版，包括内置的 GPU 加速功能、访问完整模型库的能力，以及对 OpenAI 的兼容性在内的 Ollama REST API，对用户使用尤为友好。

但无论使用哪个操作系统，Ollama 项目的安装过程都设计得非常简单。不过根据研发需求以及真实企业得应用需求，还是建议使用 Linux 操作系统进行部署/实践。可以通过[https://github.com/ollama/ollama](https://github.com/ollama/ollama) 依据实际情况进行安装体验。

![](https://snowball101.oss-cn-beijing.aliyuncs.com/img/202403081646978.png)

本人是在 Ubuntu 24.04 系统下安装部署 Ollama 项目，因此本文重点总结该版本操作系统得详细步骤。

具体来说，Ollama 在 Ubuntu 系统上安装方式由两种，分别是：<hl=red>Olla一键安装和手动安装ma</hl>，但不论使用哪种方法进行安装，都需要安装Ollama项目的服务器上具备网络连通环境，因为不仅涉及Ollama安装包的更新，还会涉及后续大模型的下载。

## Ollama 项目本地安装

Ollama 项目本地安装得方法极为简单，这里以 Ubuntu 24.04 系统为例，先进入命令行终端，执行如下一条命令即可自动化完成：

```bash
 curl -fsSL https://ollama.com/install.sh | sh
```

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502111855169.png)

这行命令的目的是从 [https://ollama.com/install.sh](https://ollama.com/install.sh) 下载安装脚本，并执行安装,，在安装过程中会包含以下几个主要的操作：
1. 检查当前服务器的基础环境，如系统版本等；
2. 下载 Ollama 的二进制文件；
3. 配置系统服务，包括创建用户和用户组，添加 Ollama 的配置信息；
4. 启动 Ollama 服务。

这个过程会比较慢，拉取的文件约 2G 左右，如果安装过程中未出现任何错误信息，通常情况下能够表明安装已经成功。可以通过执行下命令来检查 Ollama 服务的运行状态：

```bash
systemctl status ollama
```

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502111857348.png)

如果 Active 状态显示为 active，则说明 Ollama 服务目前处于正常运行状态。同时还可以通过以下命令查询当前安装的 Ollama 版本信息：

```bash
$ ollama --version
$ sudo ollama -v
```

> 请注意：这种安装方式需要服务器保持联网状态以自动下载 Ollama 的二进制文件，如果出现下述报错，则说明网络环境不同，需要根据实际情况处理网络连接。
![](https://snowball101.oss-cn-beijing.aliyuncs.com/img/202403081606383.png)
{: .prompt-tip }

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502111858360.png)

至此，已经成功完成 Ollama 项目的本地部署，并顺利启动了 Ollama 服务。


## Ollama 下载 DeepSeek R1 及启动

> 需要说明的一点是：`Ollama`项目虽然提供了本地化大模型的能力，但这并不意味着所有大模型都可以通过它下载和使用。其支持的大模型的详细列表可在`Ollama`的官方模型库页面查看：[https://ollama.com/library](https://ollama.com/library)。
![Ollama 支持的大模型](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502121017505.png)
{: .prompt-tip }


在 `Ollama` 的模型库中主要支持的还是 `LLaMA` 架构的一些主流大模型，并且现在已经全面接入了 `DeepSeek R1` 满血版模型及其蒸馏的小模型，可以进入如下页面查看所有可使用的 `DeepSeek` 模型。注意：Ollama 暂时没有接入 `DeepSeek V3` 模型 

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502131352604.png)

在进入大模型的详细页面后，可以通过下拉菜单选择不同参数量的大模型版本。然后需要复制页面右侧提供的模型标识符进行下一步的模型下载操作。

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502131430011.png)

接下来回到服务器的命令行终端，直接复制并运行此命令即可执行 `DeepSeek R1`模型文件的自动化下载，执行的具体命令如下：

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502131429889.png)

上诉命令会自动执行 `deepseek-r1:32b` 模型的下载过程。当下载任务完成后，大模型的全部文件的存储路径在不同操作系统的位置如下：
- 在 Linux 系统，`/usr/share/ollama/.ollama/models` 路径中；
- 在 Mac 系统，`~/.ollama/models` 路径中；
- 在 Windows 系统，`C:\Users\%username%\.ollama\models` 路径中。

同时，进一步进入子文件，即可找到下载模型的具体标识：
![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502131434757.png)

`Ollama` 下载的模型是 `GGUF` 格式。 `GGUF`（Generalized Graph Universal Format） 是一种用于存储和表示模型的格式。它与原版开源模型的关系是：
- 首先下载原版的开源模型（例如这里的 `DeepSeek-R1-Distill-Qwen-32B`）
- 通过转化脚本将原本开源模型被转换未 `GGUF` 格式
- 将 `GGUF` 格式的模型文件量化为较低的精度

在 `Ollama` 中，最常用的量化类型是 `Q4_K_M`，表示 `4-bit` 量化，旨在保持较高性能的同时减少模型的存储要求。

此外，还可以使用命令 `ollama list` 来直接查看通过 `Ollama` 下载的大模型文件列表，这些模型都支持在线启动和调用。

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502131436153.png)


## Ollama 启动和使用方法

在 `Ollama` 的机制中，使用 `run` 命令时，系统会首先检查本地是否已经存在指定模型，如果本地没有找到该模型，`Ollama` 会自动执行 `ollama pull <model_name>` 命令，从远程仓库下载该模型，下载完成后将该模型存储为 `GGUF` 格式，供后续使用。最后，当成功下载后，`Ollama` 会继续执行 `run` 命令，启动模型并进行推理或生成任务。因此是可以直接通过在命令行终端对启动的大模型进行调用的，如下所示:

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502131629723.png)

> 这里需要重点说明两点：<br/>
1. `DeepSeek R1`作为推理模型，其返回结果是包含`<think></think>`的，里面包含的是思考推理的内容.<br/>
2. 会存在`<think></think>`中为空，这其实是因为`DeepSeek-R1`系列模型倾向于绕过思维模式（即输出`\n\n`）,因此一个使用的技巧是：每个输出的开头强制模型以 `<think>\n` 开头。
{: .prompt-tip }


## Ollama 多 GPU 部署及 server 启动

使用最简单的命令，即 `ollama run xxxx` 时，`Ollama` 的内部机制会根据启动模型的参数量去运行该模型所需的 VRAM（显存）。如果该模型可以使用单个 `GPU` 加载，则 `Ollama` 将在该 `GPU` 上加载该模型。这种方式一般可以提供出最佳的性能，因为它可以减少推理过程中 PCI 总线的数据传输量。

如果该模型没办法仅在一个 GPU 上加载，则将分布在所有可用的 `GPU` 中，比如根据官网的介绍，`DeepSeek-r1:32b` 模型需要占用 `20GB` 显存。
![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502131648407.png)

实际也确实在运行在了单张 `3090 GPU` 上，占用约 21GB 显存，如下：

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502131648408.png)

如果你想加载多张显卡且做到负载均衡，可以修改 `ollama` 的 `SystemD` 配置服务，操作步骤如下：
1. 找到当前服务器上 GPU 的 ID，执行命令：
    
    ```bash
        nvidia-smi
    ```
    
    ![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502131709312.png)

2. 执行 `systemctl edit ollama.service` 命令修改 `ollama` 的 `SystemD` 配置服务:

    ```bash
        systemctl edit ollama.service
    ```

    ![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502121127759.png)

3. 编辑并填写以下内容：

    ```bash
        Environment="CUDA_VISIBLE_DEVICES=0,1,2,3"    # 这里根据你自己实际的 GPU标号来进行修改
        Environment="OLLAMA_SCHED_SPREAD=1"           # 这个参数是做负载均衡
    ```

    ![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502131711393.png)

    保存退出后，重新加载 `systemd` 并重新启动 `Ollama` 服务使其配置生效，执行如下命令：

    ```bash
        systemctl daemon-reload
        systemctl restart ollama
    ```

    ![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502121127761.png)

此时再次通过 `ollama run xxx` 即可分布式的加载到多张 `GPU` 显卡上，如下所示：

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502131716696.png)


## Ollama REST API 服务启动及调用

`ollama run xxx` 命令启动模型后，不仅仅是可以在命令行终端与启动的大模型进行对话，更重要的是它还会同步启动 Ollama REST API。这个 REST API 服务简单理解为：你可以通过某种方式在代码环境中调用到使用 `Ollama` 模型启动的大模型，从而和大模型进行对话。

默认绑定的 `IP + Port` 是：`http://localhost:11434`，所以，如果启动 `Ollama` 的服务和当前环境是同一台机器的话，可以使用如下代码进行快速的调用测试：

```python
from openai import OpenAI

client = OpenAI(
    base_url='http://localhost:11434/v1/',      
    api_key='ollama',  # 这里随便写，但是api_key字段一定要有
)

chat_completion = client.chat.completions.create(
    model='deepseek-r1:32b',       # 这里要修改成 你 ollama 启动模型的名称
    messages=[
        {
            'role': 'user',
            'content': '你好，请你介绍一下你自己',
        }
    ],
)

print(chat_completion)
```

```Response
---------------------------------------------------------------------------
RemoteProtocolError                       Traceback (most recent call last)
File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\httpx\_transports\default.py:101, in map_httpcore_exceptions()
    100 try:
--> 101     yield
    102 except Exception as exc:

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\httpx\_transports\default.py:250, in HTTPTransport.handle_request(self, request)
    249 with map_httpcore_exceptions():
--> 250     resp = self._pool.handle_request(req)
    252 assert isinstance(resp.stream, typing.Iterable)

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\httpcore\_sync\connection_pool.py:256, in ConnectionPool.handle_request(self, request)
    255     self._close_connections(closing)
--> 256     raise exc from None
    258 # Return the response. Note that in this case we still have to manage
    259 # the point at which the response is closed.

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\httpcore\_sync\connection_pool.py:236, in ConnectionPool.handle_request(self, request)
    234 try:
    235     # Send the request on the assigned connection.
--> 236     response = connection.handle_request(
    237         pool_request.request
    238     )
    239 except ConnectionNotAvailable:
    240     # In some cases a connection may initially be available to
    241     # handle a request, but then become unavailable.
    242     #
    243     # In this case we clear the connection and try again.

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\httpcore\_sync\http_proxy.py:206, in ForwardHTTPConnection.handle_request(self, request)
    199 proxy_request = Request(
    200     method=request.method,
    201     url=url,
   (...)
    204     extensions=request.extensions,
    205 )
--> 206 return self._connection.handle_request(proxy_request)

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\httpcore\_sync\connection.py:103, in HTTPConnection.handle_request(self, request)
    101     raise exc
--> 103 return self._connection.handle_request(request)

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\httpcore\_sync\http11.py:136, in HTTP11Connection.handle_request(self, request)
    135         self._response_closed()
--> 136 raise exc

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\httpcore\_sync\http11.py:106, in HTTP11Connection.handle_request(self, request)
     97 with Trace(
     98     "receive_response_headers", logger, request, kwargs
     99 ) as trace:
    100     (
    101         http_version,
    102         status,
    103         reason_phrase,
    104         headers,
    105         trailing_data,
--> 106     ) = self._receive_response_headers(**kwargs)
    107     trace.return_value = (
    108         http_version,
    109         status,
    110         reason_phrase,
    111         headers,
    112     )

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\httpcore\_sync\http11.py:177, in HTTP11Connection._receive_response_headers(self, request)
    176 while True:
--> 177     event = self._receive_event(timeout=timeout)
    178     if isinstance(event, h11.Response):

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\httpcore\_sync\http11.py:231, in HTTP11Connection._receive_event(self, timeout)
    230     msg = "Server disconnected without sending a response."
--> 231     raise RemoteProtocolError(msg)
    233 self._h11_state.receive_data(data)

RemoteProtocolError: Server disconnected without sending a response.

The above exception was the direct cause of the following exception:

RemoteProtocolError                       Traceback (most recent call last)
File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\openai\_base_client.py:1003, in SyncAPIClient._request(self, cast_to, options, retries_taken, stream, stream_cls)
   1002 try:
-> 1003     response = self._client.send(
   1004         request,
   1005         stream=stream or self._should_stream_response_body(request=request),
   1006         **kwargs,
   1007     )
   1008 except httpx.TimeoutException as err:

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\httpx\_client.py:914, in Client.send(self, request, stream, auth, follow_redirects)
    912 auth = self._build_request_auth(request, auth)
--> 914 response = self._send_handling_auth(
    915     request,
    916     auth=auth,
    917     follow_redirects=follow_redirects,
    918     history=[],
    919 )
    920 try:

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\httpx\_client.py:942, in Client._send_handling_auth(self, request, auth, follow_redirects, history)
    941 while True:
--> 942     response = self._send_handling_redirects(
    943         request,
    944         follow_redirects=follow_redirects,
    945         history=history,
    946     )
    947     try:

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\httpx\_client.py:979, in Client._send_handling_redirects(self, request, follow_redirects, history)
    977     hook(request)
--> 979 response = self._send_single_request(request)
    980 try:

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\httpx\_client.py:1014, in Client._send_single_request(self, request)
   1013 with request_context(request=request):
-> 1014     response = transport.handle_request(request)
   1016 assert isinstance(response.stream, SyncByteStream)

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\httpx\_transports\default.py:249, in HTTPTransport.handle_request(self, request)
    237 req = httpcore.Request(
    238     method=request.method,
    239     url=httpcore.URL(
   (...)
    247     extensions=request.extensions,
    248 )
--> 249 with map_httpcore_exceptions():
    250     resp = self._pool.handle_request(req)

File C:\Python312\Lib\contextlib.py:158, in _GeneratorContextManager.__exit__(self, typ, value, traceback)
    157 try:
--> 158     self.gen.throw(value)
    159 except StopIteration as exc:
    160     # Suppress StopIteration *unless* it's the same exception that
    161     # was passed to throw().  This prevents a StopIteration
    162     # raised inside the "with" statement from being suppressed.

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\httpx\_transports\default.py:118, in map_httpcore_exceptions()
    117 message = str(exc)
--> 118 raise mapped_exc(message) from exc

RemoteProtocolError: Server disconnected without sending a response.

The above exception was the direct cause of the following exception:

APIConnectionError                        Traceback (most recent call last)
Cell In[1], line 8
      1 from openai import OpenAI
      3 client = OpenAI(
      4     base_url='http://localhost:11434/v1/',      
      5     api_key='ollama',  # 这里随便写，但是api_key字段一定要有
      6 )
----> 8 chat_completion = client.chat.completions.create(
      9     model='deepseek-r1:32b',       # 这里要修改成 你 ollama 启动模型的名称
     10     messages=[
     11         {
     12             'role': 'user',
     13             'content': '你好，请你介绍一下你自己',
     14         }
     15     ],
     16 )
     18 print(chat_completion)

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\openai\_utils\_utils.py:279, in required_args.<locals>.inner.<locals>.wrapper(*args, **kwargs)
    277             msg = f"Missing required argument: {quote(missing[0])}"
    278     raise TypeError(msg)
--> 279 return func(*args, **kwargs)

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\openai\resources\chat\completions.py:863, in Completions.create(self, messages, model, audio, frequency_penalty, function_call, functions, logit_bias, logprobs, max_completion_tokens, max_tokens, metadata, modalities, n, parallel_tool_calls, prediction, presence_penalty, reasoning_effort, response_format, seed, service_tier, stop, store, stream, stream_options, temperature, tool_choice, tools, top_logprobs, top_p, user, extra_headers, extra_query, extra_body, timeout)
    821 @required_args(["messages", "model"], ["messages", "model", "stream"])
    822 def create(
    823     self,
   (...)
    860     timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    861 ) -> ChatCompletion | Stream[ChatCompletionChunk]:
    862     validate_response_format(response_format)
--> 863     return self._post(
    864         "/chat/completions",
    865         body=maybe_transform(
    866             {
    867                 "messages": messages,
    868                 "model": model,
    869                 "audio": audio,
    870                 "frequency_penalty": frequency_penalty,
    871                 "function_call": function_call,
    872                 "functions": functions,
    873                 "logit_bias": logit_bias,
    874                 "logprobs": logprobs,
    875                 "max_completion_tokens": max_completion_tokens,
    876                 "max_tokens": max_tokens,
    877                 "metadata": metadata,
    878                 "modalities": modalities,
    879                 "n": n,
    880                 "parallel_tool_calls": parallel_tool_calls,
    881                 "prediction": prediction,
    882                 "presence_penalty": presence_penalty,
    883                 "reasoning_effort": reasoning_effort,
    884                 "response_format": response_format,
    885                 "seed": seed,
    886                 "service_tier": service_tier,
    887                 "stop": stop,
    888                 "store": store,
    889                 "stream": stream,
    890                 "stream_options": stream_options,
    891                 "temperature": temperature,
    892                 "tool_choice": tool_choice,
    893                 "tools": tools,
    894                 "top_logprobs": top_logprobs,
    895                 "top_p": top_p,
    896                 "user": user,
    897             },
    898             completion_create_params.CompletionCreateParams,
    899         ),
    900         options=make_request_options(
    901             extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
    902         ),
    903         cast_to=ChatCompletion,
    904         stream=stream or False,
    905         stream_cls=Stream[ChatCompletionChunk],
    906     )

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\openai\_base_client.py:1290, in SyncAPIClient.post(self, path, cast_to, body, options, files, stream, stream_cls)
   1276 def post(
   1277     self,
   1278     path: str,
   (...)
   1285     stream_cls: type[_StreamT] | None = None,
   1286 ) -> ResponseT | _StreamT:
   1287     opts = FinalRequestOptions.construct(
   1288         method="post", url=path, json_data=body, files=to_httpx_files(files), **options
   1289     )
-> 1290     return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\openai\_base_client.py:967, in SyncAPIClient.request(self, cast_to, options, remaining_retries, stream, stream_cls)
    964 else:
    965     retries_taken = 0
--> 967 return self._request(
    968     cast_to=cast_to,
    969     options=options,
    970     stream=stream,
    971     stream_cls=stream_cls,
    972     retries_taken=retries_taken,
    973 )

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\openai\_base_client.py:1027, in SyncAPIClient._request(self, cast_to, options, retries_taken, stream, stream_cls)
   1024 log.debug("Encountered Exception", exc_info=True)
   1026 if remaining_retries > 0:
-> 1027     return self._retry_request(
   1028         input_options,
   1029         cast_to,
   1030         retries_taken=retries_taken,
   1031         stream=stream,
   1032         stream_cls=stream_cls,
   1033         response_headers=None,
   1034     )
   1036 log.debug("Raising connection error")
   1037 raise APIConnectionError(request=request) from err

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\openai\_base_client.py:1105, in SyncAPIClient._retry_request(self, options, cast_to, retries_taken, response_headers, stream, stream_cls)
   1101 # In a synchronous context we are blocking the entire thread. Up to the library user to run the client in a
   1102 # different thread if necessary.
   1103 time.sleep(timeout)
-> 1105 return self._request(
   1106     options=options,
   1107     cast_to=cast_to,
   1108     retries_taken=retries_taken + 1,
   1109     stream=stream,
   1110     stream_cls=stream_cls,
   1111 )

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\openai\_base_client.py:1027, in SyncAPIClient._request(self, cast_to, options, retries_taken, stream, stream_cls)
   1024 log.debug("Encountered Exception", exc_info=True)
   1026 if remaining_retries > 0:
-> 1027     return self._retry_request(
   1028         input_options,
   1029         cast_to,
   1030         retries_taken=retries_taken,
   1031         stream=stream,
   1032         stream_cls=stream_cls,
   1033         response_headers=None,
   1034     )
   1036 log.debug("Raising connection error")
   1037 raise APIConnectionError(request=request) from err

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\openai\_base_client.py:1105, in SyncAPIClient._retry_request(self, options, cast_to, retries_taken, response_headers, stream, stream_cls)
   1101 # In a synchronous context we are blocking the entire thread. Up to the library user to run the client in a
   1102 # different thread if necessary.
   1103 time.sleep(timeout)
-> 1105 return self._request(
   1106     options=options,
   1107     cast_to=cast_to,
   1108     retries_taken=retries_taken + 1,
   1109     stream=stream,
   1110     stream_cls=stream_cls,
   1111 )

File e:\01_木羽研发\04_Agent正课\【项目开发实战】DeepSeek 项目开发\fufan_deepseek_agent\.venv\Lib\site-packages\openai\_base_client.py:1037, in SyncAPIClient._request(self, cast_to, options, retries_taken, stream, stream_cls)
   1027         return self._retry_request(
   1028             input_options,
   1029             cast_to,
   (...)
   1033             response_headers=None,
   1034         )
   1036     log.debug("Raising connection error")
-> 1037     raise APIConnectionError(request=request) from err
   1039 log.debug(
   1040     'HTTP Response: %s %s "%i %s" %s',
   1041     request.method,
   (...)
   1045     response.headers,
   1046 )
   1047 log.debug("request_id: %s", response.headers.get("x-request-id"))

APIConnectionError: Connection error.
```

这里需要注意的是：如果 `Ollama` 启动和执行调用的代码是同一台机器，上述代码是可以的跑通的。

如果`Ollama`服务在云服务器、局域网的服务器上等情况，则无法通过`http://localhost:11434/v1/` 来进行访问，因为**网络不通**。 

正如上述的报错，我的`Ollama`模型服务是在局域网的服务器上，因此我需要修改`Ollama REST API`的请求地址，操作方法如下：

1. 修改 `ollama` 的`SystemD`配置服务，执行如下代码：
    ```bash
        systemctl edit ollama.service
    ```

    ![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502121127759.png)

2. 编辑并填写如下内容：
    ```bash
        Environment="OLLAMA_HOST=0.0.0.0：11434" 
    ```

    ![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502121127760.png)

3. 保存退出后，重新加载`systemd`并重新启动`Ollama`服务使其配置生效，执行如下命令：
    ```bash
        systemctl daemon-reload
        systemctl restart ollama.service 
        # or systemctl restart ollama
    ```

    ![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502121127761.png)


使用`ollama run xxx`启动模型。然后找到服务器可访问的有效`IP`。在 `Linux` 系统中，可以通过多种方式查看有效的访问 `IP` 地址（即当前与系统建立连接或尝试访问系统的远程 `IP` 地址）。这里使用如下命令：

```bash
    sudo netstat -tn | grep ESTABLISHED
```

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502121127763.png)

因此，修改访问`Ollama`的`REST API`地址，如下所示：

```python
from openai import OpenAI

client = OpenAI(
    base_url='http://192.168.110.131:11434/v1/',     # 这里修改成可访问的 IP
    api_key='ollama',   # 这里随便写，但是api_key字段一定要有
)

chat_completion = client.chat.completions.create(
    model='deepseek-r1:32b',
    messages=[
        {
            'role': 'user',
            'content': '你好，请你介绍一下你自己',
        }
    ],
)

print(chat_completion)
```

```Response
ChatCompletion(id='chatcmpl-309', choices=[Choice(finish_reason='stop', index=0, logprobs=None, message=ChatCompletionMessage(content='<think>\n我是DeepSeek-R1，一个由深度求索公司开发的智能助手，我会尽我所能为您提供帮助。\n</think>\n\n我是DeepSeek-R1，一个由深度求索公司开发的智能助手，我会尽我所能为您提供帮助。', refusal=None, role='assistant', audio=None, function_call=None, tool_calls=None))], created=1739439431, model='deepseek-r1:32b', object='chat.completion', service_tier=None, system_fingerprint='fp_ollama', usage=CompletionUsage(completion_tokens=53, prompt_tokens=8, total_tokens=61, completion_tokens_details=None, prompt_tokens_details=None))
```

```python
print(chat_completion.choices[0].message.content)
```

```Response
<think>
我是DeepSeek-R1，一个由深度求索公司开发的智能助手，我会尽我所能为您提供帮助。
</think>

我是DeepSeek-R1，一个由深度求索公司开发的智能助手，我会尽我所能为您提供帮助。
```

至此，我们就可以像访问大模型`在线API`一样调用本地通过`Ollama`启动的`DeepSeek`模型了。而关于数据隐私问题，因为`Ollama`在本地服务器运行，因此所有的对话数据不会离开机器，大家无需担心隐私数据泄露问题。

同时，`Ollama`还有其他的一些常见操作命令，也都非常直观易懂，如下所示：

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502131741282.png)

`Ollama` 每个参数命令说明整理如下所示：

| 命令       | 描述                                   |
|------------|----------------------------------------|
| `serve`    | 启动 Ollama 服务                       |
| `create`   | 从 Modelfile 创建一个模型             |
| `show`     | 显示模型的信息                         |
| `run`      | 运行一个模型                           |
| `stop`     | 停止正在运行的模型                     |
| `pull`     | 从注册表中拉取一个模型                 |
| `push`     | 将一个模型推送到注册表                 |
| `list`     | 列出所有模型                           |
| `ps`       | 列出正在运行的模型                     |
| `cp`       | 复制一个模型                           |
| `rm`       | 删除一个模型                           |
| `help`     | 显示关于任何命令的帮助信息             |

通过上述关于`Ollama`的安装、模型下载及启动推理的介绍和实践，我们可以感受到`Ollama`极大地简化了大模型部署的过程，也降低了大模型在使用上的技术门槛。然而，对大部分用户而言，命令行界面并不够友好。正如我们之前提到的，在大模型的应用开发框架下，使用到的往往是其`API`调用形式，为此，`Ollama`也是可以集成多个开源项目，包括`Web`界面、桌面应用和终端工具等方式提升使用体验，并满足满足不同用户的偏好和需求。