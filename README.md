# astrbot_plugin_tataru

TataruBot2 的 AstrBot 插件迁移版本。当前分支只保留 AstrBot 插件根目录内容，可直接作为远程插件安装。

## 安装

在 AstrBot 插件管理页面安装远程插件：

```text
https://github.com/jawwe/TataruBot2/tree/codex-astrbot-plugin-tataru
```

安装后在 AstrBot WebUI 重载插件即可使用。

## 已实现功能

| 命令 | 功能 | 返回形式 |
| --- | --- | --- |
| `帮帮忙` | 查看塔塔露当前可用命令 | 文本 |
| `暖暖` | 查询本周 FF14 时尚品鉴作业 | 图片，失败时返回 QQ 文档链接 |
| `选门` | 随机给出 5 次藏宝洞左右门选择 | 文本 |
| `仙人彩` | 随机给出 3 组仙人彩号码 | 文本 |
| `日历` | 查询国服/国际服活动日历 | 文本 |
| `攻略` | 查询副本攻略 | 默认图片，带 `文本` 参数时返回文本 |
| `招募` | 查询 FF14 国服招募板 | 图片 |
| `看看微博` | 查询 FF14 官方微博最新消息 | 文本 |
| `物品` | 查询物品基础信息和获取方式 | 图标 + 图片 |
| `价格` | 查询市场板物价 | 图片 |
| `房子` / `房屋` | 查询指定服务器空房 | 图片，参数错误时返回文本 |
| `输出` | 查询 FFLogs 输出分位 | 文本 |
| `抽卡` | 随机抽取一张 FF14 塔罗牌 | 文字图片 + 塔罗牌图片 |

## 命令说明

### 帮帮忙

```text
帮帮忙
```

返回当前已迁移命令列表，以及仍在迁移中的功能。

### 暖暖

```text
暖暖
```

返回本周时尚品鉴作业图片。优先尝试解析 B 站/腾讯文档等来源；如果无法获取图片，会返回 QQ 文档链接。

### 选门

```text
选门
```

返回 5 个随机左右选择，例如：

```text
塔塔露在藏宝洞中横冲直撞！
左 右 右 左 右
```

### 仙人彩

```text
仙人彩
```

返回 3 组随机 4 位数字，用于每周仙人彩参考。

### 日历

```text
日历
日历 国服
日历 国际服
```

返回近期活动日历文本，按近 2 天结束、近 7 天内、未来活动分组。

配置项：

- `默认使用国际服日历`：关闭时默认国服，开启后默认国际服。
- 命令参数会覆盖默认配置。

数据源：Google Calendar 为主源，iCloud Calendar 为备用源。国服日历内置了一份本地缓存兜底。

### 攻略

```text
攻略 副本名
攻略 副本等级 副本名
攻略 副本名 文本
```

示例：

```text
攻略 90 佐特塔
攻略 佐特塔 文本
```

默认把攻略内容渲染成图片返回；带 `文本` 参数时直接返回纯文本。若匹配到多个副本，会返回候选列表让用户重新指定。

### 招募

```text
招募 陆行鸟
招募 红玉海
招募 战士
招募 陆行鸟 随机任务
招募 陆行鸟 绝龙诗
招募 陆行鸟 高难任务 光暗未来绝境战
招募 红玉海 高难任务 战士 20
```

参数能力：

- 支持四大区：`陆行鸟`、`莫古力`、`猫小胖`、`豆豆柴`。
- 支持具体服务器名，例如 `红玉海`。
- 支持职业名筛选，例如 `战士`。
- 支持分类筛选：随机任务、迷宫挑战、行会令、讨伐歼灭战、大型任务、高难任务、PvP、金碟、危命任务、寻宝、狩猎、采集、深层迷宫、特殊场景探索、多变迷宫、其他。
- 未识别为分类/职业/服务器的参数会作为关键词搜索。
- 数字参数表示返回数量，默认 10，最多 40。

返回图片内容包含：分类、搜索词、职业筛选状态、招募副本、描述、发布者、服务器、人数、剩余时间、更新时间等。

数据源优先级：remote-party-finder v2 API + XIVAPI v2 解析世界名/副本名，失败时回退 v1 API，再失败时回退网页解析。

### 看看微博

```text
看看微博
```

返回 FF14 官方微博最新 5 条非置顶微博，内容包含微博标题、发布时间和微博原文链接。命令会优先使用微博移动端接口，并在配置 Cookie 时使用网页端接口补足数据；会跳过广告、推荐、非微博正文卡片和置顶微博。

配置项：

- `微博 Cookie`：可选。微博移动端接口可能对匿名请求返回 432 或限流，填写 Cookie 后会随请求发送，提高获取稳定性。

数据源：微博移动端接口，账号为《最终幻想14》官方微博。

### 物品

```text
物品 铁矿
物品 5114
```

返回图标和物品资料图片。内容包括物品名、分类、物品等级、装备等级、说明、采集/钓鱼/制作/商店/兑换/怪物掉落/副本/任务奖励等来源信息，以及 Garland Tools 详情链接。

数据源：

- 物品详情、来源和图标直接使用 Garland Tools 国服站。
- 名称到物品 ID 的搜索使用 XIVAPI v2。
- 如果直接输入数字，会按物品 ID 查询 Garland Tools。

### 价格

```text
价格 铁矿
价格 陆行鸟 铁矿
价格 红玉海 铁矿
价格 红玉海 铁矿 HQ 20
```

参数能力：

- 未指定范围时默认查询四大区，合并后按单价返回最低 10 条挂单。
- 支持四大区和具体服务器名作为筛选项。
- 支持 `HQ`、`高品质`、`高品` 参数，只返回 HQ 挂单。
- 数字参数表示返回数量，默认 10，最多 40。
- 支持旧别名：`鸟`、`猪`、`猫`、`狗`、`柔风`。

返回图片内容包含：物品名、查询范围、品质筛选、返回数量、单价、数量、总价、HQ/NQ、服务器、雇员名、更新时间。

数据源：Universalis API；物品 ID 搜索复用 XIVAPI v2。价格查询不抓网页。

### 房子

```text
房子 银泪湖
房子 银泪湖 森都 S
房子 银泪湖 森都一区
房子 银泪湖 森都一区5号
房子 银泪湖 森都 5号
房屋 红玉海 海都 M
```

参数能力：

- 服务器名使用国服服务器，例如 `银泪湖`、`红玉海`。
- 主城名支持：森都、海都、沙都、白银、雪都，也支持海雾村、薰衣草苗圃、高脚孤丘、白银乡、穹顶皓天等完整地区名。
- 房屋大小支持：`S`、`M`、`L`。
- 支持房区筛选，例如 `森都一区`、`森都1区`。
- 支持房号筛选，房号需要带主城区域，房区可选，例如 `森都一区5号` 或 `森都 5号`。
- 数字参数表示返回数量，默认 10，最多 40。

返回图片内容包含：服务器、筛选条件、空房总数、主城、房屋大小、区号、门牌号、价格、购买方式、土地类型和更新时间。没有空房时返回文本提示。

数据源：优先使用 [艾欧泽亚售楼中心](https://house.ffxiv.cyou/) 的 `https://house.ffxiv.cyou/api/sales` API。

### 输出

```text
输出 海德林 武士
输出 海德林 武士 国际服
输出 海德林 武士 国服
输出 海德林 武士 国服 adps
输出 海德林 武士 国服 pdps
输出 海德林 武士 国服 day10
```

参数能力：

- `boss名` 支持 FFLogs metadata 补全后的中文名、英文名和别名；本地映射查不到时，会在配置 FFLogs API 凭据后动态拉取 metadata 再匹配。
- `职业名` 支持中文名、英文名和内置别名，已包含蝰蛇剑士、绘灵法师等当前 FFLogs 职业。
- 默认查询国服、`rdps`、最新一天。
- 加 `国际服` 查询国际服 FFLogs；加 `国服` 查询国服 FFLogs。
- 支持显式指定 `rdps`、`adps`、`pdps`、`ndps`、`cdps`；默认 `rdps` 不向 FFLogs statistics table 传 `dpstype` 参数。
- 加 `dayN` 查询网页 statistics table 中第 N 天数据。

返回文本内容包含：服务器、DPS 类型、数据源、版本分区、副本、boss、职业、天数，以及 10%、25%、50%、75%、95%、99%、100% 分位。

配置项：

- `FFLogs API Client ID`
- `FFLogs API Client Secret`

数据源优先级：分位数据使用对应站点的 FFLogs statistics table 网页解析，并使用网页统计表的 DPS 聚合口径；配置 FFLogs API 凭据后，本地 boss 映射查不到时会使用 FFLogs metadata 动态匹配 boss。

### 抽卡

```text
抽卡
```

随机抽取一张 FF14 塔罗牌，返回说明文字图片和塔罗牌图片。

## 配置项

当前插件配置文件 `_conf_schema.json` 提供：

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `默认使用国际服日历` | `false` | 控制 `日历` 命令无参数时默认查询国服还是国际服。 |
| `微博 Cookie` | 空 | 可选。供 `看看微博` 请求微博移动端接口时使用，提高稳定性。 |
| `FFLogs API Client ID` | 空 | 可选。供 `输出` 在本地 boss 映射查不到时动态查询 FFLogs metadata。 |
| `FFLogs API Client Secret` | 空 | 可选。供 `输出` 获取 FFLogs OAuth token。 |
| `默认使用国际服 FFLogs` | `false` | 控制 `输出` 命令无服务器参数时默认查询国服还是国际服。 |

## 后续待迁移

暂无。

## 使用的项目和服务

- [AstrBot](https://github.com/Soulter/AstrBot)：插件运行框架。
- [Soulter/helloworld](https://github.com/Soulter/helloworld)：AstrBot 插件结构参考模板。
- [TataruBot2](https://github.com/jawwe/TataruBot2)：原始功能来源。
- [remote-party-finder](https://github.com/LittleNightmare/remote-party-finder)：招募板 API 数据源。
- [XIVAPI v2](https://xivapi-v2.xivcdn.com/zh-cn/)：FF14 游戏数据查询，用于物品、世界、副本等 ID 解析。
- [Garland Tools 国服站](https://garlandtools.cn/)：物品详情、来源和图标数据源。
- [Universalis](https://docs.universalis.app/)：市场板物价 API 数据源。
- [艾欧泽亚售楼中心](https://house.ffxiv.cyou/)：房屋空房 API 数据源。
- [FF14.org](https://ff14.org/duty)：副本攻略数据源。
- [Google Calendar](https://calendar.google.com/)：活动日历主数据源。
- [iCloud Calendar](https://www.icloud.com/calendar/)：活动日历备用数据源。
- [腾讯文档](https://docs.qq.com/)：暖暖功能兜底链接。
- [Bilibili](https://www.bilibili.com/)：暖暖视频来源之一。
- [微博](https://weibo.com/1797798792)：`看看微博` 的 FF14 官方微博数据源。
- [FFLogs statistics](https://cn.fflogs.com/)：`输出` 的分位数据源。
- [FFLogs API](https://cn.fflogs.com/api/docs)：`输出` 动态匹配 boss metadata 的数据源。
- [fflogsapi](https://fflogsapi.readthedocs.io/en/latest/index.html)：FFLogs API 调用方式参考。
- [Pillow](https://python-pillow.org/)：文本转图片渲染。
- [icalendar](https://icalendar.readthedocs.io/)：ICS 日历解析。
