# AstrBot 塔塔露插件

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-v1.0.17-blue.svg)](metadata.yaml)
[![AstrBot](https://img.shields.io/badge/AstrBot-plugin-7c3aed.svg)](https://github.com/Soulter/AstrBot)

面向 Final Fantasy XIV 国服/国际服玩家的 AstrBot 插件，提供时尚品鉴、活动日历、副本攻略、石之家内容、招募板、微博资讯、物品资料、市场价格、房屋空房、FFLogs 输出分位、角色 Logs 和塔罗抽卡等查询功能。

## 功能特性

### 核心命令

| 命令 | 功能说明 | 返回形式 |
| --- | --- | --- |
| `帮帮忙` | 查看可用命令 | 文本 |
| `暖暖` | 查询本周 FF14 时尚品鉴作业 | 图片 / 文本兜底 |
| `选门` | 随机给出 5 次藏宝洞左右门选择 | 文本 |
| `仙人彩` | 随机给出 3 组仙人彩号码 | 文本 |
| `日历` | 查询国服 / 国际服活动日历 | 文本 |
| `攻略` | 查询副本攻略 | 图片 / 文本 |
| `石之家` | 查询石之家公开帖子和攻略 | 文本 |
| `招募` | 查询 FF14 国服招募板 | 图片 |
| `看看微博` | 查询 FF14 官方微博最新消息 | 文本 |
| `物品` | 查询物品基础信息和获取方式 | 图标 + 图片 |
| `价格` | 查询市场板物价 | 图片 |
| `房子` / `房屋` | 查询指定服务器空房 | 图片 / 文本 |
| `输出` | 查询 FFLogs 输出分位 | 文本 |
| `logs` | 查询角色 FFLogs 战绩 | 文本 |
| `抽卡` | 随机抽取一张 FF14 塔罗牌 | 文字图片 + 塔罗牌图片 |

### 数据能力

| 模块 | 能力说明 |
| --- | --- |
| 日历 | 支持国服和国际服日历，主备数据源自动切换 |
| 招募 | 支持大区、具体服务器、分类、职业、关键词和数量筛选 |
| 物品 | 支持名称和物品 ID 查询，返回来源、图标和 Garland Tools 链接 |
| 价格 | 支持四大区、具体服务器、HQ 和返回数量筛选 |
| 房屋 | 支持服务器、房区、房型、房号和返回数量筛选 |
| FFLogs | 支持国服 / 国际服、rDPS / aDPS / pDPS / nDPS / cDPS、角色公开战绩查询 |
| 图片输出 | 文本转图片默认使用系统字体，也可在配置页指定字体路径 |

## 安装方法

在 AstrBot 插件管理页面安装远程插件：

```text
https://github.com/jawwe/astrbot_plugin_tataru
```

安装后在 AstrBot WebUI 重载插件即可使用。

## 使用方法

### 基础查询

```text
帮帮忙
暖暖
选门
仙人彩
抽卡
```

### 日历

```text
日历
日历 国服
日历 国际服
```

### 攻略

```text
攻略 副本名
攻略 副本等级 副本名
攻略 副本名 文本
```

### 石之家

```text
石之家
石之家 帖子 幻化 5
石之家 攻略 零式 10
石之家 招募 副本 妖星乱舞 5
石之家 招募 萌新 5
石之家 招募 其他 5
石之家 招募 RP 5
```

默认查询最新帖子。可指定 `帖子` 或 `攻略`，再附加关键词和数量；默认 `10` 条，最多 `20` 条。

在 `石之家 招募` 下，可查询公开的 `副本`、`萌新`、`其他` 和 `RP` 招募；部队招待需要登录态，会在石之家账号绑定功能中提供。

### 石之家账号与签到

以下命令仅能在私聊中使用。凭据按平台和用户独立保存到插件本地 SQLite 数据库，不会在消息或日志中回显。

```text
石之家 绑定 Cookie 请求头
石之家 绑定 Bearer Token
石之家 我的
石之家 通知
石之家 统计
石之家 统计 零式
石之家 统计 深层
石之家 幻化
石之家 幻化 夏日 5
石之家 幻化 装备 纯白长袍
石之家 幻化 详情 265250
石之家 签到
石之家 自动签到 开启
石之家 自动签到 关闭
石之家 解绑
```

绑定会先验证账号是否已绑定角色。自动签到默认关闭；开启后，插件会在 `Asia/Shanghai` 时区的配置时点执行，每个账号每天最多尝试一次。

`石之家 我的` 返回当前绑定角色档案；`石之家 通知` 返回系统、评论、招募和粉丝等未读计数。

`石之家 统计` 默认汇总当前角色有记录的战场、绝境、钓鱼、零式、幻化、蜃景幻界和深层迷宫数据。可指定 `战场`、`绝境`、`钓鱼`、`零式`、`幻化`、`蜃景` 或 `深层` 查询单项。

`石之家 幻化` 查询投稿列表或按标题检索；使用 `装备` 可按装备名称检索相关投稿，使用 `详情` 加投稿 ID 可查看单条投稿。

### 招募

```text
招募 陆行鸟
招募 红玉海
招募 战士
招募 陆行鸟 高难任务 光暗未来绝境战
招募 红玉海 高难任务 战士 20
```

支持四大区、具体服务器、职业、分类、关键词和数量筛选。数字参数表示返回数量，默认 `10`，最多 `40`。返回结果渲染为竖排卡片图，每张图最多显示 `5` 条招募。

### 物品

```text
物品 铁矿
物品 5114
```

### 价格

```text
价格 铁矿
价格 陆行鸟 铁矿
价格 红玉海 铁矿 HQ 20
```

### 房屋

```text
房子 银泪湖
房子 银泪湖 森都 S
房子 银泪湖 森都一区5号
房屋 红玉海 海都 M
```

### FFLogs 输出分位

```text
输出 海德林 武士
输出 海德林 武士 国际服
输出 海德林 武士 国服 adps
输出 海德林 武士 国服 day10
```

默认查询国服、`rdps` 和最新数据。支持 `rdps`、`adps`、`pdps`、`ndps`、`cdps`。

### FFLogs 角色战绩

```text
logs 角色名 服务器名
logs 角色名 服务器名 国服
logs 角色名 服务器名 国际服
```

角色名支持空格，服务器名放在最后。零式返回 7.x 阿卡狄亚零式的当前标准记录；绝境战会保留最后一次公开有效记录的版本来源。

## 配置选项

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `debug_mode` | `false` | 输出插件指令、缓存和联网请求调试日志；Cookie、Token、密码等敏感字段会自动脱敏 |
| `proxy_enabled` | `false` | 开启后插件全部联网请求通过 HTTP 代理发送；关闭时保持直连 |
| `proxy_host` | 空 | HTTP 代理 IP 或主机名，不填写协议、端口或路径 |
| `proxy_port` | `0` | HTTP 代理端口，启用代理时必须为 `1-65535` |
| `proxy_username` | 空 | 可选的 HTTP 代理认证用户名，需与代理密码同时填写 |
| `proxy_password` | 空 | 可选的 HTTP 代理认证密码，插件日志不会输出该值 |
| `use_global_calendar` | `false` | `日历` 命令无参数时默认查询国际服日历 |
| `weibo_cookie` | 空 | 微博 Cookie，可提高 `看看微博` 稳定性 |
| `fflogs_client_id` | 空 | FFLogs API Client ID，用于 `输出` 动态匹配和 `logs` 查询 |
| `fflogs_client_secret` | 空 | FFLogs API Client Secret，用于获取 FFLogs OAuth token |
| `use_global_fflogs` | `false` | `输出` 和 `logs` 默认查询国际服 FFLogs |
| `font_path` | 空 | 文本转图片字体路径，留空时自动尝试 Linux 系统中文字体 |
| `ffxiv_icon_font_path` | 空 | `招募` 卡片渲染 FFXIV 游戏内特殊图标字符时使用的本地图标字体路径 |
| `risingstones_checkin_hour` | `8` | 已开启石之家自动签到的账号每日执行时点，使用 `Asia/Shanghai` 时区 |

### 字体建议

插件不内置字体文件。图片输出需要中文字体时，推荐下载并配置 `SimHei.ttf`：

- 下载地址：[SimHei.ttf](https://github.com/StellarCN/scp_zh/blob/master/fonts/SimHei.ttf)
- 配置方式：在 AstrBot 插件配置页的 `font_path` 填写字体文件绝对路径。
- 留空时：插件会自动尝试 Linux 常见字体，如 Noto Sans CJK、文泉驿等。

`招募` 卡片内如果出现游戏内特殊图标字符，可下载 Lodestone 图标字体到本地，并在 `ffxiv_icon_font_path` 填写绝对路径：

- 推荐字体：[FFXIV_Lodestone_SSF.ttf](https://img.finalfantasyxiv.com/lds/pc/global/fonts/FFXIV_Lodestone_SSF.ttf)
- 备用格式：[FFXIV_Lodestone_SSF.woff](https://img.finalfantasyxiv.com/lds/pc/global/fonts/FFXIV_Lodestone_SSF.woff)

### Cookie 必填提醒
**微博Cookie为必填项**，插件虽然允许在未配置 Cookie 时启动，但**必须配置 Cookie 后才能正常抓取数据**。请务必按照下方步骤获取并配置Cookie。

### 如何获取微博 Cookie

1. 在电脑浏览器打开 [微博移动端官网](https://m.weibo.cn/) 并登录。
2. 按 `F12` 打开开发者工具，切换到 `网络 (Network)` 选项卡。
3. 刷新页面，在左侧列表中找到第一个 `m.weibo.cn` 的请求（或者任何一个 `getIndex` 请求）。
4. 在右侧的 `请求标头 (Request Headers)` 中找到 `Cookie` 字段。
5. 复制该字段的完整值，粘贴到插件设置的 `weibo_cookie` 中。

### Cookie 注意事项
- Cookie具有有效期，失效后需要重新获取。
- 请勿在多设备同时登录同一账号，可能导致Cookie失效。
- 获取Cookie时请确保使用微博移动端官网 (m.weibo.cn)，而非PC端官网。

## 项目结构

```text
astrbot_plugin_tataru/
├── main.py
├── metadata.yaml
├── _conf_schema.json
├── requirements.txt
├── CHANGELOG.md
├── LICENSE
├── README.md
├── logo.png
├── .gitignore
└── data/
    ├── boss.json
    ├── job.json
    ├── calendar.ics
    └── TarotImages/
```

## 数据源与参考项目

- [AstrBot](https://github.com/AstrBotDevs/AstrBot)：插件运行框架。
- [Soulter/helloworld](https://github.com/Soulter/helloworld)：AstrBot 插件结构参考模板。
- [TataruBot2](https://github.com/aaron-lii/TataruBot2)：原始功能来源。
- [remote-party-finder](https://github.com/LittleNightmare/remote-party-finder)：招募板 API 数据源。
- [XIVAPI v2](https://xivapi-v2.xivcdn.com/zh-cn/)：FF14 游戏数据查询。
- [Garland Tools 国服站](https://garlandtools.cn/)：物品详情、来源和图标数据源。
- [Universalis](https://docs.universalis.app/)：市场板物价 API 数据源。
- [艾欧泽亚售楼中心](https://house.ffxiv.cyou/)：房屋空房 API 数据源。
- [FF14.org](https://ff14.org/duty)：副本攻略数据源。
- [石之家](https://ff14risingstones.web.sdo.com/pc/index.html)：国服社区帖子和攻略数据源。
- [Google Calendar](https://calendar.google.com/)：活动日历主数据源。
- [iCloud Calendar](https://www.icloud.com/calendar/)：活动日历备用数据源。
- [微博](https://weibo.com/1797798792)：FF14 官方微博数据源。
- [FFLogs statistics](https://cn.fflogs.com/)：输出分位数据源。
- [FFLogs API](https://cn.fflogs.com/api/docs)：FFLogs metadata 和角色战绩数据源。
- [fflogsapi](https://fflogsapi.readthedocs.io/en/latest/index.html)：FFLogs API 调用方式参考。
- [Pillow](https://python-pillow.org/)：文本转图片渲染。
- [icalendar](https://icalendar.readthedocs.io/)：ICS 日历解析。

## 许可证

本项目使用 MIT License，详见 [LICENSE](LICENSE)。
