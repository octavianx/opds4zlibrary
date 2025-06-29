 

# 📖 Z-Library OPDS Proxy

本项目将 Z-Library 的内容包装为标准 OPDS Catalog，可以被各类阅读器（如 Marvin、Lithium、Aldiko、Moon+ Reader等）直接浏览和下载。

---

## 🛠 安装与环境初始化

### 1. 克隆项目

略，进入项目目录

### 2. 创建虚拟环境（推荐）

```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

*必要依赖包括：* `fastapi`, `httpx`, `beautifulsoup4`, `python-dotenv`, `uvicorn` 等。


###  **Playwright 安装浏览器引擎**

Playwright 是用来自动化登录 Z-Library 的，它需要额外安装浏览器驱动：


安装 Playwright Python SDK：

```bash
   pip install playwright
```

安装 playwright 浏览器驱动
```bash
playwright install
```

（此命令会下载 Chromium / Firefox / WebKit 三个浏览器的无头版本）

如果你只需要 Chromium，可以指定安装：

```bash
playwright install chromium
```

⚡ 注意：必须执行 playwright install，否则无法进行自动化登录操作。

### 4. 配置 ` config.env `  # 明确指定路径
`

在项目根目录创建 `config.env` 文件，内容示例：

```bash
ZLIB_EMAIL= "your@email.com"
ZLIB_PASSWORD= "your_password"
 
NYT_API_KEY="仅当你需要使用NewYorkTimes功能时使用"

OPDS_USER="yourname"
OPDS_PASS="yourpass"


```

用于Playwright自动登录提取Z-Lib登录cookie。

> ⚡ **注意：首次登录需要执行 playwright 自动登录工具，后续将使用本地缓存cookie，无需重复登录。**

---

## 🚀 启动服务

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

启动后访问：

- OPDS Catalog根目录： `http://localhost:8000/opds`
- 示例搜索（如Python相关书籍）： `http://localhost:8000/opds/search?q=python`

可以在 OPDS 客户端添加 `http://your-server-ip:8000/opds` 作为书库源！

---

## 🔑 第一次使用？登录并提取 Z-Lib Cookie

执行一次以下命令，自动登录并保存 cookie：

```bash
python zlib_opds_launcher.py
```

登录成功后，会生成 `zlib_cookies.json` 文件，供本地OPDS代理读取使用。

---

## 💡 注意事项

- 本项目为教育研究用途，请勿用于商业行为。
- 访问Z-Lib需要有效账号，请妥善保管自己的账户信息。
- 请遵守所在地区法律法规，对于使用本代码所产生的后果，请自行评估并承担。

---

## 🛣 Roadmap

| 状态 | 任务 | 说明 |
|:------- |:---- |:---- |
| ✅ 完成 | 基础OPDS目录 | 兼容常见OPDS客户端 |
| ✅ 完成 | 搜索+分页功能（/opds/search） | 支持多关键词检索 |
| 🆕 计划 | Popular推荐（/opds/popular） | 模拟分类浏览 |
| ✅ 完成 | 带登录cookie的中转下载 | 保证大部分文件能顺利下载 |
| ✅ 完成 | HTTP BasicAuth for OPDS | 防止被爬虫滥用 |
| ✅ 完成 | 支持Moon reader, 支持 KyBook 3 | 多客户端支持 |
| ✅ 完成 | support new york times best seller ranking list |  multiple sourcing |
| 🆕 计划 | `/opds/new` 新书推荐目录 | 解析Z-Lib首页推荐 |
| 🆕 计划 | `/opds/category/{subject}` 分类检索 | 比如编程、历史、医学 |
| 🆕 计划 | `/opds/author/{author}` 作者浏览 | 通过作者名搜索 |
| 🆕 计划 | 基于 sertraline/zlibrary API 的搜索加速模式 | 高速但不稳定 |
| 🆕 计划 | 登录Cookie定时刷新 | 通过Playwright后台刷新登录状态 |
| 🆕 计划 | Docker打包 | 支持NAS/VPS一键部署 |
| 🆕 计划 | 下载异常容错 | 403/404处理，超时处理，错误提示 |


---

> 💬 当前已支持常见OPDS客户端如 Marvin, Moon+ Reader, Librera等兼容访问。

