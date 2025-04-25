## OPDS4ZLIBRARY

Z-library的OPDS封装，这样用OPDS客户端就能直接访问zlib，不再需要其他计算设备下载中转了。


## 🛣 Roadmap

| 状态 | 任务 | 说明 |
|:---|:---|:---|
| ✅ 完成 | 基础OPDS目录（/opds, /opds/root.xml, /opds/opensearch.xml） | 兼容常见OPDS客户端 |
| ✅ 完成 | 搜索+分页功能（/opds/search） | 支持多关键词检索 |
| ✅ 完成 | Popular推荐（/opds/popular） | 模拟分类浏览 |
| ✅ 完成 | 带登录cookie的中转下载 | 保证大部分文件能顺利下载 |
| 🔥 进行中 | 下载异常容错 | 403/404处理，超时处理，错误提示 |
| 🆕 计划 | `/opds/new` 新书推荐目录 | 解析Z-Lib首页推荐 |
| 🆕 计划 | `/opds/category/{subject}` 分类检索 | 比如编程、历史、医学 |
| 🆕 计划 | `/opds/author/{author}` 作者浏览 | 通过作者名搜索 |
| 🆕 计划 | 基于 sertraline/zlibrary API 的搜索加速模式 | 高速但不稳定 |
| 🆕 计划 | 登录Cookie定时刷新 | 通过Playwright后台刷新登录状态 |
| 🆕 计划 | 加入 API-Key或BasicAuth保护 | 防止被爬虫滥用 |
| 🆕 计划 | Docker打包 | 支持NAS/VPS一键部署 |

---

> 💬 当前已支持常见OPDS客户端如 Marvin, Moon+ Reader, Librera等兼容访问。

