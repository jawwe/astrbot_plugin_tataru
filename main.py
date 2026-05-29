import asyncio
from dataclasses import dataclass
from datetime import date, datetime
from email.utils import parsedate_to_datetime
import html
import json
import random
import re
from pathlib import Path
from urllib.parse import quote, urlencode

import aiohttp
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
import astrbot.api.message_components as Comp
from astrbot.api.star import Context, Star, register
from icalendar import Calendar
from PIL import Image, ImageDraw, ImageFont


PLUGIN_DIR = Path(__file__).resolve().parent
DATA_DIR = PLUGIN_DIR / "data"
TAROT_DIR = DATA_DIR / "TarotImages"
TAROT_JSON = TAROT_DIR / "ff14_tarot.json"
JOB_JSON = DATA_DIR / "job.json"
BOSS_JSON = DATA_DIR / "boss.json"
FONT_PATH = DATA_DIR / "simhei.ttf"
DEFAULT_CN_CALENDAR_PATH = DATA_DIR / "calendar.ics"
CALENDAR_SOURCES = {
    "国服": {
        "primary": (
            "https://calendar.google.com/calendar/ical/"
            "up88drvlnnh2t77hbpqq8v33i2cngfh7%40import.calendar.google.com/public/basic.ics"
        ),
        "fallback": (
            "https://p66-caldav.icloud.com/published/2/"
            "MTAyMTk3MTMxMjExMDIxOXsjasy7WUO0EcKVz7qGEuVjjTlRkgd6"
            "WOZM171uxP_u-QM51M24lHzRlAQir-oodDRRTzZeusSLbw0snkZoqI4"
        ),
        "bundled": DEFAULT_CN_CALENDAR_PATH,
    },
    "国际服": {
        "primary": (
            "https://calendar.google.com/calendar/ical/"
            "1gpnler51bgs1ajti10ao946ou367bf6%40import.calendar.google.com/public/basic.ics"
        ),
        "fallback": (
            "https://p66-caldav.icloud.com/published/2/"
            "MTAyMTk3MTMxMjExMDIxOXsjasy7WUO0EcKVz7qGEuVzSK8L9ZRQYf1sxUFeH1A1a22"
            "GJLf6nfk2-CZNYMv5iOxCNlUR-umbJKFWWAUVRp8"
        ),
        "bundled": None,
    },
}
QQ_DOC_URL = "https://docs.qq.com/sheet/DY2lCeEpwemZESm5q?tab=dewveu&c=A1A0A0"
BILI_USER_ID = 15503317
WEIBO_UID = "1797798792"
WEIBO_API_BASE = "https://m.weibo.cn/api/container/getIndex"
WEIBO_MOBILE_BASE = "https://m.weibo.cn"
WEIBO_WEB_BASE = "https://weibo.com"
WEIBO_WEB_TIMELINE_API = "https://weibo.com/ajax/statuses/mymblog"
FFLOGS_HOSTS = {False: "https://www.fflogs.com", True: "https://cn.fflogs.com"}
FFLOGS_PERCENTILES = [10, 25, 50, 75, 95, 99, 100]
FFLOGS_STAT_AGGREGATES = ["persecondamount", "amount", "persecond", "raw", "normalized"]
FFLOGS_METADATA_QUERY = """
query {
  worldData {
    zones {
      id
      name
      frozen
      difficulties { id name }
      partitions { id name compactName default }
      encounters { id name }
    }
  }
}
"""
FFLOGS_METADATA_CACHE: dict[str, dict] = {}
DUNGEON_NOTE_URL = "https://ff14.org/duty"
GARLAND_BASE_URL = "https://garlandtools.cn"
PARTY_FINDER_URL = "https://xivpf.littlenightmare.top/listings"
PARTY_FINDER_API_V1_URL = "https://xivpf.littlenightmare.top/api/listings"
PARTY_FINDER_API_V2_URL = "https://xivpf.littlenightmare.top/api/v2/listings"
XIVAPI_BASE_URL = "https://xivapi-v2.xivcdn.com/api"
HOUSE_API_URL = "https://house.ffxiv.cyou/api/sales"
DATA_CENTRES = ["陆行鸟", "莫古力", "猫小胖", "豆豆柴"]
CN_WORLD_DATA_CENTRES = set(DATA_CENTRES)
CN_WORLD_NAME_CACHE: dict[str, dict] | None = None
HOUSE_DEFAULT_LISTINGS = 10
HOUSE_MAX_LISTINGS = 40
HOUSE_SERVER_IDS = {
    "红玉海": 1167,
    "神意之地": 1081,
    "拉诺西亚": 1042,
    "幻影群岛": 1044,
    "萌芽池": 1060,
    "宇宙和音": 1173,
    "沃仙曦染": 1174,
    "晨曦王座": 1175,
    "白银乡": 1172,
    "白金幻象": 1076,
    "神拳痕": 1171,
    "潮风亭": 1170,
    "旅人栈桥": 1113,
    "拂晓之间": 1121,
    "龙巢神殿": 1166,
    "梦羽宝境": 1176,
    "紫水栈桥": 1043,
    "延夏": 1169,
    "静语庄园": 1106,
    "摩杜纳": 1045,
    "海猫茶屋": 1177,
    "柔风海湾": 1178,
    "琥珀原": 1179,
    "水晶塔": 1192,
    "银泪湖": 1183,
    "太阳海岸": 1180,
    "伊修加德": 1186,
    "红茶川": 1201,
}
HOUSE_AREA_NAMES = ["海都", "森都", "沙都", "白银", "雪都"]
HOUSE_AREA_ALIASES = {
    "海雾村": "海都",
    "海雾": "海都",
    "薰衣草苗圃": "森都",
    "薰衣草": "森都",
    "高脚孤丘": "沙都",
    "高脚": "沙都",
    "白银乡": "白银",
    "穹顶皓天": "雪都",
    "穹顶": "雪都",
}
HOUSE_SIZE_NAMES = ["S", "M", "L"]
HOUSE_PURCHASE_TYPES = {
    0: "不可购买",
    1: "先到先得",
    2: "抽签",
}
HOUSE_REGION_TYPES = {
    0: "保留",
    1: "部队",
    2: "个人",
}
MARKET_DEFAULT_SCOPE = "全大区"
MARKET_DEFAULT_LISTINGS = 10
MARKET_MAX_LISTINGS = 40
MARKET_SCOPE_ALIASES = {
    "鸟": "陆行鸟",
    "猪": "莫古力",
    "猫": "猫小胖",
    "狗": "豆豆柴",
    "柔风": "柔风海湾",
}
GARLAND_CORE_DATA: dict | None = None
NODE_NAME_BY_TYPE = {
    0: "矿脉",
    1: "石场",
    2: "良材",
    3: "草场",
    4: "鱼影",
    5: "鱼影",
}
PARTY_CATEGORY_LABELS = {
    "DutyRoulette": "随机任务",
    "Dungeons": "迷宫挑战",
    "Guildhests": "行会令",
    "Trials": "讨伐歼灭战",
    "Raids": "大型任务",
    "HighEndDuty": "高难任务",
    "Pvp": "PvP",
    "GoldSaucer": "金碟",
    "Fates": "危命任务",
    "TreasureHunt": "寻宝",
    "TheHunt": "狩猎",
    "GatheringForays": "采集",
    "DeepDungeons": "深层迷宫",
    "AdventuringForays": "特殊场景探索",
    "V&C Dungeon Finder": "多变迷宫",
    "None": "其他",
}
PARTY_CATEGORY_IDS = {
    "None": 0,
    "DutyRoulette": 2,
    "Dungeons": 4,
    "Guildhests": 8,
    "Trials": 16,
    "Raids": 32,
    "HighEndDuty": 64,
    "Pvp": 128,
    "GoldSaucer": 256,
    "Fates": 512,
    "TreasureHunt": 1024,
    "TheHunt": 2048,
    "GatheringForays": 4096,
    "DeepDungeons": 8192,
    "AdventuringForays": 16384,
    "V&C Dungeon Finder": 32768,
}
PARTY_CATEGORY_ID_LABELS = {
    category_id: PARTY_CATEGORY_LABELS[category]
    for category, category_id in PARTY_CATEGORY_IDS.items()
    if category in PARTY_CATEGORY_LABELS
}
PARTY_CATEGORY_ALIASES = {
    "随机任务": "DutyRoulette",
    "随机": "DutyRoulette",
    "roulette": "DutyRoulette",
    "dutyroulette": "DutyRoulette",
    "迷宫挑战": "Dungeons",
    "迷宫": "Dungeons",
    "dungeons": "Dungeons",
    "行会令": "Guildhests",
    "guildhests": "Guildhests",
    "讨伐歼灭战": "Trials",
    "讨伐": "Trials",
    "歼灭": "Trials",
    "trials": "Trials",
    "大型任务": "Raids",
    "大型": "Raids",
    "raids": "Raids",
    "高难任务": "HighEndDuty",
    "高难度任务": "HighEndDuty",
    "高难度": "HighEndDuty",
    "高难本": "HighEndDuty",
    "高难": "HighEndDuty",
    "零式": "HighEndDuty",
    "绝": "HighEndDuty",
    "highendduty": "HighEndDuty",
    "high-end": "HighEndDuty",
    "high-endduty": "HighEndDuty",
    "pvp": "Pvp",
    "金碟": "GoldSaucer",
    "goldsaucer": "GoldSaucer",
    "危命任务": "Fates",
    "危命": "Fates",
    "fate": "Fates",
    "fates": "Fates",
    "寻宝": "TreasureHunt",
    "宝物库": "TreasureHunt",
    "treasurehunt": "TreasureHunt",
    "狩猎": "TheHunt",
    "恶名精英": "TheHunt",
    "hunt": "TheHunt",
    "thehunt": "TheHunt",
    "采集": "GatheringForays",
    "gatheringforays": "GatheringForays",
    "深层迷宫": "DeepDungeons",
    "死宫": "DeepDungeons",
    "天宫": "DeepDungeons",
    "deepdungeons": "DeepDungeons",
    "特殊场景探索": "AdventuringForays",
    "特殊战场": "AdventuringForays",
    "adventuringforays": "AdventuringForays",
    "fieldoperations": "AdventuringForays",
    "多变迷宫": "V&C Dungeon Finder",
    "异闻": "V&C Dungeon Finder",
    "vc": "V&C Dungeon Finder",
    "v&c": "V&C Dungeon Finder",
    "v&cdungeonfinder": "V&C Dungeon Finder",
    "其他": "None",
    "无": "None",
    "none": "None",
}
PARTY_JOB_ALIASES = {
    "骑士": 19,
    "骑": 19,
    "pld": 19,
    "武僧": 20,
    "僧": 20,
    "mnk": 20,
    "战士": 21,
    "战": 21,
    "war": 21,
    "龙骑": 22,
    "龙骑士": 22,
    "龙": 22,
    "drg": 22,
    "诗人": 23,
    "吟游诗人": 23,
    "诗": 23,
    "brd": 23,
    "白魔": 24,
    "白魔法师": 24,
    "白": 24,
    "whm": 24,
    "黑魔": 25,
    "黑魔法师": 25,
    "黑": 25,
    "blm": 25,
    "召唤": 27,
    "召唤师": 27,
    "召": 27,
    "smn": 27,
    "学者": 28,
    "学": 28,
    "sch": 28,
    "忍者": 30,
    "忍": 30,
    "nin": 30,
    "机工": 31,
    "机工士": 31,
    "机": 31,
    "mch": 31,
    "暗黑": 32,
    "暗黑骑士": 32,
    "暗骑": 32,
    "drk": 32,
    "占星": 33,
    "占星术士": 33,
    "占": 33,
    "ast": 33,
    "武士": 34,
    "侍": 34,
    "sam": 34,
    "赤魔": 35,
    "赤魔法师": 35,
    "赤": 35,
    "rdm": 35,
    "青魔": 36,
    "青魔法师": 36,
    "青": 36,
    "blu": 36,
    "绝枪": 37,
    "绝枪战士": 37,
    "枪刃": 37,
    "gnb": 37,
    "舞者": 38,
    "舞": 38,
    "dnc": 38,
    "钐镰": 39,
    "钐镰客": 39,
    "镰刀": 39,
    "镰": 39,
    "rpr": 39,
    "贤者": 40,
    "贤": 40,
    "sge": 40,
    "蝰蛇": 41,
    "蝰蛇剑士": 41,
    "蝰": 41,
    "vpr": 41,
    "绘灵": 42,
    "绘灵法师": 42,
    "绘": 42,
    "pct": 42,
    "魔兽": 43,
    "魔兽使": 43,
    "bst": 43,
}


@dataclass
class PartyFinderQuery:
    data_centre: str | None
    category: str | None
    search_terms: list[str]
    job_ids: list[int]
    limit: int


@dataclass
class MarketQuery:
    scope_name: str
    scope_type: str
    item_name: str | None
    hq: bool
    limit: int


@dataclass
class HouseQuery:
    server_name: str | None
    area_name: str | None
    size_name: str | None
    ward: int | None
    plot_id: int | None
    limit: int


@dataclass
class LogsQuery:
    boss_name: str | None
    job_name: str | None
    cn_source: bool
    dps_type: str
    day: int


async def aiohttp_get(url: str, res_type: str = "json", timeout_seconds: int = 15, headers: dict | None = None):
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Edge/125.0 Safari/537.36",
    ]
    request_headers = {
        "Connection": "close",
        "User-Agent": random.choice(user_agents),
    }
    if headers:
        request_headers.update(headers)

    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    async with aiohttp.ClientSession(timeout=timeout, headers=request_headers) as session:
        async with session.get(url) as response:
            if response.status != 200:
                return None
            if res_type == "bytes":
                return await response.read()
            if res_type == "text":
                return await response.text()
            try:
                return await response.json(content_type=None)
            except Exception as exc:
                logger.warning(f"JSON响应解析失败: {url}, {exc}")
                return None


def random_left_right() -> str:
    result = []
    for _ in range(5):
        result.append("右" if random.random() > 0.5 else "左")
    return " ".join(result)


def random_lottery() -> str:
    last_num_list = []
    lottery_list = []
    for _ in range(3):
        while True:
            last_num = random.randint(0, 9)
            if last_num not in last_num_list:
                last_num_list.append(last_num)
                break
        lottery_list.append(
            f"{random.randint(0, 9)} {random.randint(0, 9)} "
            f"{random.randint(0, 9)} {last_num}"
        )
    return "\n".join(lottery_list)


def text_to_image(text: str, output_path: Path, width_now: int = 20) -> None:
    font_size = 20
    font = ImageFont.truetype(str(FONT_PATH), size=font_size)

    cursor = 0
    wrapped = ""
    for char in text:
        if char == "\n":
            if len(wrapped) > 1:
                wrapped += char
            cursor = 0
            continue
        cursor += 2 if len(char.encode()) > 1 else 1
        wrapped += char
        if cursor >= 2 * width_now:
            wrapped += "\n"
            cursor = 0

    lines = wrapped.split("\n")
    image = Image.new(
        "RGB",
        (int(width_now * 22), (len(lines) + 1) * (font_size + 2)),
        (255, 255, 255),
    )
    draw = ImageDraw.Draw(image)
    draw.text((10, 10), wrapped, font=font, fill=(0, 0, 0))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="JPEG")


def load_tarot() -> dict:
    with TAROT_JSON.open("r", encoding="utf-8") as tarot_file:
        return json.load(tarot_file)


def load_json_list(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig") as json_file:
        data = json.load(json_file)
    return data if isinstance(data, list) else []


def choose_tarot(tarot_dict: dict) -> tuple[str, Path]:
    info_now = tarot_dict["_塔罗牌堆"][random.randint(0, 43)]
    text_now = info_now.split("[", 1)[0]
    file_name = info_now.rsplit("/", 1)[-1][:-1].replace(" ", "_")
    return text_now, TAROT_DIR / file_name


def create_help_text() -> str:
    return """【塔塔露现有指令】
()括号表示可选的参数
[暖暖] 本周时尚品鉴作业
[选门] 帮你选藏宝洞的门
[仙人彩] 帮你选每周仙人仙彩数字
[日历 (国服/国际服)] 获取FF近期活动日历
[攻略 (副本等级) 副本名关键字 (文本)] 查简单副本攻略
[招募 大区名 (分类) (数量)] 获取指定大区招募板信息
[看看微博] 获取FF官方微博新闻
[物品 物品名] 查询物品信息
[价格 (大区/服务器) 物品名 (HQ) (数量)] 查询市场物价
[房子 服务器名 主城名 房子大小] 查询空房
[输出 boss名 职业名 (国服) (rdps) (day2)] 查询FFLogs输出分段
[抽卡] 随机抽取一张FF14塔罗牌

以下功能仍在迁移中：
"""


def format_calendar_item(info_item: list) -> str:
    end_info = str(info_item[0]).strip().split("+", 1)[0].rsplit(":", 1)[0].replace("-", ".")
    start_info = str(info_item[1]).strip().split("+", 1)[0].rsplit(":", 1)[0].replace("-", ".")
    summary_info = str(info_item[2]).strip()
    return "* " + summary_info + "\n  " + start_info + " 至 " + end_info


def normalize_calendar_date(value) -> tuple[date, date | datetime]:
    if isinstance(value, datetime):
        return value.date(), value
    return value, value


def normalize_calendar_server(value: str | None, default_server: str = "国服") -> str:
    if not value:
        return default_server
    value = value.strip().lower()
    if value in {"国际服", "国际", "global", "intl", "international", "gaia", "mana", "elemental"}:
        return "国际服"
    if value in {"国服", "国", "cn", "china", "陆行鸟", "莫古力", "猫小胖", "豆豆柴"}:
        return "国服"
    return default_server


def command_args(message: str, command: str) -> str:
    message = message.strip()
    if message == command:
        return ""
    if message.startswith(command):
        return message[len(command):].strip()
    return message


def parse_dungeon_query(dungeon_info: str) -> tuple[str | None, str | None, bool]:
    parts = dungeon_info.split()
    if not parts:
        return None, None, False

    dungeon_level = None
    is_text = False
    if "文本" in parts:
        is_text = True
        parts = [part for part in parts if part != "文本"]

    if parts and parts[0].isdigit():
        dungeon_level = parts[0]
        parts = parts[1:]

    if not parts:
        return dungeon_level, None, is_text
    return dungeon_level, parts[0], is_text


def strip_html(text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<.*?>", "", text)
    return html.unescape(text).strip()


def normalize_party_category(value: str | None) -> str | None:
    if not value:
        return None
    key = re.sub(r"\s+", "", value.strip().lower())
    return PARTY_CATEGORY_ALIASES.get(key)


def normalize_party_job(value: str | None) -> int | None:
    if not value:
        return None
    key = re.sub(r"\s+", "", value.strip().lower())
    return PARTY_JOB_ALIASES.get(key)


def parse_party_finder_query(query: str) -> PartyFinderQuery:
    parts = query.split()
    if not parts:
        return PartyFinderQuery(None, None, [], [], 10)

    data_centre = parts[0] if parts[0] in DATA_CENTRES else None
    remain_parts = parts[1:] if data_centre else parts
    category = None
    search_terms = []
    job_ids = []
    limit = 10
    for part in remain_parts:
        if part.isdigit():
            limit = max(1, min(int(part), 40))
            continue
        normalized_category = normalize_party_category(part)
        if normalized_category:
            category = normalized_category
            continue
        job_id = normalize_party_job(part)
        if job_id:
            if job_id not in job_ids:
                job_ids.append(job_id)
            continue
        search_terms.append(part)
    return PartyFinderQuery(data_centre, category, search_terms, job_ids, limit)


def is_hq_token(value: str) -> bool:
    return value.strip().lower() in {"hq", "高品质", "高品", "hq品"}


def truncate_text(text: str, length: int = 80) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= length:
        return text
    return text[:length - 1] + "…"


def clean_weibo_title(text: str) -> str:
    title = strip_html(text)
    title = re.sub(r"全文$", "", title).strip()
    title = re.sub(r"#(?:最终幻想14|FF14)#", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return truncate_text(title or "微博内容为空", 90)


def is_pinned_weibo_card(card: dict, mblog: dict) -> bool:
    title = mblog.get("title")
    title_text = title.get("text") if isinstance(title, dict) else ""
    return any(
        [
            mblog.get("isTop"),
            mblog.get("is_top"),
            card.get("is_top"),
            mblog.get("top"),
            title_text == "置顶",
            "置顶" in str(card.get("title", "") or card.get("desc", "")),
        ]
    )


def get_weibo_headers(cookie: str | None = None, uid: str = WEIBO_UID) -> dict:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 "
            "Mobile/15E148 Safari/604.1"
        ),
        "Accept": "application/json, text/plain, */*",
        "Referer": f"{WEIBO_MOBILE_BASE}/u/{uid}",
        "MWeibo-Pwa": "1",
        "X-Requested-With": "XMLHttpRequest",
    }
    if cookie:
        headers["Cookie"] = cookie
    return headers


def get_weibo_web_headers(cookie: str | None = None, uid: str = WEIBO_UID) -> dict:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Referer": f"{WEIBO_WEB_BASE}/u/{uid}",
        "X-Requested-With": "XMLHttpRequest",
    }
    if cookie:
        headers["Cookie"] = cookie
    return headers


async def fetch_weibo_cards(cookie: str | None = None, uid: str = WEIBO_UID) -> list[dict]:
    params = urlencode({"type": "uid", "value": uid, "containerid": f"107603{uid}"})
    url = f"{WEIBO_API_BASE}?{params}"
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout, headers=get_weibo_headers(cookie, uid)) as session:
        async with session.get(url) as response:
            if response.status != 200:
                logger.warning(f"微博接口请求失败，状态码：{response.status}")
                return []
            try:
                payload = await response.json(content_type=None)
            except Exception as exc:
                logger.warning(f"微博接口 JSON 解析失败: {exc}")
                return []

    if not isinstance(payload, dict) or payload.get("ok") != 1:
        logger.warning("微博接口返回状态异常")
        return []
    cards = payload.get("data", {}).get("cards")
    return cards if isinstance(cards, list) else []


async def fetch_weibo_web_statuses(cookie: str | None = None, uid: str = WEIBO_UID) -> list[dict]:
    params = urlencode({"uid": uid, "page": 1, "feature": 0})
    url = f"{WEIBO_WEB_TIMELINE_API}?{params}"
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout, headers=get_weibo_web_headers(cookie, uid)) as session:
        async with session.get(url) as response:
            if response.status != 200:
                logger.warning(f"微博网页端接口请求失败，状态码：{response.status}")
                return []
            try:
                payload = await response.json(content_type=None)
            except Exception as exc:
                logger.warning(f"微博网页端接口 JSON 解析失败: {exc}")
                return []

    if not isinstance(payload, dict) or payload.get("ok") != 1:
        logger.warning("微博网页端接口返回状态异常")
        return []
    data = payload.get("data", {})
    if not isinstance(data, dict):
        return []
    statuses = data.get("list") or data.get("statuses")
    return statuses if isinstance(statuses, list) else []


def extract_valid_weibo_mblogs(cards: list[dict]) -> list[dict]:
    result = []
    for card in cards:
        if not isinstance(card, dict) or card.get("card_type") != 9:
            continue
        mblog = card.get("mblog")
        if not isinstance(mblog, dict):
            continue
        if is_pinned_weibo_card(card, mblog):
            continue
        if not mblog.get("bid"):
            continue
        result.append(mblog)
    return result


def extract_valid_weibo_web_statuses(statuses: list[dict]) -> list[dict]:
    result = []
    for status in statuses:
        if not isinstance(status, dict):
            continue
        title = status.get("title")
        title_text = title.get("text") if isinstance(title, dict) else ""
        if any([status.get("isTop"), status.get("is_top"), status.get("top"), title_text == "置顶"]):
            continue
        if not (status.get("mblogid") or status.get("bid")):
            continue
        result.append(status)
    return result


def format_weibo_time(value: str) -> str:
    if not value:
        return "未知时间"
    try:
        parsed = parsedate_to_datetime(value)
        return f"{parsed.year}/{parsed.month}/{parsed.day} {parsed:%H:%M:%S}"
    except (TypeError, ValueError, IndexError):
        return value


def format_weibo_status(index: int, status: dict, uid: str = WEIBO_UID) -> str:
    bid = str(status.get("bid") or status.get("mblogid"))
    title = clean_weibo_title(str(status.get("text_raw") or status.get("text") or ""))
    created_at = format_weibo_time(str(status.get("created_at") or ""))
    weibo_url = f"{WEIBO_WEB_BASE}/{uid}/{bid}"
    return f"【{index}】{title} {created_at}\n{weibo_url}"


async def get_ff_weibo_text(cookie: str | None = None, limit: int = 5) -> str:
    cards = await fetch_weibo_cards(cookie)
    statuses = []
    for mblog in extract_valid_weibo_mblogs(cards):
        statuses.append(mblog)
        if len(statuses) >= limit:
            break

    if len(statuses) < limit and cookie:
        web_statuses = await fetch_weibo_web_statuses(cookie)
        seen_ids = {str(item.get("bid") or item.get("mblogid")) for item in statuses}
        for status in extract_valid_weibo_web_statuses(web_statuses):
            status_id = str(status.get("bid") or status.get("mblogid"))
            if status_id in seen_ids:
                continue
            statuses.append(status)
            seen_ids.add(status_id)
            if len(statuses) >= limit:
                break

    if not statuses:
        return "没有获取到最新微博，可能是微博接口结构变化或需要配置微博 Cookie。"
    return "\n".join(format_weibo_status(index, item) for index, item in enumerate(statuses[:limit], start=1))


def find_bili_url_in_text(text: str) -> str | None:
    normalized = html.unescape(text)
    normalized = normalized.replace("\\/", "/")
    normalized = normalized.replace("\\u002F", "/").replace("\\u002f", "/")
    match = re.search(
        r"https?://(?:www\.)?bilibili\.com/video/(?:BV[0-9A-Za-z]+|av\d+)[^'\"\\\s<>]*",
        normalized,
    )
    if not match:
        return None
    return match.group(0).rstrip("),，。；;]")


def find_bili_url_in_obj(value) -> str | None:
    if isinstance(value, str):
        return find_bili_url_in_text(value)
    if isinstance(value, dict):
        for item in value.values():
            result = find_bili_url_in_obj(item)
            if result:
                return result
    if isinstance(value, list):
        for item in value:
            result = find_bili_url_in_obj(item)
            if result:
                return result
    return None


def get_current_period() -> int:
    base = datetime(2018, 10, 16, 16, 0, 0)
    current = datetime.now()
    if current < base:
        raise ValueError("当前系统时间早于2018年10月16日，请修正系统时间")
    return (current - base).days // 7 + 37


async def get_bili_url() -> str:
    table_id = "DY2lCeEpwemZESm5q"
    sheet_id = "dewveu"
    headers = {
        "referer": f"https://docs.qq.com/sheet/{table_id}?tab={sheet_id}",
        "authority": "docs.qq.com",
        "accept": "*/*",
    }
    docs_url = (
        "https://docs.qq.com/dop-api/opendoc?"
        f"tab={sheet_id}&id={table_id}&outformat=1&normal=1"
    )
    docs_json = await aiohttp_get(docs_url, headers=headers)
    if docs_json:
        result = find_bili_url_in_obj(docs_json)
        if result:
            logger.info(f"从腾讯文档接口获取暖暖视频链接: {result}")
            return result

    docs_text = await aiohttp_get(docs_url, res_type="text", headers=headers)
    if docs_text:
        result = find_bili_url_in_text(docs_text)
        if result:
            logger.info(f"从腾讯文档文本获取暖暖视频链接: {result}")
            return result

    docs_page = await aiohttp_get(QQ_DOC_URL, res_type="text", headers=headers)
    if docs_page:
        result = find_bili_url_in_text(docs_page)
        if result:
            logger.info(f"从腾讯文档页面获取暖暖视频链接: {result}")
            return result

    period = get_current_period()
    prefix = f"【FF14/时尚品鉴】第{period}期"

    search_url = (
        "https://api.bilibili.com/x/web-interface/search/type?"
        f"search_type=video&keyword={quote(prefix)}&page=1"
    )
    search_data = await aiohttp_get(search_url, headers={"referer": "https://search.bilibili.com/"})
    if search_data and search_data.get("code") == 0:
        videos = search_data.get("data", {}).get("result", [])
        for video in videos:
            title = re.sub(r"<.*?>", "", str(video.get("title", "")))
            author = str(video.get("author", ""))
            bvid = video.get("bvid")
            if title.startswith(prefix) and bvid and ("游玩C哩酱" in author or not author):
                result = f"https://www.bilibili.com/video/{bvid}"
                logger.info(f"从bilibili搜索获取暖暖视频链接: {result}")
                return result
    elif search_data:
        logger.warning(f"bilibili搜索接口返回异常: code={search_data.get('code')} message={search_data.get('message')}")

    api_url = f"https://api.bilibili.com/x/space/arc/search?mid={BILI_USER_ID}&ps=10&pn=1"
    data = await aiohttp_get(api_url, headers={"referer": f"https://space.bilibili.com/{BILI_USER_ID}"})
    if data and data.get("code") == 0:
        videos = data.get("data", {}).get("list", {}).get("vlist", [])
        for video in videos:
            if str(video.get("title", "")).startswith(prefix):
                result = f"https://www.bilibili.com/video/{video['bvid']}"
                logger.info(f"从bilibili空间接口获取暖暖视频链接: {result}")
                return result
    elif data:
        logger.warning(f"bilibili空间接口返回异常: code={data.get('code')} message={data.get('message')}")

    raise ValueError("找不到最新一期bilibili视频链接")


async def get_bili_detail(bili_url: str) -> str:
    page = await aiohttp_get(bili_url, res_type="text", headers={"referer": "https://www.bilibili.com/"})
    if not page:
        raise ValueError("获取bilibili页面失败")

    match = re.search(r'<span class="desc-info-text".*?</span>', page, flags=re.S)
    if match:
        result = match.group(0).split("\n", 1)[-1].replace("</span>", "")
        return html.unescape(re.sub(r"<.*?>", "", result)).strip()

    json_match = re.search(r'"desc"\s*:\s*"((?:\\.|[^"\\])*)"', page)
    if json_match:
        return html.unescape(json.loads(f'"{json_match.group(1)}"')).strip()

    raise ValueError("解析bilibili视频简介失败")


async def fetch_dungeon_notes() -> dict[str, dict[str, str]]:
    page = await aiohttp_get(DUNGEON_NOTE_URL, res_type="text")
    if not page:
        raise ValueError("获取攻略列表失败")

    note_dict: dict[str, dict[str, str]] = {}
    matches = re.findall(r'/duty/.*?</a>', page, flags=re.S)
    for line in matches[:-3]:
        try:
            page_id = line.split(".htm", 1)[0].replace("/duty/", "")
            dungeon_level = line.split("[", 1)[1].split("]", 1)[0]
            dungeon_name = line.split("] ", 1)[1].split("\n", 1)[0]
        except IndexError:
            continue
        note_dict.setdefault(dungeon_level, {})[html.unescape(dungeon_name)] = page_id
    return note_dict


async def get_dungeon_note(dungeon_info: str) -> tuple[str, bool]:
    dungeon_level, dungeon_name, is_text = parse_dungeon_query(dungeon_info)
    if not dungeon_name:
        return "查攻略格式：攻略 (副本等级) 副本名关键字 (文本)。括号内为可选参数，默认输出图片攻略。", True

    note_dict = await fetch_dungeon_notes()
    page_matches = []
    for level_info, dungeon_items in note_dict.items():
        for name, page_id in dungeon_items.items():
            if dungeon_name in name:
                page_matches.append([level_info, name, page_id])

    if not page_matches:
        return "副本名没搜到鸭", True

    if len(page_matches) > 1 and dungeon_level:
        filtered_matches = [item for item in page_matches if dungeon_level == item[0]]
        if filtered_matches:
            page_matches = filtered_matches

    if len(page_matches) > 1:
        result = "是哪个副本呢？重新告诉我哦~\n"
        for page_match in page_matches:
            result += page_match[0] + " " + page_match[1] + "、"
        return result[:-1], True

    detail_page = await aiohttp_get(f"{DUNGEON_NOTE_URL}/{page_matches[0][-1]}.htm", res_type="text")
    if not detail_page:
        return "攻略详情获取失败，请稍后再试", True

    blocks = re.findall(r"<p>.*?</p>|<h\d.*?</h\d>", detail_page, flags=re.S)
    result_text = ""
    for block in blocks:
        stripped = strip_html(block)
        if stripped:
            result_text += stripped + "\n"

    if not result_text.strip():
        return "攻略详情为空，请稍后再试", True
    return result_text, is_text


def garland_url(item_category: str, item_id: str | int) -> str:
    return f"{GARLAND_BASE_URL}/db/doc/{item_category}/chs/3/{item_id}.json"


def strip_xiv_tags(text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    return re.sub(r"<.*?>", "", text).strip()


async def garland_core_value(path: str):
    global GARLAND_CORE_DATA
    if GARLAND_CORE_DATA is None:
        GARLAND_CORE_DATA = await aiohttp_get(garland_url("core", "data"))
    value = GARLAND_CORE_DATA
    for part in path.split("."):
        value = value[part]
    return value


def garland_partials(payload: dict) -> dict[tuple[str, str], dict]:
    result = {}
    for partial in payload.get("partials", []):
        result[(str(partial.get("type")), str(partial.get("id")))] = partial.get("obj", {})
    return result


async def search_xivapi_item_id(name: str) -> tuple[int | None, str | None]:
    query = f'Name~"{name}"'
    params = urlencode(
        {
            "query": query,
            "sheets": "Item",
            "fields": "Name",
            "language": "chs",
            "limit": 8,
        }
    )
    payload = await aiohttp_get(f"{XIVAPI_BASE_URL}/search?{params}")
    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, list):
        return None, None

    candidates = []
    for row in results:
        if not isinstance(row, dict):
            continue
        row_id = row.get("row_id")
        item_name = xivapi_field_text(row, "Name")
        if not row_id or not item_name:
            continue
        candidates.append((int(row_id), item_name))

    if not candidates:
        return None, None
    for row_id, item_name in candidates:
        if item_name == name:
            return row_id, item_name
    return candidates[0]


async def download_garland_item_icon(item: dict, output_path: Path) -> bool:
    icon = item.get("icon")
    if not icon:
        return False
    icon_path = str(icon)
    if not icon_path.startswith("t/"):
        icon_path = "t/" + icon_path
    image = await aiohttp_get(
        f"{GARLAND_BASE_URL}/files/icons/item/{icon_path}.png",
        res_type="bytes",
    )
    if not image:
        return False
    output_path.write_bytes(image)
    return True


def format_garland_node(node: dict) -> str:
    node_type = NODE_NAME_BY_TYPE.get(int(node.get("t", 0)), "采集点")
    coord = node.get("c") or []
    coord_text = f"({coord[0]}, {coord[1]})" if len(coord) >= 2 else ""
    time_text = ""
    if node.get("ti"):
        time_text = " ET " + " ".join(f"{item}时" for item in node["ti"])
    return f"{node.get('n', '')} {node.get('l', '')}级{node_type} {coord_text}{time_text}".strip()


async def parse_item_garland(item_id: int) -> tuple[str, dict]:
    payload = await aiohttp_get(garland_url("item", item_id))
    if not isinstance(payload, dict) or "item" not in payload:
        raise ValueError("Garland 物品详情为空")

    item = payload["item"]
    partials = garland_partials(payload)
    lines = [
        item.get("name", f"物品 {item_id}"),
        await garland_core_value(f"item.categoryIndex.{item.get('category', 0)}.name"),
        f"物品等级 {item.get('ilvl', 0)}",
    ]
    if item.get("elvl"):
        lines.append(f"装备等级 {item['elvl']}")
    if item.get("jobCategories"):
        lines.append(str(item["jobCategories"]))
    if item.get("description"):
        lines.append(strip_xiv_tags(item["description"]))

    source_count = 0
    if item.get("nodes"):
        lines.append("·采集")
        for node_id in item["nodes"][:5]:
            node = partials.get(("node", str(node_id)))
            if node:
                location_name = await garland_core_value(f"locationIndex.{node.get('z')}.name")
                lines.append(f"  -- {location_name} {format_garland_node(node)}")
                source_count += 1

    if item.get("fishingSpots"):
        lines.append("·钓鱼")
        for spot_id in item["fishingSpots"][:5]:
            spot = partials.get(("fishing", str(spot_id)))
            if spot:
                location_name = await garland_core_value(f"locationIndex.{spot.get('z')}.name")
                coord = f"({spot.get('x')}, {spot.get('y')})" if spot.get("x") is not None else ""
                lines.append(f"  -- {location_name} {spot.get('n', '')} {spot.get('l', '')}级 {coord}")
                source_count += 1

    if item.get("craft"):
        jobs = await garland_core_value("jobs")
        lines.append("·制作")
        for craft in item["craft"][:3]:
            job = jobs[craft["job"]]["name"]
            lines.append(f"  -- {job} {craft.get('lvl', '')}级")
            ingredients = []
            for ingredient in craft.get("ingredients", [])[:6]:
                if ingredient.get("id", 0) < 20:
                    continue
                ingredient_item = partials.get(("item", str(ingredient["id"])), {})
                ingredients.append(f"{ingredient_item.get('n', ingredient['id'])}*{ingredient.get('amount', 1)}")
            if ingredients:
                lines.append("     " + "、".join(ingredients))
            source_count += 1

    if item.get("vendors"):
        lines.append(f"·商店贩售 {item.get('price', 0)}金币")
        for vendor_id in item["vendors"][:5]:
            vendor = partials.get(("npc", str(vendor_id)))
            if vendor:
                location = ""
                if vendor.get("l"):
                    location = await garland_core_value(f"locationIndex.{vendor['l']}.name")
                coord = vendor.get("c") or []
                coord_text = f"({coord[0]}, {coord[1]})" if len(coord) >= 2 else ""
                lines.append(f"  -- {vendor.get('n', '')} {location} {coord_text}".strip())
                source_count += 1
        if len(item["vendors"]) > 5:
            lines.append(f"  -- 等共计{len(item['vendors'])}个商人售卖")

    trades = item.get("tradeCurrency", []) + item.get("tradeShops", [])
    if trades:
        lines.append("·兑换")
        for trade in trades[:3]:
            shop_name = "商店交易" if trade.get("shop") == "Shop" else trade.get("shop", "兑换")
            lines.append(f"  -- {shop_name}")
            for listing in trade.get("listings", [])[:2]:
                currencies = []
                for currency in listing.get("currency", [])[:3]:
                    currency_item = partials.get(("item", str(currency.get("id"))), {})
                    currencies.append(f"{currency_item.get('n', currency.get('id'))}*{currency.get('amount', 1)}")
                if currencies:
                    lines.append("     使用 " + "、".join(currencies))
            source_count += 1

    if item.get("drops"):
        lines.append("·怪物掉落")
        for mob_id in item["drops"][:5]:
            mob = partials.get(("mob", str(mob_id)))
            if mob:
                location = await garland_core_value(f"locationIndex.{mob.get('z')}.name")
                lines.append(f"  -- {mob.get('n', '')} {location}")
                source_count += 1

    if item.get("instances"):
        lines.append("·副本获取")
        for duty_id in item["instances"][:5]:
            duty = partials.get(("instance", str(duty_id)))
            if duty:
                lines.append(f"  -- {duty.get('min_lvl', '')}级 {duty.get('n', '')}")
                source_count += 1

    if item.get("quests"):
        lines.append("·任务奖励")
        for quest_id in item["quests"][:5]:
            quest = partials.get(("quest", str(quest_id)))
            if quest:
                lines.append(f"  -- {quest.get('n', '')}")
                source_count += 1

    if source_count == 0:
        lines.append("获取方式较麻烦/没查到，烦请打开网页查看！")

    status = []
    if item.get("unique"):
        status.append("独占")
    if "tradeable" in item:
        status.append("可交易" if item.get("tradeable") else "不可交易")
    if "unlistable" in item:
        status.append("不可在市场上交易" if item.get("unlistable") else "可在市场上交易")
    if item.get("storable"):
        status.append("可放入收藏柜")
    if status:
        lines.append(" ".join(status))

    lines.append(f"{GARLAND_BASE_URL}/db/#item/{item_id}")
    return "\n".join(line for line in lines if str(line).strip()), item


async def create_item_info(item_name: str, cache_dir: Path) -> tuple[str, Path | None]:
    if item_name.isdigit():
        item_id = int(item_name)
    else:
        item_id, found_name = await search_xivapi_item_id(item_name)
        if not item_id:
            return f'在最终幻想XIV中没有找到"{item_name}"', None
        if found_name and found_name != item_name:
            logger.info(f"物品搜索 {item_name} 匹配到 {found_name} ({item_id})")

    text, item = await parse_item_garland(item_id)
    icon_path = cache_dir / f"item_{item_id}.png"
    try:
        has_icon = await download_garland_item_icon(item, icon_path)
    except Exception as exc:
        logger.warning(f"物品图标下载失败: {exc}")
        has_icon = False
    return text, icon_path if has_icon else None


async def parse_market_query(query: str) -> MarketQuery:
    parts = query.split()
    scope_name = MARKET_DEFAULT_SCOPE
    scope_type = "all"
    item_parts = []
    hq = False
    limit = MARKET_DEFAULT_LISTINGS
    try:
        worlds = await load_cn_world_names()
    except Exception as exc:
        logger.warning(f"物价服务器名解析失败: {exc}")
        worlds = {}

    for part in parts:
        normalized_scope = MARKET_SCOPE_ALIASES.get(part, part)
        if part.isdigit():
            limit = max(1, min(int(part), MARKET_MAX_LISTINGS))
            continue
        if is_hq_token(part):
            hq = True
            continue
        if normalized_scope in DATA_CENTRES:
            scope_name = normalized_scope
            scope_type = "dc"
            continue
        if normalized_scope in worlds:
            scope_name = normalized_scope
            scope_type = "world"
            continue
        item_parts.append(part)

    return MarketQuery(
        scope_name=scope_name,
        scope_type=scope_type,
        item_name=" ".join(item_parts).strip() or None,
        hq=hq,
        limit=limit,
    )


async def fetch_market_listings(location: str, item_id: int, fetch_limit: int) -> tuple[dict | None, str]:
    params = urlencode({"listings": fetch_limit, "entries": 0})
    url = f"https://universalis.app/api/v2/{quote(location)}/{item_id}?{params}"
    payload = await aiohttp_get(url)
    if not isinstance(payload, dict):
        return None, location
    return payload, location


def format_market_time(timestamp_ms) -> str:
    try:
        return datetime.fromtimestamp(int(timestamp_ms) / 1000).strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError, OSError):
        return "未知"


async def create_market_text(query: MarketQuery) -> str:
    if not query.item_name:
        return "查物价格式：价格 (大区/服务器) 物品名 (HQ) (数量)\n例：价格 陆行鸟 铁矿 HQ 10"

    item_id, real_name = await search_xivapi_item_id(query.item_name)
    if not item_id:
        return f'所查询物品"{query.item_name}"不存在'

    locations = DATA_CENTRES if query.scope_type == "all" else [query.scope_name]
    fetch_limit = min(max(query.limit * (5 if query.hq else 2), 20), 100)
    results = await asyncio.gather(
        *(fetch_market_listings(location, item_id, fetch_limit) for location in locations),
        return_exceptions=True,
    )

    listings = []
    upload_times = []
    errors = []
    for result in results:
        if isinstance(result, Exception):
            errors.append(str(result))
            continue
        payload, location = result
        if not payload:
            errors.append(f"{location} 无返回")
            continue
        if payload.get("lastUploadTime"):
            upload_times.append(payload.get("lastUploadTime"))
        for listing in payload.get("listings", []):
            if query.hq and not listing.get("hq"):
                continue
            item = dict(listing)
            item["_scope"] = location
            listings.append(item)

    listings.sort(
        key=lambda item: (
            item.get("pricePerUnit") if item.get("pricePerUnit") is not None else 10**18,
            item.get("total") if item.get("total") is not None else 10**18,
        )
    )
    listings = listings[:query.limit]

    hq_label = "HQ" if query.hq else "全部"
    lines = [f"【{real_name or query.item_name} 价格】范围：{query.scope_name}  品质：{hq_label}  数量：{len(listings)}"]
    if not listings:
        lines.append("未查询到数据，可能是物品不可交易、暂时无人上架或 Universalis 暂时不可用。")
        if errors:
            lines.append("接口错误：" + "；".join(errors[:3]))
        return "\n".join(lines)

    for index, listing in enumerate(listings, start=1):
        price = listing.get("pricePerUnit", 0)
        quantity = listing.get("quantity", 0)
        total = listing.get("total", price * quantity if price and quantity else 0)
        quality = "HQ" if listing.get("hq") else "NQ"
        world = listing.get("worldName") or listing.get("_scope", "")
        retainer = listing.get("retainerName") or "未知雇员"
        lines.append(f"{index:02d}. {price:,} x{quantity} = {total:,} {quality} @ {world} / {retainer}")

    if upload_times:
        lines.append("更新时间：" + format_market_time(max(upload_times)))
    return "\n".join(lines)


def parse_logs_query(query: str, default_cn_source: bool = True) -> LogsQuery:
    parts = query.split()
    boss_name = parts[0] if len(parts) > 0 else None
    job_name = parts[1] if len(parts) > 1 else None
    cn_source = default_cn_source
    if any(part.lower() in {"国际服", "国际", "global", "intl", "international"} for part in parts):
        cn_source = False
    if any(part.lower() in {"国服", "国", "cn", "china"} for part in parts):
        cn_source = True
    dps_type = "rdps"
    for part in parts:
        lower = part.lower()
        if lower in {"rdps", "adps", "pdps", "ndps", "cdps"}:
            dps_type = lower
            break
    day = -1
    for part in parts[2:]:
        lower = part.lower()
        if lower.startswith("day"):
            try:
                day = int(lower.replace("day", "", 1)) - 1
            except ValueError:
                day = -2
            continue
    return LogsQuery(boss_name, job_name, cn_source, dps_type, day)


def normalize_logs_lookup(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", "", str(value).strip()).casefold()


def find_logs_job(job_name: str | None) -> dict | None:
    if not job_name:
        return None
    query = normalize_logs_lookup(job_name)
    for item in load_json_list(JOB_JSON):
        aliases = item.get("nickname", [])
        names = [normalize_logs_lookup(name) for name in [item.get("name"), item.get("cn_name"), *aliases]]
        if query in names:
            return item
    return None


def find_logs_boss(boss_name: str | None) -> dict | None:
    if not boss_name:
        return None
    query = normalize_logs_lookup(boss_name)
    if not query:
        return None
    candidates: list[tuple[dict, list[str]]] = []
    for item in load_json_list(BOSS_JSON):
        aliases = item.get("nickname", [])
        names = [
            normalize_logs_lookup(name)
            for name in [item.get("name"), item.get("cn_name"), *aliases]
            if isinstance(name, str) and name.strip()
        ]
        candidates.append((item, names))
        if query in names:
            return item
    for item, names in candidates:
        if any(query in name or name in query for name in names):
            return item
    return None


def fflogs_region_entries(boss: dict, cn_source: bool) -> list[str]:
    regions = [
        region
        for region in boss.get("cn_region" if cn_source else "region", [])
        if isinstance(region, str) and "###" in region
    ]
    selected = []
    index = 0
    while index < len(regions):
        label = regions[index].split("###", 1)[0]
        group = []
        while index < len(regions) and regions[index].split("###", 1)[0] == label:
            group.append(regions[index])
            index += 1
        if len(group) >= 3:
            selected.append(group[1] if cn_source else group[0])
        elif len(group) == 2:
            selected.append(group[1] if cn_source else group[0])
        elif group:
            selected.append(group[0])
    return selected


async def get_fflogs_token(host: str, client_id: str, client_secret: str) -> str:
    timeout = aiohttp.ClientTimeout(total=20)
    auth = aiohttp.BasicAuth(client_id, client_secret)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            f"{host}/oauth/token",
            data={"grant_type": "client_credentials"},
            auth=auth,
        ) as response:
            if response.status != 200:
                raise RuntimeError(f"FFLogs token 请求失败：{response.status}")
            payload = await response.json(content_type=None)
    token = payload.get("access_token") if isinstance(payload, dict) else None
    if not token:
        raise RuntimeError("FFLogs token 响应缺少 access_token")
    return token


async def fflogs_graphql(host: str, token: str, query: str, variables: dict) -> dict:
    timeout = aiohttp.ClientTimeout(total=25)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        async with session.post(
            f"{host}/api/v2/client",
            json={"query": query, "variables": variables},
        ) as response:
            if response.status != 200:
                raise RuntimeError(f"FFLogs GraphQL 请求失败：{response.status}")
            payload = await response.json(content_type=None)
    if isinstance(payload, dict) and payload.get("errors"):
        raise RuntimeError("FFLogs GraphQL 返回错误")
    return payload if isinstance(payload, dict) else {}


async def fetch_fflogs_metadata(host: str, token: str) -> dict:
    cached = FFLOGS_METADATA_CACHE.get(host)
    if cached:
        return cached
    payload = await fflogs_graphql(host, token, FFLOGS_METADATA_QUERY, {})
    metadata = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(metadata, dict):
        raise RuntimeError("FFLogs metadata 响应为空")
    FFLOGS_METADATA_CACHE[host] = metadata
    return metadata


def fflogs_zone_by_id(metadata: dict) -> dict[int, dict]:
    zones = metadata.get("worldData", {}).get("zones", [])
    return {int(zone["id"]): zone for zone in zones if isinstance(zone, dict) and zone.get("id") is not None}


def fflogs_encounters_by_id(zone: dict | None) -> dict[int, dict]:
    if not isinstance(zone, dict):
        return {}
    encounters = zone.get("encounters", [])
    return {
        int(encounter["id"]): encounter
        for encounter in encounters
        if isinstance(encounter, dict) and encounter.get("id") is not None
    }


def fflogs_metadata_regions(zone: dict | None) -> list[str]:
    if not isinstance(zone, dict):
        return []
    partitions = [part for part in zone.get("partitions", []) if isinstance(part, dict) and part.get("id") is not None]
    selected = [
        part
        for part in partitions
        if isinstance(part.get("name"), str)
        and (
            ("Standard" in part["name"] and "Non-Standard" not in part["name"])
            or ("标准" in part["name"] and "非标准" not in part["name"])
        )
    ]
    if not selected:
        selected = [part for part in partitions if part.get("default")]
    if not selected:
        selected = partitions
    if not selected:
        return ["-1###1"]
    return [f"{part.get('name') or part['id']}###{int(part['id'])}" for part in selected]


def fflogs_metadata_difficulty(zone: dict | None) -> int:
    if not isinstance(zone, dict):
        return 100
    ids = [
        int(item["id"])
        for item in zone.get("difficulties", [])
        if isinstance(item, dict) and item.get("id") is not None
    ]
    return max(ids) if ids else 100


def build_fflogs_metadata_boss(en_zone: dict, cn_zone: dict | None, encounter_id: int) -> dict | None:
    en_encounter = fflogs_encounters_by_id(en_zone).get(encounter_id)
    if not en_encounter:
        return None
    cn_encounter = fflogs_encounters_by_id(cn_zone).get(encounter_id) if cn_zone else None
    en_name = en_encounter.get("name") or ""
    cn_name = cn_encounter.get("name") if isinstance(cn_encounter, dict) else None
    return {
        "pk": encounter_id,
        "quest": int(en_zone["id"]),
        "zone_name": en_zone.get("name") or "",
        "cn_zone_name": cn_zone.get("name") if isinstance(cn_zone, dict) else en_zone.get("name") or "",
        "name": en_name,
        "cn_name": cn_name or en_name,
        "nickname": [],
        "patch": 0,
        "savage": fflogs_metadata_difficulty(en_zone),
        "region": fflogs_metadata_regions(en_zone),
        "cn_region": fflogs_metadata_regions(cn_zone) if cn_zone else fflogs_metadata_regions(en_zone),
    }


def fflogs_metadata_boss_names(entry: dict, zone: dict | None = None) -> list[str]:
    names = [entry.get("name"), entry.get("cn_name"), *entry.get("nickname", [])]
    if isinstance(zone, dict) and len(zone.get("encounters", []) or []) == 1:
        names.append(zone.get("name"))
    return [normalize_logs_lookup(name) for name in names if isinstance(name, str) and name.strip()]


async def find_logs_boss_metadata(boss_name: str, client_id: str, client_secret: str) -> dict | None:
    if not client_id or not client_secret:
        return None
    query = normalize_logs_lookup(boss_name)
    if not query:
        return None

    metadata: dict[bool, dict] = {}
    for cn_source, host in FFLOGS_HOSTS.items():
        token = await get_fflogs_token(host, client_id, client_secret)
        metadata[cn_source] = await fetch_fflogs_metadata(host, token)

    en_zones = fflogs_zone_by_id(metadata[False])
    cn_zones = fflogs_zone_by_id(metadata[True])
    candidates: list[tuple[dict, list[str]]] = []
    for zone_id, en_zone in en_zones.items():
        cn_zone = cn_zones.get(zone_id)
        encounter_ids = set(fflogs_encounters_by_id(en_zone))
        encounter_ids.update(fflogs_encounters_by_id(cn_zone))
        for encounter_id in encounter_ids:
            entry = build_fflogs_metadata_boss(en_zone, cn_zone, encounter_id)
            if not entry:
                continue
            names = fflogs_metadata_boss_names(entry, en_zone)
            candidates.append((entry, names))
            if query in names:
                return entry
    for entry, names in candidates:
        if any(query in name or name in query for name in names):
            return entry
    return None


def normalize_fflogs_result(
    stat: dict,
    query: LogsQuery,
    boss: dict,
    job: dict,
    region_info: str,
    source_label: str,
) -> str:
    period_label = "日期范围" if stat.get("date_range") else "天数"
    period_value = stat.get("date_range", stat.get("day", "最新"))
    lines = [
        f"服务器: {'国服' if query.cn_source else '国际服'}  dps类型: {query.dps_type}",
        f"数据源: {source_label}",
        f"版本: {region_info}",
        f"副本: {boss['cn_zone_name']}",
        f"boss: {boss['cn_name']}",
        f"职业: {job['cn_name']}  {period_label}: {period_value}",
    ]
    if stat.get("parses"):
        lines.append(f"记录数: {stat['parses']}")
    lines.extend(f"{percentile}%: {stat[str(percentile)]:.2f}" for percentile in FFLOGS_PERCENTILES)
    return "\n".join(lines)


def parse_fflogs_number(value: str) -> float:
    return float(value.replace(",", ""))


def decode_fflogs_page_text(value: str) -> str:
    text = html.unescape(value)
    text = re.sub(r"\\u([0-9a-fA-F]{4})", lambda match: chr(int(match.group(1), 16)), text)
    return text.replace("\\/", "/")


def fflogs_text_from_html(value: str) -> str:
    text = decode_fflogs_page_text(value)
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def fflogs_number_candidates(value: str) -> list[float]:
    numbers = re.findall(r"\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?", value)
    return [parse_fflogs_number(number) for number in numbers if parse_fflogs_number(number) >= 1000]


def fflogs_decimal_candidates(value: str) -> list[float]:
    numbers = re.findall(r"\d{1,3}(?:,\d{3})*\.\d+|\d+\.\d+", value)
    return [parse_fflogs_number(number) for number in numbers if parse_fflogs_number(number) >= 1000]


def choose_fflogs_percentile_values(values: list[float]) -> list[float] | None:
    expected_count = len(FFLOGS_PERCENTILES)
    for index in range(0, len(values) - expected_count + 1):
        block = values[index : index + expected_count]
        if block[0] > block[1] and all(block[item] >= block[item + 1] for item in range(expected_count - 1)):
            return block
    return None


def parse_logs_statistics_chart_value_block(text: str, job: dict) -> dict | None:
    label_groups = [
        [f"{job.get('cn_name', '')} 最高", f"{job.get('name', '')} Max"],
        ["第99百分位数", "99th percentile", "99th Percentile"],
        ["第95百分位数", "95th percentile", "95th Percentile"],
        ["第75百分位数", "75th percentile", "75th Percentile"],
        ["第50百分位数", "50th percentile", "50th Percentile", "Median"],
        ["第25百分位数", "25th percentile", "25th Percentile"],
        ["第10百分位数", "10th percentile", "10th Percentile"],
    ]
    positions = []
    for labels in label_groups:
        match = None
        for label in labels:
            if not label.strip():
                continue
            match = re.search(re.escape(label), text, flags=re.IGNORECASE)
            if match:
                break
        if not match:
            return None
        positions.append(match.start())
    if not positions:
        return None
    start = max(0, min(positions) - 8000)
    end = min(len(text), max(positions) + 8000)
    values = choose_fflogs_percentile_values(fflogs_decimal_candidates(text[start:end]))
    if not values:
        return None
    stat = {}
    for percentile, value in zip(sorted(FFLOGS_PERCENTILES, reverse=True), values):
        stat[str(percentile)] = value
    date_match = re.search(r"[A-Z][a-z]{2}\s+\d{1,2}\s*-\s*[A-Z][a-z]{2}\s+\d{1,2}", text)
    if date_match:
        stat["date_range"] = date_match.group(0)
    return stat


def parse_logs_statistics_chart_values(page: str, job: dict) -> dict | None:
    text = decode_fflogs_page_text(page)
    block_stat = parse_logs_statistics_chart_value_block(text, job)
    if block_stat:
        return block_stat
    labels = {
        100: [f"{job.get('cn_name', '')} 最高", f"{job.get('name', '')} Max", "最高", "Max"],
        99: ["第99百分位数", "99th percentile", "99th Percentile"],
        95: ["第95百分位数", "95th percentile", "95th Percentile"],
        75: ["第75百分位数", "75th percentile", "75th Percentile"],
        50: ["第50百分位数", "50th percentile", "50th Percentile", "Median"],
        25: ["第25百分位数", "25th percentile", "25th Percentile"],
        10: ["第10百分位数", "10th percentile", "10th Percentile"],
    }
    stat = {}
    for percentile, names in labels.items():
        for label in names:
            if not label.strip():
                continue
            for match in re.finditer(re.escape(label), text, flags=re.IGNORECASE):
                section = text[match.end() : match.end() + 400]
                candidates = fflogs_number_candidates(section)
                if candidates:
                    stat[str(percentile)] = candidates[0]
                    break
            if str(percentile) in stat:
                break
        if str(percentile) not in stat:
            return parse_logs_statistics_chart_value_block(text, job)
    date_match = re.search(r"[A-Z][a-z]{2}\s+\d{1,2}\s*-\s*[A-Z][a-z]{2}\s+\d{1,2}", text)
    if date_match:
        stat["date_range"] = date_match.group(0)
    return stat


def parse_logs_statistics_primary_cell(page: str) -> dict | None:
    cells = re.findall(
        r"<td\b(?=[^>]*\bmain-table-number\b)(?=[^>]*\bprimary\b)[^>]*>(.*?)</td>",
        page,
        flags=re.IGNORECASE | re.DOTALL,
    )
    for cell in cells:
        text = fflogs_text_from_html(cell)
        candidates = fflogs_decimal_candidates(text)
        if candidates:
            return {"dps": candidates[0]}
    return None


def parse_logs_statistics_summary_row(page: str, job: dict) -> dict | None:
    job_names = [name for name in [job.get("cn_name"), job.get("name")] if isinstance(name, str) and name]
    rows = re.findall(r"<tr\b[^>]*>.*?</tr>", page, flags=re.IGNORECASE | re.DOTALL)
    candidates = rows if rows else [page]
    for row in candidates:
        text = fflogs_text_from_html(row)
        if not any(name in text for name in job_names):
            continue
        date_match = re.search(r"[A-Z][a-z]{2}\s+\d{1,2}\s*-\s*[A-Z][a-z]{2}\s+\d{1,2}", text)
        number_text = text[date_match.end():] if date_match else text
        numbers = re.findall(r"\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?", number_text)
        dps_candidates = [parse_fflogs_number(number) for number in numbers if "." in number and parse_fflogs_number(number) >= 1000]
        if not dps_candidates:
            continue
        result = {
            "dps": dps_candidates[0],
            "date_range": date_match.group(0) if date_match else None,
        }
        if len(dps_candidates) > 1:
            result["max"] = dps_candidates[1]
        parse_candidates = [int(number.replace(",", "")) for number in numbers if "." not in number]
        if parse_candidates:
            result["parses"] = parse_candidates[-1]
        return result

    text = fflogs_text_from_html(page)
    for name in job_names:
        index = text.rfind(name)
        if index < 0:
            continue
        section = text[index : index + 800]
        date_match = re.search(r"[A-Z][a-z]{2}\s+\d{1,2}\s*-\s*[A-Z][a-z]{2}\s+\d{1,2}", section)
        number_text = section[date_match.end():] if date_match else section
        numbers = re.findall(r"\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?", number_text)
        dps_candidates = [parse_fflogs_number(number) for number in numbers if "." in number and parse_fflogs_number(number) >= 1000]
        if dps_candidates:
            return {
                "dps": dps_candidates[0],
                "date_range": date_match.group(0) if date_match else None,
            }
    return None


def parse_logs_statistics_version_label(page: str) -> str | None:
    text = fflogs_text_from_html(page)
    matches = re.findall(r"(?:标准阵容构成|Standard Comps)\s*(?:\([^)]+\))?", text)
    return matches[-1] if matches else None


def log_fflogs_statistics_page_diagnostics(page: str, job: dict) -> None:
    decoded = decode_fflogs_page_text(page)
    text = fflogs_text_from_html(page)
    markers = {
        "cn_job": bool(job.get("cn_name") and job["cn_name"] in decoded),
        "en_job": bool(job.get("name") and job["name"] in decoded),
        "date": bool(re.search(r"[A-Z][a-z]{2}\s+\d{1,2}\s*-\s*[A-Z][a-z]{2}\s+\d{1,2}", text)),
        "chart": "第99百分位数" in decoded or "99th percentile" in decoded or "99th Percentile" in decoded,
        "table_rows": bool(re.search(r"<tr\b", decoded, flags=re.IGNORECASE)),
        "data_push": "data.push" in decoded,
        "cloudflare": "Just a moment" in decoded or "Enable JavaScript and cookies" in decoded,
    }
    logger.info(f"FFLogs statistics page diagnostics: len={len(page)} markers={markers}")


async def fetch_logs_statistics_summary(query: LogsQuery, boss: dict, job: dict) -> tuple[dict, str] | None:
    host = FFLOGS_HOSTS[query.cn_source]
    stat = {}
    date_range = None
    parses = None
    version_label = None
    sorted_percentiles = sorted(FFLOGS_PERCENTILES, reverse=True)
    for index, percentile in enumerate(sorted_percentiles):
        params = {
            "boss": str(boss["pk"]),
            "class": "Global",
            "spec": job["name"],
            "dataset": str(percentile),
        }
        if query.dps_type != "rdps":
            params["dpstype"] = query.dps_type
        url = f"{host}/zone/statistics/{boss['quest']}?{urlencode(params)}"
        logger.info(f"FFLogs statistics page URL: {url}")
        page = await aiohttp_get(url, res_type="text", headers={"Referer": host})
        if not isinstance(page, str):
            return None
        if index == 0:
            chart_stat = parse_logs_statistics_chart_values(page, job)
            if chart_stat:
                logger.info("FFLogs statistics chart values matched")
                version_label = parse_logs_statistics_version_label(page)
                return chart_stat, version_label or "网页默认"
        parsed = parse_logs_statistics_primary_cell(page)
        if parsed:
            logger.info("FFLogs statistics primary table cell matched")
        else:
            parsed = parse_logs_statistics_summary_row(page, job)
        if not parsed:
            log_fflogs_statistics_page_diagnostics(page, job)
            return None
        stat[str(percentile)] = parsed["dps"]
        date_range = date_range or parsed.get("date_range")
        parses = parses or parsed.get("parses")
        version_label = version_label or parse_logs_statistics_version_label(page)
    if any(str(percentile) not in stat for percentile in FFLOGS_PERCENTILES):
        return None
    if date_range:
        stat["date_range"] = date_range
    if parses:
        stat["parses"] = parses
    return stat, version_label or "网页默认"


async def fetch_logs_statistics_page(query: LogsQuery, boss: dict, job: dict) -> tuple[str, str] | None:
    regions = fflogs_region_entries(boss, query.cn_source)
    if not regions:
        return None
    host = FFLOGS_HOSTS[query.cn_source]
    search_range = [regions[-index - 1] for index in range(len(regions))]
    for region_entry in search_range:
        region_info, region_id = region_entry.split("###", 1)
        params = {}
        if query.dps_type != "rdps":
            params["dpstype"] = query.dps_type
        for aggregate in FFLOGS_STAT_AGGREGATES:
            query_string = f"?{urlencode(params)}" if params else ""
            url = (
                f"{host}/zone/statistics/table/"
                f"{boss['quest']}/dps/{boss['pk']}/{boss['savage']}/8/{int(region_id)}/100/1000/7/"
                f"{boss['patch']}/Global/{job['name']}/All/0/{aggregate}/single/0/-1/"
                f"{query_string}"
            )
            logger.info(f"FFLogs statistics table URL: {url}")
            page = await aiohttp_get(url, res_type="text", headers={"Referer": host})
            if isinstance(page, str) and "data.push" in page:
                logger.info(f"FFLogs statistics aggregate matched: {aggregate}")
                return page, f"{region_info} / {aggregate}"
    return None


def parse_logs_statistics_page(page: str) -> list[dict]:
    statistics = {}
    for percentile in FFLOGS_PERCENTILES:
        series_name = "" if percentile == 100 else str(percentile)
        pattern = rf"series{series_name}\.data\.push\(([+-]?(?:0|[1-9]\d*)(?:\.\d+)?)\)"
        statistics[str(percentile)] = [float(value) for value in re.findall(pattern, page)]
    total_length = len(statistics["100"])
    if not total_length or any(len(statistics[str(percentile)]) != total_length for percentile in FFLOGS_PERCENTILES):
        return []

    def all_zero(index: int) -> bool:
        return sum(statistics[str(percentile)][index] for percentile in FFLOGS_PERCENTILES) == 0

    left = 0
    right = total_length - 1
    while left < total_length and all_zero(left):
        left += 1
    while right >= 0 and all_zero(right):
        right -= 1
    if left > right:
        return []

    rows = []
    for index in range(left, right + 1):
        item = {"day": len(rows) + 1}
        for percentile in FFLOGS_PERCENTILES:
            item[str(percentile)] = statistics[str(percentile)][index]
        rows.append(item)
    return rows


async def create_logs_text_crawl(query: LogsQuery, boss: dict, job: dict) -> str:
    if query.day == -1:
        summary_result = await fetch_logs_statistics_summary(query, boss, job)
        if summary_result:
            stat, region_info = summary_result
            return normalize_fflogs_result(stat, query, boss, job, region_info, "FFLogs statistics page")

    result = await fetch_logs_statistics_page(query, boss, job)
    if not result:
        return "查不到数据，怎么回事呢？"
    page, region_info = result
    rows = parse_logs_statistics_page(page)
    if not rows:
        return "No data found"
    row = rows[-1] if query.day == -1 or query.day >= len(rows) else rows[query.day]
    return normalize_fflogs_result(row, query, boss, job, region_info, "FFLogs statistics table")


async def create_logs_text(query: LogsQuery, client_id: str, client_secret: str) -> str:
    if not query.boss_name or not query.job_name:
        return "查logs格式：输出 boss名 职业名 (国服) (rdps) (day2)\n例：输出 海德林 武士"
    if query.day == -2:
        return "day格式不对，例如：day2"
    job = find_logs_job(query.job_name)
    if not job:
        return "检查职业名称是否正确"
    boss = find_logs_boss(query.boss_name)
    if not boss:
        try:
            boss = await find_logs_boss_metadata(query.boss_name, client_id, client_secret)
        except Exception as exc:
            logger.info(f"FFLogs metadata 动态查找失败: {exc}")
    if not boss:
        return "检查boss名称是否正确"

    return await create_logs_text_crawl(query, boss, job)


def party_optional_text(value) -> str:
    if value is None:
        return ""
    return html.unescape(str(value)).strip()


def format_party_time_left(seconds_value) -> str:
    try:
        seconds = int(float(seconds_value))
    except (TypeError, ValueError):
        return ""

    if seconds <= 0:
        return "已过期"
    minutes = max(1, seconds // 60)
    if minutes < 60:
        return f"剩余 {minutes} 分"
    hours = minutes // 60
    rest_minutes = minutes % 60
    if rest_minutes:
        return f"剩余 {hours} 小时 {rest_minutes} 分"
    return f"剩余 {hours} 小时"


def format_party_updated_at(updated_at: str) -> str:
    if not updated_at:
        return ""
    try:
        updated_time = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        now = datetime.now(updated_time.tzinfo)
        seconds = int((now - updated_time).total_seconds())
    except ValueError:
        return f"更新 {updated_at}"

    if seconds < 60:
        return "刚刚更新"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} 分钟前更新"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} 小时前更新"
    return f"{hours // 24} 天前更新"


def format_party_finder_api_entry(index: int, listing: dict) -> str:
    category_now = party_optional_text(listing.get("category"))
    if not category_now and listing.get("category_id") is not None:
        category_label = PARTY_CATEGORY_ID_LABELS.get(int(listing["category_id"]), f"分类ID {listing['category_id']}")
    else:
        category_label = PARTY_CATEGORY_LABELS.get(category_now, category_now or "未知分类")
    duty_now = party_optional_text(listing.get("duty")) or "无"
    description_now = party_optional_text(listing.get("description")) or "无描述"
    creator_now = party_optional_text(listing.get("name") or listing.get("player_name")) or "未知"
    world_now = party_optional_text(listing.get("created_world") or listing.get("home_world"))
    if not world_now:
        world_id = listing.get("created_world_id") or listing.get("home_world_id")
        world_now = f"世界ID {world_id}" if world_id else "未知世界"

    filled = listing.get("slots_filled")
    available = listing.get("slots_available")
    total_now = ""
    if filled is not None and available is not None:
        try:
            total_now = f"{filled}/{int(filled) + int(available)}"
        except (TypeError, ValueError):
            total_now = f"{filled}/{available}"

    item_level = listing.get("min_item_level")
    item_level_text = f"IL {item_level}" if item_level else ""
    time_left = format_party_time_left(listing.get("time_left") or listing.get("time_left_seconds"))
    updated_text = format_party_updated_at(party_optional_text(listing.get("updated_at")))
    meta_parts = [f"{creator_now} @ {world_now}", total_now, item_level_text, time_left, updated_text]
    meta_text = " | ".join(part for part in meta_parts if part)

    text_now = f"{index:02d}. [{category_label}] {duty_now}\n"
    text_now += f"    {truncate_text(description_now, 86)}\n"
    text_now += f"    {meta_text}\n"
    return text_now


def xivapi_field_text(row: dict | None, *path: str) -> str:
    current = row.get("fields", {}) if isinstance(row, dict) else {}
    for part in path:
        if not isinstance(current, dict):
            return ""
        current = current.get(part)
        if isinstance(current, dict) and "fields" in current:
            current = current["fields"]
    return party_optional_text(current)


async def get_xivapi_sheet_rows(sheet: str, row_ids: set[int], fields: str) -> dict[int, dict]:
    ids = sorted(row_id for row_id in row_ids if row_id)
    if not ids:
        return {}

    params = urlencode(
        {
            "rows": ",".join(str(row_id) for row_id in ids),
            "fields": fields,
            "language": "chs",
        }
    )
    payload = await aiohttp_get(f"{XIVAPI_BASE_URL}/sheet/{sheet}?{params}")
    if not isinstance(payload, dict):
        return {}

    rows = payload.get("rows")
    if not isinstance(rows, list):
        return {}
    return {int(row["row_id"]): row for row in rows if isinstance(row, dict) and row.get("row_id") is not None}


async def load_cn_world_names() -> dict[str, dict]:
    global CN_WORLD_NAME_CACHE
    if CN_WORLD_NAME_CACHE is not None:
        return CN_WORLD_NAME_CACHE

    worlds = {}
    after = None
    seen_after = set()
    while True:
        query = {
            "fields": "Name,DataCenter.Name",
            "language": "chs",
            "limit": 500,
        }
        if after is not None:
            query["after"] = after
        payload = await aiohttp_get(f"{XIVAPI_BASE_URL}/sheet/World?{urlencode(query)}")
        rows = payload.get("rows") if isinstance(payload, dict) else None
        if not isinstance(rows, list) or not rows:
            break

        for row in rows:
            if not isinstance(row, dict):
                continue
            row_id = row.get("row_id")
            name = xivapi_field_text(row, "Name")
            data_centre = xivapi_field_text(row, "DataCenter", "Name")
            if row_id and row_id >= 1000 and name and data_centre in CN_WORLD_DATA_CENTRES:
                worlds[name] = {"id": int(row_id), "data_centre": data_centre, "name": name}

        last_row_id = rows[-1].get("row_id")
        if not last_row_id or last_row_id in seen_after:
            break
        seen_after.add(last_row_id)
        if last_row_id >= 65535:
            break
        after = last_row_id

    CN_WORLD_NAME_CACHE = worlds
    return worlds


async def resolve_party_world(search_terms: list[str]) -> tuple[dict | None, list[str]]:
    if not search_terms:
        return None, search_terms
    worlds = await load_cn_world_names()
    for index, term in enumerate(search_terms):
        world = worlds.get(term)
        if world:
            remain_terms = search_terms[:index] + search_terms[index + 1:]
            return world, remain_terms
    return None, search_terms


def parse_house_number(value: str) -> int | None:
    value = value.strip()
    if value.isdigit():
        return int(value)
    chinese_digits = {
        "零": 0,
        "一": 1,
        "二": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
    }
    if not value:
        return None
    if value == "十":
        return 10
    if "十" in value:
        left, right = value.split("十", 1)
        tens = chinese_digits.get(left, 1 if left == "" else None)
        ones = chinese_digits.get(right, 0 if right == "" else None)
        if tens is None or ones is None:
            return None
        return tens * 10 + ones
    return chinese_digits.get(value)


def normalize_house_area_name(value: str | None) -> str | None:
    if not value:
        return None
    return HOUSE_AREA_ALIASES.get(value, value if value in HOUSE_AREA_NAMES else None)


def parse_house_area_token(token: str) -> tuple[str | None, str]:
    area_labels = sorted(set(HOUSE_AREA_NAMES) | set(HOUSE_AREA_ALIASES), key=len, reverse=True)
    for label in area_labels:
        if token.startswith(label):
            return normalize_house_area_name(label), token[len(label):]
    return None, token


def parse_house_query(query: str) -> HouseQuery:
    parts = query.split()
    server_name = parts[0] if parts else None
    area_name = None
    size_name = None
    ward = None
    plot_id = None
    limit = HOUSE_DEFAULT_LISTINGS

    for raw_part in parts[1:]:
        part = raw_part.strip().upper()
        if not part:
            continue
        if part in HOUSE_SIZE_NAMES:
            size_name = part
            continue
        if part.isdigit():
            limit = max(1, min(int(part), HOUSE_MAX_LISTINGS))
            continue

        area_from_token, rest = parse_house_area_token(raw_part.strip())
        if area_from_token:
            area_name = area_from_token
            if not rest:
                continue
        else:
            rest = raw_part.strip()

        ward_match = re.search(r"([0-9]+|[一二三四五六七八九十]+)区", rest)
        if ward_match:
            ward = parse_house_number(ward_match.group(1))

        plot_match = re.search(r"([0-9]+|[一二三四五六七八九十]+)号", rest)
        if plot_match:
            plot_id = parse_house_number(plot_match.group(1))

        normalized_area = normalize_house_area_name(raw_part.strip())
        if normalized_area:
            area_name = normalized_area

    return HouseQuery(
        server_name=server_name,
        area_name=area_name,
        size_name=size_name,
        ward=ward,
        plot_id=plot_id,
        limit=limit,
    )


async def resolve_house_server_id(server_name: str) -> int | None:
    if server_name in HOUSE_SERVER_IDS:
        return HOUSE_SERVER_IDS[server_name]

    try:
        worlds = await load_cn_world_names()
    except Exception as exc:
        logger.warning(f"房屋服务器名解析失败: {exc}")
        return None

    world = worlds.get(server_name)
    if world:
        return int(world["id"])
    return None


def format_house_time(timestamp_value) -> str:
    try:
        timestamp = int(timestamp_value)
    except (TypeError, ValueError):
        return "未知"
    if timestamp <= 0:
        return "未知"
    try:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
    except (OSError, ValueError):
        return "未知"


async def fetch_house_sales(server_id: int) -> list[dict] | None:
    query = urlencode({"server": server_id, "ts": int(datetime.now().timestamp())})
    payload = await aiohttp_get(f"{HOUSE_API_URL}?{query}")
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return None


async def create_house_text(query: HouseQuery) -> str:
    if not query.server_name:
        return (
            "看空房格式：房子 服务器名 (主城/房区/房号) (房子大小) (数量)\n"
            f"主城名：{'、'.join(HOUSE_AREA_NAMES)}\n"
            f"房子大小：{'、'.join(HOUSE_SIZE_NAMES)}\n"
            f"默认返回前 {HOUSE_DEFAULT_LISTINGS} 条，最多 {HOUSE_MAX_LISTINGS} 条\n"
            "例：房子 银泪湖 森都 S\n"
            "例：房子 银泪湖 森都一区\n"
            "例：房子 银泪湖 森都一区5号\n"
            "例：房子 银泪湖 森都 5号"
        )
    if query.plot_id is not None and not query.area_name:
        return "房号筛选需要带主城区域，例如：房子 银泪湖 森都5号 或 房子 银泪湖 森都一区5号"
    if query.ward is not None and not query.area_name:
        return "房区筛选需要带主城区域，例如：房子 银泪湖 森都一区"

    server_id = await resolve_house_server_id(query.server_name)
    if not server_id:
        return "检查一下服务器名称呀：\n" + "、".join(HOUSE_SERVER_IDS)

    sales = await fetch_house_sales(server_id)
    if sales is None:
        return "房屋数据获取失败，请稍后再试"

    matched = sales
    filters = []
    if query.area_name:
        area_index = HOUSE_AREA_NAMES.index(query.area_name)
        matched = [item for item in matched if item.get("Area") == area_index]
        filters.append(query.area_name)
    if query.ward is not None:
        matched = [item for item in matched if int(item.get("Slot") or 0) + 1 == query.ward]
        filters.append(f"{query.ward}区")
    if query.plot_id is not None:
        matched = [item for item in matched if int(item.get("ID") or 0) == query.plot_id]
        filters.append(f"{query.plot_id}号")
    if query.size_name:
        size_index = HOUSE_SIZE_NAMES.index(query.size_name)
        matched = [item for item in matched if item.get("Size") == size_index]
        filters.append(query.size_name)
    matched.sort(key=lambda item: (int(item.get("Slot") or 0), int(item.get("ID") or 0)))

    filter_text = " ".join(filters) if filters else "全部"
    total = len(matched)
    shown = matched[:query.limit]
    title = f"【{query.server_name}空房】筛选：{filter_text}  数量：{total}"
    if not matched:
        return title + "\n没空房子了"

    lines = [title, "────────────────────────"]
    if total > len(shown):
        lines.append(f"仅显示前 {len(shown)} 条，可在命令末尾添加数量，最多 {HOUSE_MAX_LISTINGS} 条。")
    for index, item in enumerate(shown, start=1):
        area_name = HOUSE_AREA_NAMES[int(item.get("Area") or 0)]
        size_name = HOUSE_SIZE_NAMES[int(item.get("Size") or 0)]
        slot = int(item.get("Slot") or 0) + 1
        plot_id = int(item.get("ID") or 0)
        price = int(item.get("Price") or 0)
        purchase_type = HOUSE_PURCHASE_TYPES.get(int(item.get("PurchaseType") or 0), "未知")
        region_type = HOUSE_REGION_TYPES.get(int(item.get("RegionType") or 0), "未知")
        last_seen = format_house_time(item.get("LastSeen"))
        lines.append(
            f"{index:02d}. {area_name}{slot}区 {plot_id}号 {size_name} "
            f"| {price // 10000}万 | {purchase_type} | {region_type} | 更新 {last_seen}"
        )
    return "\n".join(lines)


async def enrich_party_finder_v2_listings(listings: list[dict]) -> list[dict]:
    world_ids = set()
    duty_ids = set()
    for listing in listings:
        for key in ("created_world_id", "home_world_id"):
            try:
                world_ids.add(int(listing.get(key) or 0))
            except (TypeError, ValueError):
                pass
        try:
            duty_ids.add(int(listing.get("duty_id") or 0))
        except (TypeError, ValueError):
            pass

    world_rows, duty_rows = await asyncio.gather(
        get_xivapi_sheet_rows("World", world_ids, "Name,DataCenter.Name"),
        get_xivapi_sheet_rows("ContentFinderCondition", duty_ids, "Name,ContentType.Name"),
    )

    enriched = []
    for listing in listings:
        item = dict(listing)
        created_world = world_rows.get(int(item.get("created_world_id") or 0))
        home_world = world_rows.get(int(item.get("home_world_id") or 0))
        duty = duty_rows.get(int(item.get("duty_id") or 0))

        item["created_world"] = xivapi_field_text(created_world, "Name")
        item["home_world"] = xivapi_field_text(home_world, "Name")
        item["datacenter"] = xivapi_field_text(created_world, "DataCenter", "Name")
        item["duty"] = xivapi_field_text(duty, "Name") or "无"
        enriched.append(item)
    return enriched


def party_finder_matches_search(listing: dict, search_text: str | None) -> bool:
    if not search_text:
        return True
    search_area = " ".join(
        party_optional_text(listing.get(key))
        for key in (
            "duty",
            "description",
            "name",
            "player_name",
            "created_world",
            "home_world",
            "datacenter",
        )
    ).lower()
    return search_text.lower() in search_area


def extract_party_finder_listings(payload) -> list[dict] | None:
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("listings"), list):
        return data["listings"]
    if isinstance(payload.get("listings"), list):
        return payload["listings"]
    return None


async def get_party_finder_texts_api_v1(
    data_centre: str | None = None,
    world_name: str | None = None,
    category: str | None = None,
    search_text: str | None = None,
    job_ids: list[int] | None = None,
    limit: int = 10,
) -> list[str] | None:
    params = {
        "page": 1,
        "per_page": max(1, min(limit, 100)),
    }
    if data_centre:
        params["datacenter"] = data_centre
    if world_name:
        params["world"] = world_name
    if category:
        params["category"] = category
    if search_text:
        params["search"] = search_text
    if job_ids:
        params["jobs"] = ",".join(str(job_id) for job_id in job_ids)
    payload = await aiohttp_get(f"{PARTY_FINDER_API_V1_URL}?{urlencode(params)}")
    listings = extract_party_finder_listings(payload)
    if listings is None:
        return None

    text_list = []
    for index, listing in enumerate(listings[:limit], start=1):
        if not isinstance(listing, dict):
            continue
        text_list.append(format_party_finder_api_entry(index, listing))
    return text_list


async def get_party_finder_texts_api_v2(
    data_centre: str | None = None,
    world_id: int | None = None,
    category: str | None = None,
    search_text: str | None = None,
    job_ids: list[int] | None = None,
    limit: int = 10,
) -> list[str] | None:
    fetch_limit = 100 if search_text else max(1, min(limit, 100))
    params = {
        "page": 1,
        "per_page": fetch_limit,
    }
    if data_centre:
        params["datacenter"] = data_centre
    if category:
        category_id = PARTY_CATEGORY_IDS.get(category)
        if category_id is None:
            return None
        params["category_id"] = category_id
    if job_ids:
        params["job_ids"] = ",".join(str(job_id) for job_id in job_ids)

    param_sets = []
    if world_id:
        created_world_params = dict(params)
        created_world_params["created_world_id"] = world_id
        home_world_params = dict(params)
        home_world_params["home_world_id"] = world_id
        param_sets.extend([created_world_params, home_world_params])
    else:
        param_sets.append(params)

    listings = []
    seen_ids = set()
    for param_set in param_sets:
        payload = await aiohttp_get(f"{PARTY_FINDER_API_V2_URL}?{urlencode(param_set)}")
        payload_listings = extract_party_finder_listings(payload)
        if payload_listings is None:
            return None
        for listing in payload_listings:
            if not isinstance(listing, dict):
                continue
            listing_id = listing.get("id")
            if listing_id in seen_ids:
                continue
            seen_ids.add(listing_id)
            listings.append(listing)

    if not listings:
        return None

    valid_listings = [listing for listing in listings[:fetch_limit] if isinstance(listing, dict)]
    enriched_listings = await enrich_party_finder_v2_listings(valid_listings)
    filtered_listings = [
        listing
        for listing in enriched_listings
        if party_finder_matches_search(listing, search_text)
    ][:limit]
    return [
        format_party_finder_api_entry(index, listing)
        for index, listing in enumerate(filtered_listings, start=1)
    ]


async def get_party_finder_texts_html(
    data_centre: str | None = None,
    world_name: str | None = None,
    category: str | None = None,
    search_text: str | None = None,
    job_ids: list[int] | None = None,
    limit: int = 10,
) -> list[str]:
    if job_ids:
        return []
    all_info = await aiohttp_get(PARTY_FINDER_URL, res_type="text")
    if not all_info:
        raise ValueError("获取招募板失败")

    category_list = re.findall(r'data-pf-category="(.*?)"', all_info)
    data_centre_list = re.findall(r'data-centre=".*?"', all_info)
    duty_list = re.findall(r'<div class="duty .*?</div>', all_info)
    description_list = re.findall(r'<div class="description">.*?</div>', all_info)
    meta_list = re.findall(r'class="text">.*?</span>', all_info)
    total_list = re.findall(r'<div class="total">.*?</div>', all_info)

    text_list = []
    index_now = 1
    entry_count = min(
        len(category_list),
        len(data_centre_list),
        len(duty_list),
        len(description_list),
        len(meta_list) // 4,
        len(total_list),
    )
    for index in range(entry_count):
        if data_centre and data_centre not in data_centre_list[index]:
            continue
        category_now = html.unescape(category_list[index])
        if category and category_now != category:
            continue

        data_centre_now = data_centre_list[index].split('"')[1].replace('"', "")
        duty_now = strip_html(duty_list[index])
        description_now = description_list[index].split(">", 1)[1].replace("</div>", "")
        if "</span>" in description_now:
            description_now = description_now.split("</span>", 1)[1]
        description_now = strip_html(description_now)
        creator_now = strip_html(meta_list[index * 4])
        world_now = strip_html(meta_list[index * 4 + 1])
        if world_name and world_name not in world_now:
            continue
        expires_now = strip_html(meta_list[index * 4 + 2])
        updated_now = strip_html(meta_list[index * 4 + 3])
        total_now = strip_html(total_list[index])
        if search_text:
            search_area = f"{duty_now} {description_now} {creator_now} {world_now}".lower()
            if search_text.lower() not in search_area:
                continue
        category_label = PARTY_CATEGORY_LABELS.get(category_now, category_now)

        text_now = f"{index_now:02d}. [{category_label}] {duty_now}\n"
        text_now += f"    {truncate_text(description_now, 86)}\n"
        text_now += f"    {creator_now} | {world_now} | {total_now} | {expires_now} | {updated_now}\n"

        index_now += 1
        text_list.append(text_now)
        if len(text_list) >= limit:
            break
    return text_list


async def get_party_finder_texts(
    data_centre: str | None = None,
    world_name: str | None = None,
    world_id: int | None = None,
    category: str | None = None,
    search_text: str | None = None,
    job_ids: list[int] | None = None,
    limit: int = 10,
) -> list[str]:
    try:
        v2_texts = await get_party_finder_texts_api_v2(
            data_centre,
            world_id=world_id,
            category=category,
            search_text=search_text,
            job_ids=job_ids,
            limit=limit,
        )
        if v2_texts is not None:
            return v2_texts
    except Exception as exc:
        logger.warning(f"招募板 API v2 获取失败，尝试 API v1: {exc}")

    try:
        api_texts = await get_party_finder_texts_api_v1(
            data_centre,
            world_name=world_name,
            category=category,
            search_text=search_text,
            job_ids=job_ids,
            limit=limit,
        )
        if api_texts is not None:
            return api_texts
    except Exception as exc:
        logger.warning(f"招募板 API v1 获取失败，尝试 HTML 兜底: {exc}")

    return await get_party_finder_texts_html(
        data_centre,
        world_name=world_name,
        category=category,
        search_text=search_text,
        job_ids=job_ids,
        limit=limit,
    )


@register(
    "astrbot_plugin_tataru",
    "aaron-li / Codex",
    "FF14 塔塔露 AstrBot 插件",
    "0.14.0",
    "https://github.com/jawwe/TataruBot2/tree/codex-astrbot-plugin-tataru",
)
class TataruPlugin(Star):
    def __init__(self, context: Context, config=None):
        super().__init__(context)
        self.config = config or {}
        self.tarot_dict: dict | None = None
        self.cache_dir = PLUGIN_DIR / ".cache"
        self.calendar_task: asyncio.Task | None = None
        self.last_calendar_download_time: dict[str, datetime] = {}

    async def initialize(self):
        self.tarot_dict = load_tarot()
        self.cache_dir.mkdir(exist_ok=True)
        self.calendar_task = asyncio.create_task(self.download_calendar_loop())
        logger.info("Tataru AstrBot plugin initialized.")

    def default_calendar_server(self) -> str:
        return "国际服" if bool(self.config.get("use_global_calendar", False)) else "国服"

    def weibo_cookie(self) -> str:
        return str(self.config.get("weibo_cookie", "") or "").strip()

    def fflogs_client_id(self) -> str:
        return str(self.config.get("fflogs_client_id", "") or "").strip()

    def fflogs_client_secret(self) -> str:
        return str(self.config.get("fflogs_client_secret", "") or "").strip()

    def default_logs_cn_source(self) -> bool:
        return not bool(self.config.get("use_global_fflogs", False))

    @filter.command("帮帮忙")
    async def help(self, event: AstrMessageEvent):
        """显示塔塔露当前已迁移的指令。"""
        yield event.plain_result(create_help_text())

    @filter.command("选门")
    async def precious(self, event: AstrMessageEvent):
        """帮你选藏宝洞的门。"""
        yield event.plain_result("塔塔露在藏宝洞中横冲直撞！\n" + random_left_right())

    @filter.command("仙人彩")
    async def lottery(self, event: AstrMessageEvent):
        """帮你选每周仙人仙彩数字。"""
        yield event.plain_result("塔塔露觉得这个可以！\n" + random_lottery())

    @filter.command("日历")
    async def calendar(self, event: AstrMessageEvent):
        """获取FF近期活动日历。"""
        requested_server = command_args(event.message_str, "日历") or None
        server = normalize_calendar_server(requested_server, self.default_calendar_server())
        await self.ensure_calendar(server)
        yield event.plain_result(self.create_calendar_text(server))

    @filter.command("暖暖")
    async def nuannuan(self, event: AstrMessageEvent):
        """本周时尚品鉴作业。"""
        result = await self.create_nuannuan_result(event)
        yield result

    @filter.command("攻略")
    async def dungeon_note(self, event: AstrMessageEvent):
        """查简单副本攻略。"""
        dungeon_info = command_args(event.message_str, "攻略")
        result_text, as_text = await get_dungeon_note(dungeon_info)
        if as_text:
            yield event.plain_result(result_text)
            return

        image_path = self.cache_dir / "dungeon_note.jpg"
        text_to_image(result_text, image_path, width_now=25)
        yield event.image_result(str(image_path))

    @filter.command("招募")
    async def party_finder(self, event: AstrMessageEvent):
        """获取指定大区招募板信息。"""
        query = parse_party_finder_query(command_args(event.message_str, "招募"))
        if not query.data_centre and not query.search_terms and not query.category and not query.job_ids:
            yield event.plain_result("查招募版格式：招募 (大区或服务器) (分类或关键词或职业) (数量)\n例：招募 陆行鸟 随机任务")
            return

        try:
            world, search_terms = await resolve_party_world(query.search_terms)
        except Exception as exc:
            logger.warning(f"招募服务器名解析失败: {exc}")
            world, search_terms = None, query.search_terms
        search_text = " ".join(search_terms).strip() or None
        data_centre = query.data_centre
        if world:
            data_centre = data_centre or world["data_centre"]
        scope_label = world["name"] if world else (data_centre or "全服")

        try:
            text_list = await get_party_finder_texts(
                data_centre,
                world_name=world["name"] if world else None,
                world_id=world["id"] if world else None,
                category=query.category,
                search_text=search_text,
                job_ids=query.job_ids,
                limit=query.limit,
            )
        except Exception as exc:
            logger.warning(f"招募板获取失败: {exc}")
            yield event.plain_result("招募板获取失败，请稍后再试")
            return

        if not text_list:
            category_hint = f"「{PARTY_CATEGORY_LABELS.get(query.category, query.category)}」" if query.category else ""
            search_hint = f"包含「{search_text}」的" if search_text else ""
            job_hint = "指定职业的" if query.job_ids else ""
            yield event.plain_result(f"当前{scope_label}{category_hint}{search_hint}{job_hint}无人上传招募信息")
            return

        image_components = []
        for index in range(0, len(text_list), 10):
            category_label = PARTY_CATEGORY_LABELS.get(query.category, "全部") if query.category else "全部"
            search_label = search_text or "无"
            job_label = "有" if query.job_ids else "无"
            final_text = f"【{scope_label}招募板】分类：{category_label}  搜索：{search_label}  职业：{job_label}  数量：{len(text_list)}\n"
            final_text += "────────────────────────\n"
            final_text += "\n".join(text_list[index:index + 10])
            image_path = self.cache_dir / f"party_finder_{index // 10}.jpg"
            text_to_image(final_text, image_path, width_now=42)
            image_components.append(Comp.Image.fromFileSystem(str(image_path)))

        yield event.chain_result(image_components)

    @filter.command("看看微博")
    async def ff_weibo(self, event: AstrMessageEvent):
        """获取FF官方微博新闻。"""
        yield event.plain_result(await get_ff_weibo_text(self.weibo_cookie()))

    @filter.command("物品")
    async def item(self, event: AstrMessageEvent):
        """查询物品信息。"""
        item_name = command_args(event.message_str, "物品")
        if not item_name:
            yield event.plain_result("查物品格式：物品 物品名\n例：物品 铁矿")
            return

        try:
            item_text, icon_path = await create_item_info(item_name, self.cache_dir)
        except Exception as exc:
            logger.warning(f"物品查询失败: {exc}")
            yield event.plain_result("物品查询失败，请稍后再试")
            return

        text_image_path = self.cache_dir / "item_text.jpg"
        text_to_image(item_text, text_image_path, width_now=34)
        components = []
        if icon_path:
            components.append(Comp.Image.fromFileSystem(str(icon_path)))
        components.append(Comp.Image.fromFileSystem(str(text_image_path)))
        yield event.chain_result(components)

    @filter.command("价格")
    async def market(self, event: AstrMessageEvent):
        """查询市场物价。"""
        market_query = await parse_market_query(command_args(event.message_str, "价格"))
        if not market_query.item_name:
            yield event.plain_result("查物价格式：价格 (大区/服务器) 物品名 (HQ) (数量)\n例：价格 陆行鸟 铁矿 HQ 10")
            return

        try:
            market_text = await create_market_text(market_query)
        except Exception as exc:
            logger.warning(f"物价查询失败: {exc}")
            yield event.plain_result("物价查询失败，请稍后再试")
            return

        image_path = self.cache_dir / "market.jpg"
        text_to_image(market_text, image_path, width_now=42)
        yield event.image_result(str(image_path))

    @filter.command("房子")
    async def house(self, event: AstrMessageEvent):
        """查询指定服务器空房。"""
        async for result in self.create_house_result(event, "房子"):
            yield result

    @filter.command("房屋")
    async def house_alias(self, event: AstrMessageEvent):
        """查询指定服务器空房。"""
        async for result in self.create_house_result(event, "房屋"):
            yield result

    async def create_house_result(self, event: AstrMessageEvent, command: str):
        """查询指定服务器空房。"""
        house_info = command_args(event.message_str, command)
        house_query = parse_house_query(house_info)
        try:
            house_text = await create_house_text(house_query)
        except Exception as exc:
            logger.warning(f"房屋查询失败: {exc}")
            yield event.plain_result("房屋查询失败，请稍后再试")
            return

        if "────────────────────────" not in house_text:
            yield event.plain_result(house_text)
            return

        parts = house_text.split("\n")
        header = "\n".join(parts[:2])
        rows = parts[2:]
        components = []
        for index in range(0, len(rows), 30):
            page_text = header + "\n" + "\n".join(rows[index:index + 30])
            image_path = self.cache_dir / f"house_{index // 30}.jpg"
            text_to_image(page_text, image_path, width_now=44)
            components.append(Comp.Image.fromFileSystem(str(image_path)))
        yield event.chain_result(components)

    @filter.command("输出")
    async def logs_dps(self, event: AstrMessageEvent):
        """查询FFLogs输出分段。"""
        logs_query = parse_logs_query(command_args(event.message_str, "输出"), self.default_logs_cn_source())
        yield event.plain_result(
            await create_logs_text(
                logs_query,
                self.fflogs_client_id(),
                self.fflogs_client_secret(),
            )
        )

    @filter.command("抽卡")
    async def tarot(self, event: AstrMessageEvent):
        """随机抽取一张FF14塔罗牌。"""
        result = self.create_tarot_result(event)
        async for item in result:
            yield item

    async def create_tarot_result(self, event: AstrMessageEvent):
        if self.tarot_dict is None:
            self.tarot_dict = load_tarot()

        text_now, tarot_image_path = choose_tarot(self.tarot_dict)
        if not tarot_image_path.exists():
            yield event.plain_result(f"塔罗牌图片不存在：{tarot_image_path.name}")
            return

        text_image_path = self.cache_dir / "tarot_text.jpg"
        text_to_image(text_now, text_image_path)

        yield event.chain_result(
            [
                Comp.Image.fromFileSystem(str(text_image_path)),
                Comp.Image.fromFileSystem(str(tarot_image_path)),
            ]
        )

    async def download_calendar_loop(self):
        while True:
            try:
                await self.download_calendar_once(self.default_calendar_server())
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning(f"日历更新连接错误: {exc}")
            await asyncio.sleep(60 * 60)

    def calendar_cache_path(self, server: str) -> Path:
        return self.cache_dir / f"calendar_{'global' if server == '国际服' else 'cn'}.ics"

    async def download_calendar_once(self, server: str) -> bool:
        sources = CALENDAR_SOURCES[server]
        result = await aiohttp_get(sources["primary"], res_type="bytes")
        if result is None:
            logger.info(f"{server}日历主链接更新失败，尝试备用链接")
            result = await aiohttp_get(sources["fallback"], res_type="bytes")

        if result is None:
            logger.warning(f"{server}日历更新失败，将使用本地缓存")
            return False

        self.calendar_cache_path(server).write_bytes(result)
        self.last_calendar_download_time[server] = datetime.now()
        logger.info(f"{server}日历更新成功")
        return True

    async def ensure_calendar(self, server: str):
        cache_path = self.calendar_cache_path(server)
        if not cache_path.exists():
            await self.download_calendar_once(server)

    def calendar_read_path(self, server: str) -> Path | None:
        cache_path = self.calendar_cache_path(server)
        if cache_path.exists():
            return cache_path
        bundled_path = CALENDAR_SOURCES[server]["bundled"]
        if bundled_path and bundled_path.exists():
            return bundled_path
        return None

    def create_calendar_text(self, server: str) -> str:
        calendar_path = self.calendar_read_path(server)
        if calendar_path is None:
            return f"{server}日历文件不存在，请稍后再试"

        gcal = Calendar.from_ical(calendar_path.read_bytes())
        today = datetime.now().date()
        warn_ics = []
        week_ics = []
        future_ics = []

        for component in gcal.walk():
            if component.name != "VEVENT":
                continue

            start_raw = component.get("dtstart").dt
            end_raw = component.get("dtend").dt
            start_date, start_info = normalize_calendar_date(start_raw)
            end_date, end_info = normalize_calendar_date(end_raw)

            if end_date < today:
                continue

            info_item = [end_info, start_info, component.get("summary"), component.get("DESCRIPTION")]
            sortable_item = (end_date, start_date, str(component.get("summary")), info_item)
            days_left = (end_date - today).days
            if days_left <= 2:
                warn_ics.append(sortable_item)
            elif days_left <= 7:
                week_ics.append(sortable_item)
            else:
                future_ics.append(sortable_item)

        warn_ics.sort()
        week_ics.sort()
        future_ics.sort()

        result = f"【{server}日历】\n今天是 " + str(today).replace("-", ".") + "\n"
        if warn_ics:
            result += "【近2天结束】\n"
            for item in warn_ics:
                result += format_calendar_item(item[3]) + "\n"
        if week_ics:
            result += "【近7天内】\n"
            for item in week_ics:
                result += format_calendar_item(item[3]) + "\n"
        if future_ics:
            result += "【未来活动】\n"
            for item in future_ics:
                result += format_calendar_item(item[3]) + "\n"

        if server in self.last_calendar_download_time:
            result += "\n日历更新时间: " + str(self.last_calendar_download_time[server]).split(".")[0].replace("-", ".")
        else:
            result += "\n日历更新时间: 使用本地缓存"
        return result

    async def create_nuannuan_result(self, event: AstrMessageEvent):
        period = get_current_period()
        cache_path = self.cache_dir / "nuannuan.json"

        if cache_path.exists():
            try:
                cache = json.loads(cache_path.read_text(encoding="utf-8"))
                cached_message = cache.get(str(period))
                if cached_message:
                    image_path = self.cache_dir / "nuannuan.jpg"
                    text_to_image(cached_message, image_path, width_now=25)
                    return event.image_result(str(image_path))
            except Exception as exc:
                logger.warning(f"读取暖暖缓存失败: {exc}")

        try:
            bili_url = await get_bili_url()
            message = await get_bili_detail(bili_url)
            cache_path.write_text(json.dumps({str(period): message}, ensure_ascii=False), encoding="utf-8")
            image_path = self.cache_dir / "nuannuan.jpg"
            text_to_image(message, image_path, width_now=25)
            return event.image_result(str(image_path))
        except Exception as exc:
            logger.warning(f"暖暖获取失败: {exc}")
            return event.plain_result("暖暖获取失败，请看qq文档： " + QQ_DOC_URL)

    async def terminate(self):
        if self.calendar_task:
            self.calendar_task.cancel()
        logger.info("Tataru AstrBot plugin terminated.")
