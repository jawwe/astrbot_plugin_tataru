# AstrBot 塔塔露插件

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-v1.0.0-blue.svg)](metadata.yaml)
[![AstrBot](https://img.shields.io/badge/AstrBot-plugin-7c3aed.svg)](https://github.com/Soulter/AstrBot)

面向 Final Fantasy XIV 国服/国际服玩家的 AstrBot 插件，提供时尚品鉴、活动日历、副本攻略、招募板、微博资讯、物品资料、市场价格、房屋空房、FFLogs 输出分位、角色 Logs 和塔罗抽卡等查询功能。

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

### 招募

```text
招募 陆行鸟
招募 红玉海
招募 战士
招募 陆行鸟 高难任务 光暗未来绝境战
招募 红玉海 高难任务 战士 20
```

支持四大区、具体服务器、职业、分类、关键词和数量筛选。数字参数表示返回数量，默认 `10`，最多 `40`。

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
| `use_global_calendar` | `false` | `日历` 命令无参数时默认查询国际服日历 |
| `weibo_cookie` | 空 | 微博 Cookie，可提高 `看看微博` 稳定性 |
| `fflogs_client_id` | 空 | FFLogs API Client ID，用于 `输出` 动态匹配和 `logs` 查询 |
| `fflogs_client_secret` | 空 | FFLogs API Client Secret，用于获取 FFLogs OAuth token |
| `use_global_fflogs` | `false` | `输出` 和 `logs` 默认查询国际服 FFLogs |
| `font_path` | 空 | 文本转图片字体路径，留空时自动尝试 Linux 系统中文字体 |

### 字体建议

插件不内置字体文件。图片输出需要中文字体时，推荐下载并配置 `SimHei.ttf`：

- 下载地址：[SimHei.ttf](https://github.com/StellarCN/scp_zh/blob/master/fonts/SimHei.ttf)
- 配置方式：在 AstrBot 插件配置页的 `font_path` 填写字体文件绝对路径。
- 留空时：插件会自动尝试 Linux 常见字体，如 Noto Sans CJK、文泉驿等。

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

- [AstrBot](https://github.com/Soulter/AstrBot)：插件运行框架。
- [Soulter/helloworld](https://github.com/Soulter/helloworld)：AstrBot 插件结构参考模板。
- [TataruBot2](https://github.com/aaron-lii/TataruBot2)：原始功能来源。
- [remote-party-finder](https://github.com/LittleNightmare/remote-party-finder)：招募板 API 数据源。
- [XIVAPI v2](https://xivapi-v2.xivcdn.com/zh-cn/)：FF14 游戏数据查询。
- [Garland Tools 国服站](https://garlandtools.cn/)：物品详情、来源和图标数据源。
- [Universalis](https://docs.universalis.app/)：市场板物价 API 数据源。
- [艾欧泽亚售楼中心](https://house.ffxiv.cyou/)：房屋空房 API 数据源。
- [FF14.org](https://ff14.org/duty)：副本攻略数据源。
- [Google Calendar](https://calendar.google.com/)：活动日历主数据源。
- [iCloud Calendar](https://www.icloud.com/calendar/)：活动日历备用数据源。
- [微博](https://weibo.com/1797798792)：FF14 官方微博数据源。
- [FFLogs statistics](https://cn.fflogs.com/)：输出分位数据源。
- [FFLogs API](https://cn.fflogs.com/api/docs)：FFLogs metadata 和角色战绩数据源。
- [fflogsapi](https://fflogsapi.readthedocs.io/en/latest/index.html)：FFLogs API 调用方式参考。
- [Pillow](https://python-pillow.org/)：文本转图片渲染。
- [icalendar](https://icalendar.readthedocs.io/)：ICS 日历解析。
- [Sakura520222/astrbot_plugin_web_analyzer](https://github.com/Sakura520222/astrbot_plugin_web_analyzer)：README 结构参考。

## 许可证

本项目使用 MIT License，详见 [LICENSE](LICENSE)。
