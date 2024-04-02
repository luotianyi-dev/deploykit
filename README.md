# DeployKit

DeployKit 是 Tianyi Network 开发的静态 Web 部署工具，用于在自建服务器上实现类似 Cloudflare Pages、GitHub Pages 等服务的静态网站部署功能。

DeployKit 包括一下特性：
 - 被设计为与其他 HTTP 服务器配合使用
 - 服务端基于 Docker 部署
 - 使用 Zstandard 压缩算法压缩传输
 - 基于软链接的无缝版本切换
 - 支持将资源文件上传到 S3 兼容的对象存储

[![DeployKit](https://github.com/luotianyi-dev/deploykit/actions/workflows/docker.yml/badge.svg)](https://github.com/luotianyi-dev/deploykit/actions/workflows/docker.yml)
[![DeployKit Docker Container](https://img.shields.io/badge/ghcr.io-luotianyi--dev%2Fdeploykit-blue?style=flat-square)](https://github.com/orgs/luotianyi-dev/packages/container/package/deploykit)
[![License: MPL 2.0](https://img.shields.io/badge/LICENSE-MPL--2.0-66ccff?style=flat-square&labelColor=)](https://github.com/orgs/luotianyi-dev/packages/container/package/deploykit)

## 安装
**DeployKit 依赖以下软件：**
 - Python: **推荐 3.12**，可使用 `3.9` 以上版本
 - PDM: 用于管理 Python 依赖
 - Docker（可选）

**安装 PDM**

[PDM](https://github.com/pdm-project/pdm/blob/main/README_zh.md) 是一款优秀的 Python 项目依赖管理工具，DeployKit 使用 PDM 管理 Python 依赖。

通过以下命令安装 PDM:
```bash
# 使用 pipx 安装（推荐）
pipx install pdm

# 使用脚本安装
curl -sSL https://pdm-project.org/install-pdm.py | python3 -
```

参见 [PDM 文档](https://github.com/pdm-project/pdm/blob/main/README_zh.md#%E5%AE%89%E8%A3%85) 获取更多安装方法。

**获取与安装 DeployKit**

```bash
git clone https://github.com/luotianyi-dev/deploykit.git
cd deploykit && pdm install
```

## 使用指南
DeployKit 使用命令 `deployctl` 进行操作。

在执行 `pdm install` 后，PDM 将 DeployKit 安装到虚拟环境中，可以通过以下命令执行 `deployctl`：
```bash
# 不进入虚拟环境直接运行
pdm run deployctl

# 进入虚拟环境后运行
$(pdm venv activate)
deployctl

# 退出虚拟环境
deactivate
```

您也可以使用 Docker 运行 DeployKit 客户端：
```bash
docker run --rm -it \
    -e API_KEY=your-api-key \
    -e PROJECT=your-project-name \
    -v /home/user/project:/project \
    -w /project \
    ghcr.io/luotianyi-dev/deploykit deployctl
```

### 配置客户端环境变量
DeployKit 需要特定的环境变量来运行。您需要设置以下环境变量：
Environment Variable  | Default Value                                | Description
--------------------- | -------------------------------------------- | ---------------------------------------
`API_URL`             | `https://deployapi.webservice.luotianyi.dev` | DeployKit 服务器的地址
`API_KEY`             | None                                         | **（必需）** DeployKit API 密钥，与服务器上设置的一致
`PROJECT`             | None                                         | **（必需）** 项目名称，符合正则 `^[A-Za-z0-9_][A-Za-z0-9_-]{0,61}[A-Za-z0-9_]$`
`S3_ENDPOINT`         | None                                         | （仅使用 S3 时需要）S3 服务器地址
`S3_ACCESS_KEY`       | None                                         | （仅使用 S3 时需要）S3 Access Key ID
`S3_SECRET_KEY`       | None                                         | （仅使用 S3 时需要）S3 Secret Access Key
`TIMEZONE`            | `UTC`                                        | 符合 [IANA 时区数据库](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) 格式的时区名称

### 例子：将本地目录部署到服务器
使用下面的命令将本地目录 `dist` 部署到服务器 `public` 目录：
```bash
export API_KEY=45d9a857-5a44-49e1-9148-e0dd27168dbe
export PROJECT=website-static
deployctl deploy upload -f dist public
```

该命令仅仅进行部署，并返回该部署的 Deployment ID，但不会将服务器上的 `current` 指向新部署的版本。您可以使用以下命令将 `current` 指向新部署的版本（将 `<deployment-id>` 替换为上一条命令返回的 `<deployment-id>`）：
```bash
deployctl deploy switch <deployment-id>
```

此外，您也可以使用以下命令一次性部署并切换版本：
```bash
deployctl deploy upload -f dist public --switch
```

若您有额外的文件需要上传，您也可以传如多个 `-f` 参数：
```bash
deployctl deploy upload -f dist public -f common-robots.txt public/robots.txt --switch
```

若您使用 Git 管理您的部署，您也可以将该部署关联到一个 Git Commit SHA-1 值：
```bash
deployctl deploy upload -f dist public --switch -c $(git rev-parse HEAD)
```

部署后，您可以使用以下命令查看部署历史：
```bash
# 查看部署
deployctl deploy list

# 查看 Commit 历史
deployctl commit list
```

您可以使用 `deployctl --help` 查看更多部署命令的帮助。

### 例子：部署资源文件到 S3 兼容服务
使用下面的命令将本地目录 `dist` 部署到 S3 兼容服务 `my-bucket`：
```bash
export PROJECT=website-static
export S3_ENDPOINT=https://s3.us-west-004.backblazeb2.com
export S3_ACCESS_KEY="<your_key_id>"
export S3_SECRET_KEY="<your_application_key>"

deployctl s3 \
    --bucket luotianyi-dev-1251131545 \
    --prefix web/website-static/ \
    -f assets -f images
```

**注意：对于阿里云、腾讯云，Endpoint 的「虚拟主机模式」不受支持，您需要使用「路径模式」。**

## 服务器部署指南
在安装完毕 DeployKit 后，您可以使用以下命令启动 DeployKit 服务端：
```bash
pdm run server
```
DeployKit 服务端将在 `8000/tcp` 端口上侦听。DeployKit 服务端使用 [uvicorn](https://www.uvicorn.org/) 作为 ASGI 服务器，相关可配置参数可以通过 `pdm run uvicorn --help` 命令查看。

您可以设置环境变量 `WEB_CONCURRENCY` 来调整服务器的工作进程数量。

您需要 [配置环境变量](#配置服务端环境变量) 让 DeployKit 服务端正常运行，并配置一个 HTTP 服务器来托管您的静态网站（[Nginx 的例子](#例子使用-nginx-托管部署的网站)）。

### 配置服务端环境变量
DeployKit 服务端需要以下环境变量来运行：
Environment Variable  | Default Value                                | Description
--------------------- | -------------------------------------------- | ---------------------------------------
`API_KEY`             | None                                         | **（必需）** DeployKit API 密钥，用于客户端认证
`APP_PATH`            | None                                         | **（必需）** DeployKit 应用主目录
`MAX_DEPLOYMENTS`     | `500`                                        | DeployKit API 返回的最大部署历史数量
`WEB_CONCURRENCY`     | `4`                                          | ASGI 服务器工作进程数量

### 通过 Docker 部署
通过 Docker 部署 DeployKit 服务端是更为推荐的方式。运行以下命令以启动 DeployKit 服务端：
```bash
docker run -d --name deploykit-server \
    -p 127.0.0.1:8000:8000
    -e API_KEY=your-api-key \
    -e APP_PATH=/srv/web/static \
    -v /srv/web/static:/srv/web/static \
    ghcr.io/luotianyi-dev/deploykit
```

您需要将环境变量 `APP_PATH` 对应的目录挂载到 Docker 容器中。请参考上文的 [配置服务端环境变量](#配置服务端环境变量) 一节。

DeployKit 服务端将在 `8000/tcp` 端口上侦听。

### 使用 Docker Compose 部署
以下为 Docker Compose 配置文件示例：
```yaml
version: '3.8'

networks:
  deploykit:
    name: deploykit
    driver_opts:
      com.docker.network.bridge.name: cni-br0
    ipam:
      config:
        - subnet: 192.168.18.0/24

services:
  deploykit:
    image: ghcr.io/luotianyi-dev/deploykit:latest
    container_name: deploykit-server
    restart: always
    networks:
      deploykit:
        ipv4_address: 192.168.18.2
    environment:
      - API_KEY=your-api-key
      - APP_PATH=/srv/web/static
      - WEB_CONCURRENCY=4
    ports:
      - 127.0.0.1:8000:8000
    volumes:
      - /srv/web/static:/srv/web/static
    healthcheck:
      test: ["CMD", "curl", "-sfvo", "/dev/null", "localhost:8000"]
      retries: 3
      timeout: 30s
      interval: 30s
      start_period: 15s
    deploy:
      resources:
        limits:
          memory: 1024M
```

### 例子：使用 Nginx 托管部署的网站
假设您的 `APP_PATH` 在宿主机和容器内的路径均为 `/srv/web/static`，您可以使用以下 Nginx 配置文件来托管部署的网站：
```nginx
server {
    listen 80      default_server;
    listen [::]:80 default_server;
    server_name    _;

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443      ssl http2;
    listen [::]:443 ssl http2;
    server_name     example.com;
    root            /srv/web/static/website-static/current/public;
    index           index.html;

    location / {
        try_files $uri $uri/ /404.html /index.html;
    }
}
```

## 关于 Docker 镜像的更多信息
DeployKit 镜像以 [Python](https://hub.docker.com/_/python) 为基础镜像，使用多阶段构建。

镜像基于 Debian 上的 Python 3.11 版本 ([`python:3.11-slim`](https://hub.docker.com/_/python))。

DeployKit 支持 Open Container 标准元数据。

**镜像标签**
 - `latest`: 最新版本
 - `1.0.0`

## 开发与构建
安装完毕 DeployKit 后，您可以使用以下命令进行调试，该命令已经预置了调试所需的环境变量和配置：
```bash
# 调试客户端
pdm run cli

# 调试服务端
pdm run dev
```

### 使用 PDM 构建
```bash
pdm run build
```

### 使用 Docker 构建
```bash
docker build . -t ghcr.io/luotianyi-dev/powerdns:$(python -c "from src.deploykit_server import __version__; print(__version__, end='')")
```

## 许可
DeployKit 使用 MPL 2.0 许可。查看 [LICENSE](https://github.com/luotianyi-dev/deploykit/blob/main/LICENSE) 文件获取更多信息。
