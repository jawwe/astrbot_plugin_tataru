import asyncio
from datetime import date, datetime
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
DUNGEON_NOTE_URL = "https://ff14.org/duty"
PARTY_FINDER_URL = "https://xivpf.littlenightmare.top/listings"
PARTY_FINDER_API_V1_URL = "https://xivpf.littlenightmare.top/api/listings"
PARTY_FINDER_API_V2_URL = "https://xivpf.littlenightmare.top/api/v2/listings"
XIVAPI_BASE_URL = "https://xivapi-v2.xivcdn.com/api"
DATA_CENTRES = ["陆行鸟", "莫古力", "猫小胖", "豆豆柴"]
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
[抽卡] 随机抽取一张FF14塔罗牌

以下功能仍在迁移中：
[看看微博] [物品] [价格] [房子] [输出]
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


def parse_party_finder_query(query: str) -> tuple[str | None, str | None, str | None, int]:
    parts = query.split()
    if not parts:
        return None, None, None, 10

    data_centre = parts[0]
    category = None
    search_terms = []
    limit = 10
    for part in parts[1:]:
        if part.isdigit():
            limit = max(1, min(int(part), 40))
            continue
        normalized_category = normalize_party_category(part)
        if normalized_category:
            category = normalized_category
            continue
        search_terms.append(part)
    search_text = " ".join(search_terms).strip() or None
    return data_centre, category, search_text, limit


def truncate_text(text: str, length: int = 80) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= length:
        return text
    return text[:length - 1] + "…"


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
    data_centre: str,
    category: str | None = None,
    search_text: str | None = None,
    limit: int = 10,
) -> list[str] | None:
    params = {
        "page": 1,
        "per_page": max(1, min(limit, 100)),
        "datacenter": data_centre,
    }
    if category:
        params["category"] = category
    if search_text:
        params["search"] = search_text
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
    data_centre: str,
    category: str | None = None,
    search_text: str | None = None,
    limit: int = 10,
) -> list[str] | None:
    fetch_limit = 100 if search_text else max(1, min(limit, 100))
    params = {
        "page": 1,
        "per_page": fetch_limit,
        "datacenter": data_centre,
    }
    if category:
        category_id = PARTY_CATEGORY_IDS.get(category)
        if category_id is None:
            return None
        params["category_id"] = category_id
    payload = await aiohttp_get(f"{PARTY_FINDER_API_V2_URL}?{urlencode(params)}")
    listings = extract_party_finder_listings(payload)
    if listings is None:
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
    data_centre: str,
    category: str | None = None,
    search_text: str | None = None,
    limit: int = 10,
) -> list[str]:
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
        if data_centre not in data_centre_list[index]:
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
    data_centre: str,
    category: str | None = None,
    search_text: str | None = None,
    limit: int = 10,
) -> list[str]:
    try:
        v2_texts = await get_party_finder_texts_api_v2(
            data_centre,
            category=category,
            search_text=search_text,
            limit=limit,
        )
        if v2_texts is not None:
            return v2_texts
    except Exception as exc:
        logger.warning(f"招募板 API v2 获取失败，尝试 API v1: {exc}")

    try:
        api_texts = await get_party_finder_texts_api_v1(
            data_centre,
            category=category,
            search_text=search_text,
            limit=limit,
        )
        if api_texts is not None:
            return api_texts
    except Exception as exc:
        logger.warning(f"招募板 API v1 获取失败，尝试 HTML 兜底: {exc}")

    return await get_party_finder_texts_html(
        data_centre,
        category=category,
        search_text=search_text,
        limit=limit,
    )


@register(
    "astrbot_plugin_tataru",
    "aaron-li / Codex",
    "FF14 塔塔露 AstrBot 插件",
    "0.7.1",
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
        data_centre, category, search_text, limit = parse_party_finder_query(command_args(event.message_str, "招募"))
        if not data_centre:
            yield event.plain_result("查招募版格式：招募 大区名称 (分类或关键词) (数量)\n例：招募 陆行鸟 随机任务")
            return
        if data_centre not in DATA_CENTRES:
            yield event.plain_result("大区名称有误，限定" + str(DATA_CENTRES))
            return

        try:
            text_list = await get_party_finder_texts(
                data_centre,
                category=category,
                search_text=search_text,
                limit=limit,
            )
        except Exception as exc:
            logger.warning(f"招募板获取失败: {exc}")
            yield event.plain_result("招募板获取失败，请稍后再试")
            return

        if not text_list:
            category_hint = f"「{PARTY_CATEGORY_LABELS.get(category, category)}」" if category else ""
            search_hint = f"包含「{search_text}」的" if search_text else ""
            yield event.plain_result(f"当前{data_centre}{category_hint}{search_hint}无人上传招募信息")
            return

        image_components = []
        for index in range(0, len(text_list), 10):
            category_label = PARTY_CATEGORY_LABELS.get(category, "全部") if category else "全部"
            search_label = search_text or "无"
            final_text = f"【{data_centre}招募板】分类：{category_label}  搜索：{search_label}  数量：{len(text_list)}\n"
            final_text += "────────────────────────\n"
            final_text += "\n".join(text_list[index:index + 10])
            image_path = self.cache_dir / f"party_finder_{index // 10}.jpg"
            text_to_image(final_text, image_path, width_now=42)
            image_components.append(Comp.Image.fromFileSystem(str(image_path)))

        yield event.chain_result(image_components)

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
