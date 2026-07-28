---
title: Linux服务器源码部署Dify：从零构建RAG知识库应用
description: 源码部署Dify构建RAG应用，包括服务器租赁、CUDA环境配置、Docker安装、Poetry依赖管理及xinference多引擎模型配置。
author: hsc
date: 2025-03-11 10:00:00 +0800
categories: [AI Agent, 低代码平台, Dify]
tags: [Dify, RAG, 源码部署, xinference, 向量数据库, 知识库, Linux]
math: true
mermaid: true
---

上节课在本地window环境对Dify使用Docker进行了部署，同时部署了xinference[all]本节课带领大家如何在服务器环境中进行Dify的源码部署。并且对xinference 进行细化安装，避免资源浪费。
具体选用Docker或源码安装需要大家根据自己实际使用情况进行选择。
# 1. 基础环境
## 1.1 租赁服务器
大家可以根据自己习惯进行服务器租赁，但是不建议直接使用类似AutoDL这种docker容器构成的镜像环境，后续无法直接安装docker。
本次使用服务器租赁地址为：https://www.compshare.cn/        

[直接注册地址](https://passport.compshare.cn/register?referral_code=Gkp7G2YRdxfEcI5fG6AWRr)   
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107161554287_fed392b0.png)
[直接注册地址](https://passport.compshare.cn/register?referral_code=Gkp7G2YRdxfEcI5fG6AWRr)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107161617651_c33cb433.png)
登录后进行GPU实例部署
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107161701531_988f8801.png)
建议选择按量付费，同时租赁服务器需要进行实名认证，大家自行选择实名认证的方式即可。

算力选择大家根据自己需求安排。

对应系统选择直接选择系统镜像，如果选择基础镜像安装docker等组件很难套用。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107161848643_86ce4d65.png)
自行进行预充值存储
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107161907652_527476d7.png)
充值完成后，点击创建，进入初始化阶段。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107162050726_53a32be9.png)
初始化完成
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107162126645_b3e675da.png)
点击登录，不建议直接使用界面登录，可以获取用户名
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107162150801_67c55a43.png)
大家自行选择使用什么插件进行登录 我当前使用的是ZenTermLite，大家可以使用xshell等组件。看个人习惯。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108110837517_cf66d53b.png)
复制上边展示的用户名、密码、端口、IP地址，自行使用远程连接的的方式进行登录。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107162342269_e09f5f8f.png)
选择保存密码
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107162357993_059dbb5b.png)
本地连接创建完成
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107162420433_30a34f35.png)
查看显卡信息 nvidia-smi
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107162438834_12691af3.png)
## 1.2 安装驱动与CUDA
建议CUDA版本在12.4及以上，新版本xinference支持较好
1. 首先，卸载现有的 CUDA 安装：
```bash
# 删除现有的 CUDA 包
sudo apt-get --purge remove "*cuda*"
sudo apt-get --purge remove "*nvidia*"
sudo apt-get autoremove
sudo apt-get autoclean
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107164527946_d7687348.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107164608060_4266c1c6.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107164632038_a0c1c948.png)
2. 删除之前的 CUDA 目录：
```bash
sudo rm -rf /usr/local/cuda*
sudo rm -rf /usr/lib/cuda*
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107164704013_9dc80dee.png)
3. 清理 apt 源：
```bash
sudo rm /etc/apt/sources.list.d/cuda*
sudo rm /etc/apt/preferences.d/cuda*
```


初次安装或者没有配置则不用管
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107164755524_dd4bfc48.png)
4. 重新安装 CUDA 12.4：
```bash
# 下载并设置 pin 文件
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-ubuntu2204.pin
sudo mv cuda-ubuntu2204.pin /etc/apt/preferences.d/cuda-repository-pin-600

# 可以选择最新版或者历史版本 https://developer.nvidia.com/cuda-downloads
```

```bash
# 下载并安装 CUDA 仓库包
wget https://developer.download.nvidia.com/compute/cuda/12.4.0/local_installers/cuda-repo-ubuntu2204-12-4-local_12.4.0-550.54.14-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu2204-12-4-local_12.4.0-550.54.14-1_amd64.deb
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107164908639_1ff21bfc.png)

```bash
# 下载并安装 CUDA 仓库包
sudo dpkg -i cuda-repo-ubuntu2204-12-4-local_12.4.0-550.54.14-1_amd64.deb

```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107164953731_510c8396.png)

```bash
# 复制密钥
sudo cp /var/cuda-repo-ubuntu2204-12-4-local/cuda-*-keyring.gpg /usr/share/keyrings/
# 更新软件包列表
sudo apt-get update

```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107165323161_47cd7968.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107165432426_34b519da.png)

```bash
# 安装 CUDA 12.4
sudo apt-get -y install cuda-12-4
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107165521017_cb89ce6c.png)
5. 设置环境变量：
```bash
# 编辑 ~/.bashrc 文件
sudo vim ~/.bashrc

# 添加以下行
export PATH=/usr/local/cuda-12.4/bin${PATH:+:${PATH}}
export LD_LIBRARY_PATH=/usr/local/cuda-12.4/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}

# 保存并应用更改
source ~/.bashrc
```


也可以按照以下方式，设置环境变量，将以下内容添加到 ~/.bashrc：
```bash
echo 'export PATH=/usr/local/cuda-12.4/bin${PATH:+:${PATH}}' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.4/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}' >> ~/.bashrc
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107170142402_ca105226.png)
8. 重启系统：
```bash
sudo reboot
```
9. 验证安装：
```bash
# 检查 CUDA 版本
nvcc --version

# 检查 NVIDIA 驱动和 CUDA 版本
nvidia-smi
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107173336731_5cdbb973.png)
## 1.3 安装Docker
1. 移除旧版本的 Docker（如果存在）：
```bash
sudo apt-get remove docker docker-engine docker.io containerd runc
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107173450604_747e05bb.png)

2. 更新包索引并安装必要的依赖：
```bash
sudo apt-get update
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107173526312_68de1c7d.png)

3. 添加 Docker 的官方 GPG 密钥：
```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

![image](/assets/img/posts/low-code-dify-coze-12/image-20250107173616138_aa22d554.png)

4. 设置 Docker 仓库：
```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107173654783_3171788e.png)

5. 更新包索引并安装 Docker：
```bash
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107173806303_9382030a.png)

6. 验证安装：
```bash
# 检查 Docker 版本
docker --version

```

![image](/assets/img/posts/low-code-dify-coze-12/image-20250107173933286_ccfd105c.png)
7. 创建或修改 Docker 配置文件，添加国内镜像源：
```bash
# 当前文件如果没有直接创建即可
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://docker-0.unsee.tech",
    "https://docker.hlmirror.com",
    "https://docker.imgdb.de",
    "https://docker.m.daocloud.io",
    "https://mirror.ccs.tencentyun.com",
    "https://hub-mirror.c.163.com"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m"
  },
  "max-concurrent-downloads": 10,
  "max-concurrent-uploads": 5
}
EOF
# log-driver: 这个配置项指定了 Docker 容器的日志驱动类型。这里设置为 json-file，表示日志将以 JSON 格式存储到本地磁盘。json-file 是 Docker 默认的日志驱动。
# log-opts: 这个配置项用于指定日志驱动的选项。这里设置了日志的最大大小为 100MB，意味着每个容器的日志文件大小会限制在 100MB 以内，超过 100MB 后会进行日志切割。
# max-concurrent-downloads: 控制 Docker 在拉取镜像时的最大并发下载数量，设置为 10 表示 Docker 可以同时并行下载最多 10 个镜像层。
# max-concurrent-uploads: 控制 Docker 上传镜像时的最大并发上传数量，设置为 5 表示 Docker 可以同时并行上传最多 5 个镜像层。
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107174220496_2d7c1b2a.png)

8. 重启 Docker 服务：
```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
```

9. 安装 Docker Compose：
```bash
# Docker Compose 现在已包含在 docker-compose-plugin 包中
docker compose version
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107174433511_1fdb8f85.png)
10. 验证安装后的配置：
```bash
# 检查 Docker 服务状态
sudo systemctl status docker
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107174501864_9fd29970.png)
11. 配置 Docker 用户组（这样你可以不用 sudo 运行 docker 命令）：
```bash
sudo usermod -aG docker $USER
```

12. 配置 Docker 开机自启：
```bash
sudo systemctl enable docker
```
提示：
1. 运行完步骤 11 后，需要注销并重新登录才能使用户组更改生效
2. 如果遇到权限问题，可以使用以下命令：
```bash
sudo chmod 666 /var/run/docker.sock
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107174616617_bb97a841.png)
```bash
# 检查 Docker 信息（包括镜像源配置）
docker info
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107174724661_b83518f4.png)
测试镜像拉取：
```bash
# 尝试拉取一个测试镜像
docker pull hello-world
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107174821523_85c0136a.png)
## 1.4 安装miniconda

1. 下载 Miniconda 安装脚本（使用清华镜像源）：
```bash
# 对于 Linux x86_64 系统
wget https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh

# 如果 wget 没有安装，先安装 wget
# sudo apt-get update && sudo apt-get install wget -y
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107175327146_7b28fa06.png)
2. 验证下载文件的完整性：
```bash
# SHA-256 是一种加密哈希算法，常用于验证文件的完整性或确保文件在传输过程中未被篡改
sha256sum ~/miniconda.sh
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107175415086_8fdf197c.png)
3. 运行安装脚本：
```bash
# -b：该选项表示 "batch mode"（批处理模式），不显示任何交互提示，自动安装。这意味着脚本在执行时不会要求用户输入任何内容（如同意许可证、选择安装路径等）。安装过程完全自动化，适用于需要快速安装且不想人工干预的场景。
# -p: 后面接的是你希望 Miniconda 被安装到的路径
bash ~/miniconda.sh -b -p $HOME/miniconda
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107175530035_083d2ba1.png)
4. 初始化 conda：
```bash
# 将 conda 添加到 PATH
echo 'export PATH="$HOME/miniconda/bin:$PATH"' >> ~/.bashrc

# 刷新当前 shell
source ~/.bashrc

# 初始化 conda
conda init bash

# 如果没有生效就重新init  再执行 source ~/.bashrc
```

![image](/assets/img/posts/low-code-dify-coze-12/image-20250107175709268_899601a9.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107175805140_471b208e.png)
5. 配置国内镜像源（清华源）：
```bash
# 创建 .condarc 文件
cat > ~/.condarc << EOF
channels:
  - defaults
show_channel_urls: true
default_channels:
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/r
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/msys2
custom_channels:
  conda-forge: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  msys2: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  bioconda: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  menpo: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  pytorch: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  pytorch-lts: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  simpleitk: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
EOF

# default_channels：这是一个列表，指定了默认的几个镜像源路径
# show_channel_urls: true 这一配置项表示，当 conda 进行包下载时，会显示包的下载源
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107175837219_4c1159e2.png)
6. 清除缓存并更新 conda：
```bash
# 清除缓存
conda clean -i

# 更新 conda
conda update -n base -c defaults conda
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107180028086_b305a79f.png)
7. 验证安装：
```bash
# 检查 conda 版本
conda --version

# 检查配置
conda config --show
```
# 2. 源码安装Dify
创建dify环境  conda create -n dify -y 

建议直接使用python 3.11   conda create -n dify python=3.11 -y  

因为了更好复现问题，所以采取了多台服务器并行进行安装，但系统版本环境完全一致(ip地址不一致)，遇到问题处理方式一致。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108141451080_1336ba6c.png)
自定义路径存放代码

在git上下载代码
git clone https://github.com/langgenius/dify.git
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107181508318_5d047a16.png)
需要先部署 PostgreSQL / Redis / Weaviate (如果本地没有，如果本地有需要自行配置对应的权限及用户)

```bash
cd docker # dify文件夹下Docker文件
cp middleware.env.example middleware.env

```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107181633439_21ad9e0b.png)
```bash

sudo usermod -aG docker $USER
# usermod：用于修改用户的属性。
# -a：追加用户到一个组，而不是覆盖现有的组。
# -G docker：指定要添加的目标组是 docker。
# $USER：当前用户的环境变量，表示你正在登录的用户。

# 将当前用户添加到 Docker 组 (docker) 中。
# Docker 守护进程默认需要 root 权限，或者属于 docker 组的用户权限才能操作。通过这个命令，当前用户就可以直接运行 Docker 命令而不需要每次加 sudo。

newgrp docker
# newgrp：用于切换到一个新用户组。
# docker：指定切换到的组是 docker。
# 让当前用户会话立即加载新组的权限，而无需注销并重新登录。

docker compose -f docker-compose.middleware.yaml up -d
# 命令的作用是基于 docker-compose.middleware.yaml 文件定义的服务，启动所有相关的容器，并让它们在后台运行。
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107182212874_d5decc79.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107182250059_97f3f4b2.png)
进入dify/api文件夹

```bash
# 复制环境变量配置文件
cp .env.example .env

```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107183137857_7b756a94.png)
```bash
# 生成随机密钥，并替换 .env 中 SECRET_KEY 的值
awk -v key="$(openssl rand -base64 42)" '/^SECRET_KEY=/ {sub(/=.*/, "=" key)} 1' .env > temp_env && mv temp_env .env
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107183222402_88979b28.png)
```bash
# Dify API 服务使用 Poetry 来管理依赖。你可以执行根据poetry版本 poetry shell 来激活环境。
poetry env use 3.11
# 依据提示进行安装(这是个坑 安装版本过低)
sodo apt install python3-poetry  
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107183933475_744a36f9.png)
建议全选，使用空格选择，然后TAB键进行切换确认或者取消，enter选择
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107200155908_6f69e97c.png)
```bash
# Dify API 服务使用 Poetry 来管理依赖。你可以执行根据poetry版本 poetry shell 来激活环境。
poetry env use 3.11
poetry install
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107200923743_24f61199.png)
将原有默认版本进行卸载
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107200956875_9997b2f5.png)
自定义安装新版本

pip install poetry==2.0.0
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107201621773_10a6f191.png)
查看安装版本 poetry --version
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107201633179_4d0f8330.png)
注意优先切换环境，然后执行

poetry env use 3.11

官方建议使用python3.11 为了方便管理 在最一开始创建了dify 环境直接规定为3.11
### Conda 与 Poetry 对比

| 特性                  | Poetry                                      | Conda                                               |
|-----------------------|---------------------------------------------|-----------------------------------------------------|
| **主要功能**          | Python 项目的依赖管理和打包发布             | 跨语言的包管理和环境管理                             |
| **适用语言**          | 主要是 Python                              | Python 和其他语言（如 R、C、Java 等）               |
| **依赖管理**          | 通过 `pyproject.toml` 和 `poetry.lock` 锁定依赖 | 通过 `.yaml` 文件管理，支持多语言依赖               |
| **虚拟环境管理**      | 自动创建和管理 Python 虚拟环境              | 创建和管理多个语言的虚拟环境                         |
| **易用性**            | 简单、现代，适用于 Python 项目              | 强大、灵活，适合跨语言开发，尤其在数据科学领域       |
| **性能和包管理**      | 专注于 Python 项目，快速且高效              | 优化科学计算库，预编译包，适合数据科学应用           |

#### 额外说明

- **Conda**：环境中包含 Python 解释器和相关依赖。您通过 `conda create -n dify python=3.11` 创建的环境已经包含 Python 3.11，但您需要手动安装和管理项目依赖。适用于需要跨语言依赖的场景。
  
- **Poetry**：专注于 Python 项目的依赖管理和打包发布。Poetry 创建的环境默认基于系统的 Python 解释器（或者通过 pyenv 管理的版本），使用 `pyproject.toml` 和 `poetry.lock` 文件来精确管理 Python 依赖。适合开发、管理和发布 Python 项目。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107201740482_9ab3be94.png)
再次执行依赖安装

poetry install 

报异常，需要更新 poetry lock
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107201848616_dea4cc87.png)
执行完成后 再次执行 poetry install 
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107202204052_2641a393.png)
准备激活环境，使用poetry shell ，因为当前是2.0.0版本，环境不支持当前命令。

切换 poetry env shell 查看命令使用
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107203025912_f1302f63.png)
使用当前命令进行环境激活   
poetry env use $(which python)

poetry run python -V

将数据库结构迁移至最新版本  
flask db upgrade
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107202945596_60fa7958.png)
### 启动服务端
启动API服务  

flask run --host 0.0.0.0 --port=5001 --debug
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107203610604_5352b40d.png)
新启动一个链接窗口  


```bash
celery -A app.celery worker -P gevent -c 1 -Q dataset,generation,mail,ops_trace --loglevel INFO
    # 这个命令启动了一个 Celery worker 进程，并配置了以下内容：
    # -A app.celery：从 app.py 或 app/celery.py 中加载 Celery 实例。
    # worker：启动 worker 来处理任务。
    # -P gevent：使用 gevent 作为并发池来提高并发处理能力（适合 I/O 密集型任务）。
    # -c 1：每个 worker 同时处理一个任务（并发数为 1）。
    # -Q dataset,generation,mail,ops_trace：监听 dataset、generation、mail 和 ops_trace 四个任务队列。
    # --loglevel INFO：设置日志级别为 INFO，显示基本的运行信息。
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107203807216_d5e76bfc.png)
### 前端页面部署
切换conda环境

进入到web文件夹下 
Web 前端服务启动需要用到 Node.js v18.x (LTS) 、NPM 版本 8.x.x 或 Yarn。本次只用NPM作为展示。

1. 添加 NodeSource 仓库（使用国内镜像源）：
```bash
# 删除旧版本（如果存在）
sudo apt-get remove nodejs npm

# 清理 apt
sudo apt-get clean
sudo rm -rf /var/lib/apt/lists/*
sudo apt-get update
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107204112568_93533a92.png)
```bash

# 安装必要的包
sudo apt-get install -y ca-certificates curl gnupg

```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107204203698_60c92a30.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107204224462_48a72ac5.png)
```bash
# 添加 NodeSource 仓库的 GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg

# 添加 NodeSource 仓库
echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_18.x nodistro main" | sudo tee /etc/apt/sources.list.d/nodesource.list
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107204410207_d73f62f9.png)
2. 更新包列表并安装 Node.js：
```bash
sudo apt-get update
sudo apt-get install -y nodejs
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107204521938_6521f637.png)
3. 验证安装：
```bash
# 检查 Node.js 版本
node --version  

# 检查 npm 版本
npm --version 
```


![image](/assets/img/posts/low-code-dify-coze-12/image-20250107204613373_f1ec0f5f.png)
4. 配置 npm 使用淘宝镜像源（加快安装速度）：
```bash
# 配置 npm 使用淘宝镜像
npm config set registry https://registry.npmmirror.com

# 验证配置
npm config get registry
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107204821311_cacdf6dc.png)
安装依赖包

npm install
时间较长
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107205800352_455eb497.png)
在当前目录下创建文件 .env.local，并复制.env.example中的内容。根据需求修改这些环境变量的值
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107210306251_b95169c4.png)
```bash
# For production release, change this to PRODUCTION
NEXT_PUBLIC_DEPLOY_ENV=DEVELOPMENT
# The deployment edition, SELF_HOSTED
NEXT_PUBLIC_EDITION=SELF_HOSTED
# The base URL of console application, refers to the Console base URL of WEB service if console domain is
# different from api or web app domain.
# example: http://cloud.dify.ai/console/api
NEXT_PUBLIC_API_PREFIX=http://localhost:5001/console/api
# The URL for Web APP, refers to the Web App base URL of WEB service if web app domain is different from
# console or api domain.
# example: http://udify.app/api
NEXT_PUBLIC_PUBLIC_API_PREFIX=http://localhost:5001/api

# SENTRY
NEXT_PUBLIC_SENTRY_DSN=
NEXT_PUBLIC_SENTRY_ORG=
NEXT_PUBLIC_SENTRY_PROJECT=
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107210326650_2e8da29e.png)
构建代码

npm run build
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107210351427_9f5e47c9.png)
构建完成
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107210729656_74f7ea57.png)
启动服务   npm run start
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107210814929_34817fc0.png)
-----
## 补充说明
因为平台原因如果遇到使用 npm install 长期无法加载也不报错，可以使用pnpm install (后续dify可能会全部使用pnpm进行管理1.0版本使用npm会抛异常明确要求安装pnpm)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250313151645389_e02501e5.png)
创建一个用户级别的npm全局安装目录    
配置npm使用这个新目录而不是系统目录    
将这个目录添加到PATH中    
以用户权限（非root）安装了pnpm    
```json
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
export PATH=~/.npm-global/bin:$PATH
或者 echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.profile
source ~/.profile  # or source ~/.bashrc if you added it there
npm install -g pnpm
```
可以再base环境执行也可以在 dify环境执行
![image](/assets/img/posts/low-code-dify-coze-12/image-20250313151845346_c1c1eefe.png)
sudo npm install -g pnpm
![image](/assets/img/posts/low-code-dify-coze-12/image-20250313151744791_40a4c770.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250313152241921_3f54feaa.png)
##  补充说明结束-
-----
到现在为止一共启动了三个本地连接界面。用来连接服务器启动程序界面。

准备本地连接记好当前服务器对外ip，并记录密码
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107210941496_4dfa0fb1.png)
更改防火墙，配置过滤端口
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107211100310_78b21c1f.png)
编辑防火墙规则
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107211201455_4e4a48f8.png)
点击添加规则
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107211233256_fc5c8b36.png)
当前以40996为例，进行保存
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107211318789_a48c57e4.png)
确认规则后完成。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107211336184_444dfe89.png)
添加完成
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107211355867_f8011d9f.png)
建议端口必选：9997 
    5432  
    5001  
    3000   
    6379 
打开本地电脑命令窗口(服务器上不关闭程序)
```bash
ssh -CNg -L 3000:127.0.0.1:3000 -L  5001:127.0.0.1:5001 ubuntu@117.50.188.133 -p 22

    # 使用 SSH 连接到远程服务器 117.50.188.133（用户名 ubuntu，端口 22）。
    # 建立 SSH 连接时启用了压缩和仅建立连接，不执行远程命令。
    # 同时，开启了 端口转发：
    # 将本地的 3000 端口转发到远程服务器 127.0.0.1:3000。
    # 将本地的 5001 端口转发到远程服务器 127.0.0.1:5001。
    # 这样，你可以在本地访问 localhost:3000 和 localhost:5001，实际上是在访问远程服务器上的相应端口
```
回车后输入密码(第一次会需要你输入yes)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107211948290_48ce7248.png)
打开本地电脑浏览器
http://localhost:3000/install
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107212019138_0ec1edf0.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107212210435_59852e7c.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107212302592_11ad6ac8.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107212321772_62861b03.png)
# 3. xinference安装
conda create -n xinference python=3.11 创建xinference环境
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107213122623_23fd0e20.png)
切换环境 conda activate xinference
pip install "xinference[transformers,vllm]"

只选择transformers引擎与vllm引擎。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107213242218_d5feb6a3.png)
安装完成
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107214036752_85c6e79a.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107214350945_5140d71a.png)
Xinference 会使用 `<HOME>/.xinference` 作为主目录来存储一些必要的信息，比如日志文件和模型文件，其中 `<HOME>` 就是当前用户的主目录
XINFERENCE_MODEL_SRC="modelscope" XINFERENCE_HOME=/home/ubuntu/muyan/xinference xinference-local --host 0.0.0.0 --port 9997
使用XINFERENCE_MODEL_SRC="modelscope" 配置使用魔撘社区

XINFERENCE_HOME=/home/ubuntu/muyan/xinference 内容存放到指定目录
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107214448368_c7b41b4c.png)
启动完成后，依然使用本地连接

ssh -CNg -L 9997:127.0.0.1:9997  ubuntu@117.50.188.133 -p 22    依然使用密码
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107214628485_ba7e7bdc.png)
打开本地连接 

http://localhost:9997

![image](/assets/img/posts/low-code-dify-coze-12/image-20250107214713317_48790502.png)
自行选择模型做为测试
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107214757086_bceadeeb.png)
发布模型查看后台，看一下载路径
当前指定文件存储路径/home/ubuntu/muyan/xinference
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107214849867_af41b837.png)
具体在服务器中查看
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107215043911_f58ba6e8.png)
查看运行模型，进行发布当前模型对话界面
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107215305117_639d1e1f.png)
尝试对话，校验模型是否正常
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107215241154_ccb03176.png)
### Llama.cpp引擎
Xinference 通过 llama-cpp-python 支持 gguf 格式的模型，需要手动安装
创建新环境  conda cerete -n xinference2 python=3.11 -y
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108191946545_2baf2b09.png)
切换新环境 conda activate xinference2

pip install llama-cpp-python==0.2.79 (测试目前兼容的最高版本)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108192225269_074b583a.png)
pip install xinference
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108192319130_e31981e5.png)
启动测试：XINFERENCE_MODEL_SRC="modelscope" XINFERENCE_HOME=/home/ubuntu/muyan/xinference xinference-local --host 0.0.0.0 --port 9997
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108193746243_8478310f.png)
界面访问
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108192918903_be6bc67c.png)
## 连接测试
回到dify界面，创建对话机器人。(上节课已经说过如何创建，本次不再赘述)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107215600387_8e6a64ce.png)
增加大模型配置  直接使用localhost:9997
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107215812047_87a9d43e.png)
查看已经配置的
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107215826575_ead109e5.png)
回到对话界面切换模型
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107215920021_5bb56936.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107215946125_ca1777c3.png)
直接对话测试，测试流程。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250107220102488_ffd44a07.png)
# 4. 构建知识库
## 扩充服务器算力
给当前系统制作镜像
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108172636782_2c98e79c.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108173730166_5671aa64.png)
重新部署算力，选择自定义镜像内容。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108191151561_40bfc710.png)
直接发布即可
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108191803918_54407da8.png)
查看GPU
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108191738403_4f140dd5.png)
### 启动服务
xinference： XINFERENCE_MODEL_SRC="modelscope" XINFERENCE_HOME=/home/ubuntu/muyan/xinference xinference-local --host 0.0.0.0 --port 9997

(dify):/dify/web$ npm run start

(dify):/dify/api$ celery -A app.celery worker -P gevent -c 1 -Q dataset,generation,mail,ops_trace --loglevel INFO

(dify):/dify/api$ flask run --host 0.0.0.0 --port=5001 --debug

线上使用建议使用nohup
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108194801539_95c4e0eb.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108194843008_477704c4.png)
本地进行连接
ssh -CNg -L 9997:127.0.0.1:9997  ubuntu@117.50.81.101 -p 22

ssh -CNg -L 3000:127.0.0.1:3000 -L  5001:127.0.0.1:5001 ubuntu@117.50.81.101 -p 22
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108194939728_62e0856a.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108195018414_00062f7a.png)
登录本地界面：http://localhost:3000  查看当前创建的对话机器人，切换到知识库界面。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108195111633_c791368e.png)
点击创建知识库
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108195943205_8ae700e8.png)
本次使用已有文本进行测试
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108200044931_76a1460c.png)
选择文件进行上传
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108200923256_123e5738.png)
点击下一步后会进入到文本分段与清洗阶段
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108201204488_e5ccfb2c.png)
根据自定义选择长度，以及预览切割是否合理，并进行调整。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108201300526_09ce4ed1.png)
点击切换父子分段(或者切换默认分段状态)，会发现需要设置Embedding模型和Rerank模型。准备进行二次配置。
```bash
在 RAG 中，Embedding 模型 主要用于将输入查询（问题）和知识库中的文档转换为向量表示。通过这种方式，系统可以计算它们的相似性，从而进行检索。

# 检索流程：  
#     输入文本（例如问题或查询）通过 Embedding 模型 被转换为一个向量表示（通常是高维的数字向量）。  
#     知识库中的每个文档或片段也会通过 Embedding 模型 转换为向量表示。这些文档可以是预先存储的文本，通常来自于大型数据库或其他资源。  
#     然后，查询的向量与知识库中所有文档的向量进行 相似度计算，通常使用 余弦相似度 或 点积 等方法来评估查询与文档之间的相似度。  
#     根据相似度得分，选择出最相关的文档或片段作为 候选文档。  


Rerank 模型 的主要作用是在从知识库中检索到一批候选文档后，进一步对这些文档进行重新排序。其目的是确保最终选出的文档是最相关、最有用的。

# 检索流程：
    # 在 Embedding 模型 通过计算向量相似度筛选出初步的候选文档后，Rerank 模型 会对这些候选文档进行更加精细的排序。
    # Rerank 模型 通常会根据额外的信息或复杂的语义理解来重新评估候选文档的质量。这些模型通常采用深度学习方法（如 BERT 或其他预训练模型）进行排序，它们能够考虑更多的上下文信息和细粒度的语义关系。
    # 在一些场景中，Rerank 模型可能会结合多个特征，例如文档的内容、查询的意图、文档的上下文等，从而选择出最符合需求的文档。
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108201401420_29be0463.png)
回到xinference Launch Model 界面，直接选择对应的模型。当前处理知识库为中文，优先进行推荐。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108201457823_f62b8559.png)
EMBEDDING models 同样进行选择后发布
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108201557084_2767e4a5.png)
后台会报错，缺少包，直接进行安装即可
pip install sentence-transformers
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108201859603_a7d7b0c1.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108201939063_232ea45b.png)
安装完成后直接进行二次部署，查看运行情况即可
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108202038694_1a3a11b7.png)
安装reranker模型
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108202115055_091e5bc4.png)
点击发布后后端会进行下载
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108202611140_86e360ee.png)
同样会因为少包报错
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108203245590_ff268b4a.png)
这里有个小坑，不建议直接安装最新版本FlagEmbedding包
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108203310561_3e89c1fe.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108203518493_026b7b57.png)
pip index versions FlagEmbedding  先查看历史版本

pip install FlagEmbedding==1.2.11  跳过大版本更新，选择相对成熟版本
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108204142990_2baa4300.png)
安装完成后进行二次发布，现在llm、rerank、EMBEDDING 模型全部启动完成。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108212434479_3231c6a3.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108212558816_140648fb.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108212528217_934e6889.png)
注意选择大模型时候建议选择多GUP部署，在N-GPU位置直接选择最大数值，如果算力足够或者模型够小选择单卡运行也OK。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108221903353_526de467.png)
返回Dify，直接点击右上角头像设置，进行模型模型配置
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108212808317_08aed321.png)
选择已经配置好的xinference 模型供应商进行模型添加
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108212839264_96e6cb05.png)
选择模型类型，注册模型id、名称、ip地址:端口
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108212924737_a4503ea4.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108213039681_f946073c.png)
查看模型供应商列表，查看已经注册好的额模型。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108213100619_0498839f.png)
返回知识库创建界面刷新或者重新建立。已经直接引用了EMBEDDING 模型与rerank模型
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108213152203_f597c5ac.png)
### 1. 向量检索

#### 定义
向量检索通过将查询和文档转化为向量（嵌入），计算查询与文档之间的相似度来进行检索。

#### 优点
- **强大的语义理解能力**：能够理解查询和文档之间的语义关系，即便是用不同的表达方式，也能找到相关的文档。
- **处理同义词和变体**：识别不同表达方式的同义词和语言变体。
- **容错能力**：对拼写错误、词形变化等容错性较好。
- **处理复杂查询**：对于包含复杂语义、上下文和长尾问题的查询有明显优势。

#### 缺点
- **计算资源消耗大**：在文档库较大时，检索过程会较慢。
- **实现复杂**：需要搭建和优化向量索引。
- **索引空间占用大**：向量索引需要占用大量存储空间。

#### 适用场景
- 复杂的问答系统或对话生成
- 需要跨语言支持的场景



### 2. 全文检索

#### 定义
全文检索是基于倒排索引技术，利用关键词匹配对查询进行检索。适用于检索包含大量文本的数据库，能够快速找到包含特定词汇的文档。

#### 优点
- **检索速度快**：特别适合大规模文档库的快速查询。
- **实现简单**：有成熟的工具可以使用，容易部署和维护。
- **资源消耗小**：不需要复杂的计算或高性能硬件。

#### 缺点
- **缺乏语义理解**：无法理解查询的深层语义。
- **对拼写和语法错误敏感**：可能导致无法返回准确结果。
- **无法处理长尾查询**：如果查询非常具体且不常见，可能无法找到相关文档。

#### 适用场景
- 电商搜索
- 新闻网站或博客

### 3. 混合检索

#### 定义
混合检索结合了向量检索和全文检索，通常采用先使用关键词检索筛选出一定数量的相关文档，再通过向量检索对候选文档进行精确排序。

#### 优点
- **平衡效率与准确性**：保证高效检索的同时提高检索结果的准确性。
- **速度较快**：减少了需要进行向量检索的文档数量，从而提高整体检索速度。
- **准确度高**：提高了检索结果的相关性和精确度。
- **适应多种查询类型**：提供快速和精细的结果。

#### 缺点
- **实现复杂**：增加了系统的复杂度。
- **性能瓶颈**：关键词检索的结果质量影响后续的向量检索效果。

#### 适用场景
- 需要快速检索和高精度结果的场景，如电商搜索、文档管理等

- **大量文档和简单查询**：选择全文检索以获得快速响应。
- **语义理解和复杂查询**：选择向量检索，特别是在多语言支持或处理长尾查询时。
- **平衡效率和准确性**：考虑混合检索，通过先使用关键词检索来提高速度，再利用向量检索提升准确性。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108213254956_5b6c24ad.png)
点击确认后，后端开始输出力数据
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108213331598_8b3f68d8.png)
可以在知识库中查看，当前为自动知识库起名。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108213352043_a0b61dbf.png)
可以针对文档进行操作，比如重命名等
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108213435410_c379f34a.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108213457282_fbf0e6e8.png)
可以自定义名称
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108213516092_df38648f.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108213602912_2a2a7cf0.png)
知识库名称默认为上传文本名称，一样可以进行二次更改和补充描述
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108213644465_a296286e.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108213707424_d90099fd.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108213804895_cf6dc3e5.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108213827325_84dc6f86.png)
### 第二种创建知识库方法
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108213847716_6b5604b9.png)
先对知识库进行命名
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108213937125_d603c5eb.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108214009373_caabe0a7.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108214056300_3f468a6d.png)
上次已经配置好了，本次会默认选择
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108214210337_d0e19bcc.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108214309023_95596670.png)
# 5. 构建简单RAG
RAG 是一种结合 **信息检索（Information Retrieval, IR）** 和 **生成式模型（如大语言模型，LLM）** 的方法，用于改进文本生成任务的质量和准确性。它的核心思想是在生成过程中利用外部知识库进行 检索，并将检索到的信息融合进生成过程，从而增强模型的生成能力。

RAG的工作流程：  
检索阶段：首先，通过查询输入问题或文本，在一个大型的知识库（例如文档库或数据库）中进行检索，找到相关的信息片段。  
生成阶段：然后，将检索到的信息（比如相关文档或段落）与原始输入一同作为条件输入到生成模型中，生成更为精准的回答或文本。  

RAG（Retrieval-Augmented Generation）并不一定需要同时使用 embedding、rerank 和 LLM（大语言模型）。虽然这三者是 RAG 的典型组成部分，但具体配置取决于实现的需求和应用场景。下面是几种不同的实现方式：

### 1. 只使用 Embedding 和 LLM

**描述**：一些简化版的 RAG 可能只依赖于 embedding 模型进行检索，而不使用专门的 rerank 模型。这种方式通过简单的向量相似度计算来选取相关文档，然后将这些文档与查询一同输入到 LLM 中生成最终的文本。

**适用场景**：
- 当对系统复杂性有较高要求时，可以减少模型数量以简化架构。
- 对于不太复杂的查询或较小的知识库，可能已经足够提供满意的结果。

### 2. 使用 Embedding + Rerank + LLM

**描述**：对于精度要求更高的应用，可能会采用 embedding 模型来进行初步检索，再使用 rerank 模型对检索结果进行精细化排序，最后将排好序的相关文档输入到 LLM 中进行生成。这种方法能够更精确地选择相关文档，从而提高生成结果的质量。

**适用场景**：
- 需要高准确性和高质量生成结果的应用。
- 大型知识库中，为了确保检索到最相关的文档，需要额外的排序步骤。

### 3. 无需 Rerank

**描述**：在某些情况下，直接从检索到的相关文档中生成结果，而不进行额外的排序，也能达到较好的效果。特别是在知识库规模不大或者检索准确性较高的情况下，省略 rerank 步骤可以简化流程并加快响应速度。

**适用场景**：
- 知识库相对较小，检索准确性较高。
- 对实时性能有严格要求的应用，减少处理时间。

![image](/assets/img/posts/low-code-dify-coze-12/image-20250108214502166_81d9cf63.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108222351180_180d43a0.png)
在上下文部分进行知识库引用
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108222415714_39df3e6a.png)
选择知识库
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108222438230_941aeab0.png)
增加系统提示词后开始测试。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108222624299_b4b39a4b.png)
查看对话回答引用的文本文件内容。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108222701937_bb185bfb.png)
点击更新后进行发布。到界面开始测试。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108222757314_052b5698.png)
校验回答引入内容。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108222813604_c216b962.png)
查看日志监控。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108223056341_501c338a.png)
查看对话监测。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250108223113850_0290f1ca.png)
# 总结
![image](/assets/img/posts/low-code-dify-coze-12/image-20250109172703115_6a5bf7bf.png)