---
title: Dify对接企业微信：智能对话与人工客服无缝转接
description: Dify对接企业微信实现智能对话与人工客服转接，包含access_token自动管理、企业微信集成、域名配置等完整方案。
author: hsc
date: 2025-03-29 10:00:00 +0800
categories: [AI Agent, 低代码平台, Dify]
tags: [Dify, 企业微信, 客服转接, access_token, 智能对话, 人工客服]
math: true
mermaid: true
---

# 背景
之前场景中已经构建了，如何让微信生态接入dify对话流中，其中包含了知识库的语音及文字问答回复状况。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250218002103854_ffe7d7eb.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250218002122169_0ed5f929.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250220113118320_269855b3.png)
如果有人出现疑问或者出现购买意向，或者找人工服务，用户很难去针对每个聊天用户的对话框挨个查看及时获取用户的问题。
# 1.人工客服转接
原有销售测试链路上增加意图识别，当用户想要找人工客服的时候直接通过与当前对话机器人说明就可以对客服人员进行呼叫。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225111918379_544b0ebf.png)
额外必备条件：企业微信、企业备案域名+服务器
## 1 微信端准备
https://work.weixin.qq.com/wework_admin/loginpage_wx?from=myhome   企微登录链接
### corpid

每个企业都拥有唯一的corpid，获取此信息可在管理后台“我的企业”－“企业信息”下查看“企业ID”（需要有管理员权限）
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225113740301_9ad8765a.png)




### secret

secret是企业应用里面用于保障数据安全的“钥匙”，每一个应用都有一个独立的访问密钥，为了保证数据的安全，secret务必不能泄漏。secret查看方法：
在管理后台->“应用管理”->“应用”->“自建”，点进某个应用，即可看到。


![image](/assets/img/posts/low-code-dify-coze-12/image-20250218194334054_a2afe55b.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250218194421747_31c54a74.png)

记住Agentid与Secret，可见范围出要录入你需要人工信息通知的用户。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250218202417958_09ba675d.png)

会将Secret发送到企业微信中，需要管理员才能看到。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250218194922182_0edfc506.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250218194951744_1572f666.png)

### 获取access_token
https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={你的corpid}&corpsecret={你的secret}  获取 `access_token`
官方说明文档 https://developer.work.weixin.qq.com/document/path/91039

```json
{
  "status_code": 200,
  "body": "{\"errcode\":0,\"errmsg\":\"ok\",\"access_token\":\"Q62v70XvgdHOyQiTxOQX9I46Bz1LNcVYpy9ufYPs7wpas5oHljZb9fBNWG_f0qPfNeMsr-nJd6BTZLCGlYYsjPdZdAnoOqZVhDJey9tJRmZIHK0O-FRzYAHvA-HxjRSKbNyPFC8h9-ikygXxbRR5fL8fZnJeCA\",\"expires_in\":7200}",
  "headers": {
​    "date": "Tue, 18 Feb 2025 11:57:22 GMT",
​    "content-type": "application/json; charset=UTF-8",
​    "content-length": "277",
​    "connection": "keep-alive",
​    "server": "nginx",
​    "error-code": "0",
​    "error-msg": "ok",
​    "x-w-no": "6"
  },
  "files": []
}
```
|参数|说明|
|---|---|
|errcode	|出错返回码，为0表示成功，非0表示调用失败|
|errmsg	|返回码提示语|
|access_token	|获取到的凭证，最长为512字节|
|expires_in	|凭证的有效时间（秒）|
尝试给指定用户发送信息。
```json
https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={上边获取到.access_token}
-header  Content-Type:application/json
{
    "touser": "{应用可见范围内企业微信id}",
    "msgtype": "text",
    "agentid": {应用中获取到的agentid},
    "text": {
        "content": "这是测试信息！"
    }
}
```
带入dify节点
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225121342391_e8f69f3a.png)

常见问题：60020报错：没有设置可信ip
![image](/assets/img/posts/low-code-dify-coze-12/image-20250218204823501_d3b0e1c4.png)

返回应用中，拉倒最下边
![image](/assets/img/posts/low-code-dify-coze-12/image-20250218205342949_144b1185.png)

查验当前环境国内公网IP
- [https://www.whatismyip.com](https://www.whatismyip.com/)  
- [https://ipinfo.io](https://ipinfo.io/)   
- [https://ifconfig.me](https://ifconfig.me/)   
![image](/assets/img/posts/low-code-dify-coze-12/image-20250224115002238_e6111ea9.png)

直接录入公网IP地址
![image](/assets/img/posts/low-code-dify-coze-12/image-20250218205610176_d714856e.png)

如果没有设置可信域名需要先设置可信域名，可以点击设置可信域名超链接直接跳转，也可以在网页授权设置可信域名。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225144737067_c373c53d.png)

正常设置完成可信域名与公网IP的状况。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225145147273_50d747a8.png)
如果设置可信域名报错。需要进行申请校验域名。将文件上传到域名绑定云服务器下的根目录中。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225145920947_27766e07.png)
保证在浏览器中输入域名+对应文件名能够访问到下载文件中的内容。    

http://你的域名/WW_verify_tvUR.txt
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225201158773_be5d9dbd.png)
## 2.域名端准备
如果没有域名需要先进行购买(需要绑定企业主体)，本次以阿里云为例。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225151606214_67b02c57.png)
购买域名后总览。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225151733317_9cd9f604.png)

域名需要是实名认证后续方便进行检验。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225151830133_b0e9a4e9.png)

认证完成后需要进行icp备案
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225153145626_5d8cd006.png)

点击后进行跳转自行备案即可，如果已经备案不需重复备案。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225153302921_b6870b5c.png)

备案完成后需要进行DNS解析，需要将你的域名绑定到你指定的云服务器地址中。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225152642235_7bbb22d9.png)

建议安装宝塔系统+**Ubuntu**
可以选择系统时候直接安装上宝塔系统    
Ubuntu手动安装宝塔命令  wget -O install.sh http://download.bt.cn/install/install-ubuntu_6.0.sh && sudo bash install.sh
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225154741068_7e3d45b6.png)

实例信息
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225155206702_63351699.png)

申请SSl证书(个人测试可以申请免费证书，SSL证书可选，但是推荐)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225152752316_4d99e7c3.png)

保证ping 域名时候显示你的云服务器ip即可

回到云服务器ip进行域名配置。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225155937879_c062a02f.png)
根据安装宝塔信息打开界面登陆(可能涉及到端口问题，需要再租赁实例的安全组中进行端口添加)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225161441266_34c14d3e.png)
点击网站一栏，选择安装nginx可以直接访问
![image](/assets/img/posts/low-code-dify-coze-12/image-20250223144838575_2f33a08b.png)

点击添加站点，将域名写入，并记住根目录位置。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250223150535329_de13b858.png)

添加完成。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250223150614194_be70aa92.png)

将在微信中设置可信域名的验证文件进行下载后上传到当前网站的根目录下。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250223151230400_22d8fce3.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250225162056513_b911ac19.png)

上传完成
![image](/assets/img/posts/low-code-dify-coze-12/image-20250223152417890_5dd94316.png)

SSl证书，可以使用上边同一域名解析过的。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250223152453496_4205cdbf.png)

也可以使用宝塔中免费申请。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250223152533055_6d78075e.png)

注意：当前界面使用的账户名需要和在宝塔官网注册的账号信息一致。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250223152949873_c754ef05.png)

登录与宝塔相同账号

![image](/assets/img/posts/low-code-dify-coze-12/image-20250223170908021_7ca5f77f.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250223172239236_9ebae3a7.png)

将当前域名上传到企业微信可信域名授权中
![image](/assets/img/posts/low-code-dify-coze-12/image-20250224114338319_6d918a64.png)

设置IP白名单。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250224115013463_d068decd.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250224115029660_ecbbec9e.png)

进行单点验证。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225121342391_e8f69f3a.png)
## 3.链路拆解
全链路概览：增加输入内容-》意图分析增加人工选项-》判断access_token的状态-》根据状态做条件分发-》方向1、状态过期重新请求生成access_token-》使用变量存储-》最终回归方向2：信息发送-》界面返回。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225164119854_38249816.png)

开始节点增加捕获信息，用户id及群聊相关内容。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225172540084_c0a6c928.png)

通过当前时间是否大于access_token产生时间+2小时判断是否过期
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225232909607_2337e74a.png)

判断access_token是否有效 当前逻辑包含false为token无效
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225164258372_e4115007.png)

开始重新生成access_token流程然后发送信息
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225164359475_0c422104.png)

https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=  &corpsecret=

![image](/assets/img/posts/low-code-dify-coze-12/image-20250225164459285_e0d08c46.png)

获取上游产生的access_token信息及产生时间
```python
# 代码仅供参考
import json
from datetime import datetime

def main(body, headers):
​    try:
​        # 判断body类型并相应处理
​        if isinstance(body, str):
​            acbody = json.loads(body)
​        else:
​            acbody = body
​        # 判断headers类型并相应处理
​        if isinstance(headers, str):
​            acheaders = json.loads(headers)
​        else:
​            acheaders = headers
​        # 获取access_token
​        access_token = acbody['access_token']
​        # 获取headers中的date并转换为时间戳
​        date_str = acheaders['date']
​        # 将GMT时间字符串转换为datetime对象
​        date_obj = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S GMT')
​        # 转换为时间戳（秒级）
​        timestamp = int(date_obj.timestamp())
​        return {
​            'access_token': access_token,
​            'timestamp': timestamp
​        }
​    except Exception as e:
​        print(f"Error: {str(e)}")
​        return None

```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225164558184_3de0c566.png)

更新变量，方便下一轮进行判断。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225164631336_fa101c3d.png)

给指定用户发送信息。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225164804104_dc94bf70.png)

最终输出，会给发信人一个基本回答。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225164824300_24107241.png)
# 2.呼叫测试
## 个微
使用个人微信登录对话流，群聊中直接@登录账户名称。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225172347678_552318be.png)

个微直接对话，呼叫人工客服。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225172406053_4bba086f.png)

被指定人会在企微中收到指定自建应用中的信息(用户存在于企微自建中)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225172450954_d5221d9e.png)
## 企微
### 企微安装
当前只做了window环境验证
重新安装dify-on-wechat项目
python环境建议3.10  ： conda create -n wework python=3.10 -y

![image](/assets/img/posts/low-code-dify-coze-12/image-20250224160331959_bdf06af2.png)

正常安装dify-on-wechat项目
pip install -r requirements.txt  -i https://mirrors.aliyun.com/pypi/simple

![image](/assets/img/posts/low-code-dify-coze-12/image-20250224160741745_f0a2901f.png)

pip install -r requirements-optional.txt  -i https://mirrors.aliyun.com/pypi/simple

![image](/assets/img/posts/low-code-dify-coze-12/image-20250224161107319_53e00e15.png)

额外需要安装ntwork依赖选择好对应的python版本以及当前电脑64或者32位。
https://github.com/hanfangyuan4396/ntwork-bin-backup/tree/main/ntwork-whl

![image](/assets/img/posts/low-code-dify-coze-12/image-20250224162830640_81ed57bd.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250224162924949_1ac0f3c2.png)

pip install 绝对路径\ntwork-0.1.3-cp310-cp310-win_amd64.whl

![image](/assets/img/posts/low-code-dify-coze-12/image-20250224163017589_7f96321d.png)

```json
# 从阿里云镜像仓库拉取(国内" width=100%></div>
docker pull registry.cn-chengdu.aliyuncs.com/tu1h/wechotd:alpine
docker tag registry.cn-chengdu.aliyuncs.com/tu1h/wechotd:alpine gewe

# 创建数据目录并启动服务
mkdir -p gewechat/data  
docker run -itd -v 绝对路径(包含gewechat/data):/root/temp -p 2531:2531 -p 2532:2532 --restart=always --name=gewe gewe
```
例如：docker run -itd -v C:\Users\FF\Downloads\dify-on-wechat\gewechat\data:/root/temp -p 2531:2531 -p 2532:2532 --restart=always --name=gewe gewe
![image](/assets/img/posts/low-code-dify-coze-12/image-20250224164525429_df270acb.png)

企微下载地址


需要下载指定版本：https://dldir1.qq.com/wework/work_weixin/WeCom_4.0.8.6027.exe

![image](/assets/img/posts/low-code-dify-coze-12/image-20250224155953910_fff58204.png)

注意如果使用老版本的企微手机扫描登录微信后显示版本过低无法登陆。
解决办法：下载一个新版本企微桌面版。安装完成后再次安装老版本进行新版本覆盖(安装路径要相同)。
https://work.weixin.qq.com/#indexDownload

![image](/assets/img/posts/low-code-dify-coze-12/image-20250224161926203_fc0303d3.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250224162257290_75962e32.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250224163149338_104b4952.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250224163350664_46a722b8.png)
企微登录完成后进行config.json更改
![image](/assets/img/posts/low-code-dify-coze-12/image-20250224165821040_bc54a9b0.png)

 注意企微对应的是："channel_type": "wework",
```json
{ 
 "dify_api_base": "http://localhost/v1",
 "dify_api_key": "app-4cMl1lw5Hxi4SUUdMxqegEjF",
 "dify_app_type": "chatbot",
 "channel_type": "wework",
 "model": "dify",
 "single_chat_prefix": [""],
 "single_chat_reply_prefix": "",
 "group_chat_prefix": ["@bot"],
 "group_name_white_list": ["ALL_GROUP"]
}
```
执行启动命令：python app.py

![image](/assets/img/posts/low-code-dify-coze-12/image-20250224170013920_0a3cc040.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250224170035725_fae85a89.png)

等待初始化完成之后可以进行测试
![image](/assets/img/posts/low-code-dify-coze-12/image-20250224180407974_552d15ca.png)

测试过程中后端信息。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225183433445_a06cbf95.png)

个人微信用户与企业微信用户对话
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225185610075_43a3c823.png)

群聊中企微用户@企微登录用户。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225185651094_b160d02d.png)

企微中被指定发送人收到的应用信息。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250225185741857_a393d894.png)

# 3.总结
![image](/assets/img/posts/low-code-dify-coze-12/image-20250226150543535_1e1411f2.png)