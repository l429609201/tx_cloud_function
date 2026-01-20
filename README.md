# 腾讯云函数通用服务

> 类似 Vercel 万能反代，基于腾讯云 Serverless 架构的 HTTP 代理服务

## 📖 项目简介

这是一个部署在腾讯云函数（SCF）上的通用 HTTP 代理服务，可以通过 URL 路径动态指定目标地址进行请求转发。

**核心特性：**
- ✅ 支持 HTTP/HTTPS 协议转发
- ✅ 自动处理请求头和查询参数
- ✅ 支持多种 HTTP 方法（GET、POST、PUT、DELETE、HEAD 等）
- ✅ 自动添加 CORS 跨域支持
- ✅ 内置请求日志记录（最近 50 条）
- ✅ 显示云函数出口 IP 和地域信息
- ✅ 无需 API 网关，直接使用函数 URL

## 🚀 使用方式

### 基本格式

```
https://你的函数URL地址/{协议}/{目标域名}/{路径}?{查询参数}
```

### 使用示例

```bash
# 访问 HTTPS 接口
https://你的函数URL/https/api.imdbapi.dev/search/titles?query=test

# 访问 HTTP 接口
https://你的函数URL/http/example.com/api/data

# GitHub API
https://你的函数URL/https/api.github.com/users/octocat

# 查看代理 IP
https://你的函数URL/https/httpbin.org/ip
```

### 查看服务状态

访问根路径可查看服务信息：

```bash
https://你的函数URL/
```

返回内容包括：
- 服务状态
- 出口 IP 地址
- 云函数地域信息
- 最近 20 条请求日志

## 📦 部署步骤

### 1. 创建云函数

1. 登录 [腾讯云函数控制台](https://console.cloud.tencent.com/scf)
2. 点击「新建」创建函数
3. 选择「从头开始」

### 2. 配置函数

- **函数名称**：自定义（如 `proxy-service`）
- **运行环境**：`Python 3.9`
- **函数类型**：事件函数
- **提交方法**：本地上传文件夹

### 3. 上传代码

将 `index.py` 文件上传到云函数

### 4. 启用函数 URL

1. 在函数配置中找到「触发管理」
2. 创建触发器，选择「函数 URL」
3. 无需配置 API 网关
4. 获取生成的函数 URL

### 5. 完成

访问函数 URL 即可使用代理服务

## 🌍 支持的地域

| 地域代码 | 地域名称 | 地域代码 | 地域名称 |
|---------|---------|---------|---------|
| ap-guangzhou | 广州 | ap-shanghai | 上海 |
| ap-beijing | 北京 | ap-chengdu | 成都 |
| ap-hongkong | 香港 | ap-singapore | 新加坡 |
| ap-tokyo | 东京 | na-siliconvalley | 硅谷 |
| eu-frankfurt | 法兰克福 | na-ashburn | 弗吉尼亚 |

## ⚙️ 技术细节

- **运行环境**：Python 3.9
- **依赖库**：仅使用 Python 标准库（无需额外依赖）
- **超时时间**：25 秒
- **日志保留**：内存中保留最近 50 条请求记录
- **编码处理**：自动处理文本和二进制内容（Base64 编码）

## 📝 注意事项

1. **超时限制**：单次请求超时时间为 25 秒
2. **日志存储**：日志存储在内存中，函数重启后会清空
3. **请求头过滤**：自动过滤 `host`、`x-forwarded-*` 等代理相关头
4. **CORS 支持**：所有响应自动添加 CORS 头，支持跨域访问
5. **费用说明**：按实际调用次数和执行时间计费，详见[腾讯云函数计费说明](https://cloud.tencent.com/document/product/583/12284)

## 📚 相关文档

- [腾讯云函数官方文档](https://cloud.tencent.com/document/product/583)
- [函数 URL 使用指南](https://cloud.tencent.com/document/product/583/96099)
- [Python 运行环境说明](https://cloud.tencent.com/document/product/583/55592)

## 📄 许可证

MIT License

---

**提示**：本项目仅供学习和个人使用，请遵守目标网站的使用条款和相关法律法规。

