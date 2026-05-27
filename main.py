import asyncio
from datetime import date, datetime
import html
import json
import random
import re
from pathlib import Path

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
CALENDAR_PATH = DATA_DIR / "calendar.ics"
CALENDAR_URL = (
    "https://p66-caldav.icloud.com/published/2/"
    "MTAyMTk3MTMxMjExMDIxOXsjasy7WUO0EcKVz7qGEuVjjTlRkgd6"
    "WOZM171uxP_u-QM51M24lHzRlAQir-oodDRRTzZeusSLbw0snkZoqI4"
)
GOOGLE_CALENDAR_URL = (
    "https://calendar.google.com/calendar/ical/"
    "up88drvlnnh2t77hbpqq8v33i2cngfh7%40import.calendar.google.com/public/basic.ics"
)
QQ_DOC_URL = "https://docs.qq.com/sheet/DY2lCeEpwemZESm5q?tab=dewveu&c=A1A0A0"
BILI_USER_ID = 15503317


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
            return await response.json(content_type=None)


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
[日历] 获取FF近期活动日历
[抽卡] 随机抽取一张FF14塔罗牌

以下功能仍在迁移中：
[看看微博] [物品] [价格] [房子] [输出] [攻略] [招募]
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
    docs_text = await aiohttp_get(docs_url, res_type="text", headers=headers)
    if docs_text:
        match = re.search(r"https:\\?/\\?/www\.bilibili\.com/video/[^'\"\\]+", docs_text)
        if match:
            return match.group(0).replace("\\/", "/")

    period = get_current_period()
    prefix = f"【FF14/时尚品鉴】第{period}期"
    api_url = f"https://api.bilibili.com/x/space/arc/search?mid={BILI_USER_ID}&ps=5&pn=1"
    data = await aiohttp_get(api_url, headers={"referer": f"https://space.bilibili.com/{BILI_USER_ID}"})
    if data and data.get("code") == 0:
        videos = data.get("data", {}).get("list", {}).get("vlist", [])
        for video in videos:
            if str(video.get("title", "")).startswith(prefix):
                return f"https://www.bilibili.com/video/{video['bvid']}"

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


@register(
    "astrbot_plugin_tataru",
    "aaron-li / Codex",
    "FF14 塔塔露 AstrBot 插件",
    "0.2.1",
    "https://github.com/jawwe/TataruBot2/tree/codex-astrbot-plugin-tataru",
)
class TataruPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.tarot_dict: dict | None = None
        self.cache_dir = PLUGIN_DIR / ".cache"
        self.calendar_task: asyncio.Task | None = None
        self.last_calendar_download_time: datetime | None = None

    async def initialize(self):
        self.tarot_dict = load_tarot()
        self.cache_dir.mkdir(exist_ok=True)
        self.calendar_task = asyncio.create_task(self.download_calendar_loop())
        logger.info("Tataru AstrBot plugin initialized.")

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
        yield event.plain_result(self.create_calendar_text())

    @filter.command("暖暖")
    async def nuannuan(self, event: AstrMessageEvent):
        """本周时尚品鉴作业。"""
        result = await self.create_nuannuan_result(event)
        yield result

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
                await self.download_calendar_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning(f"日历更新连接错误: {exc}")
            await asyncio.sleep(60 * 60)

    async def download_calendar_once(self):
        result = await aiohttp_get(CALENDAR_URL, res_type="bytes")
        if result is None:
            logger.info("日历主链接更新失败，尝试备用链接")
            result = await aiohttp_get(GOOGLE_CALENDAR_URL, res_type="bytes")

        if result is None:
            logger.warning("日历更新失败，将使用本地缓存")
            return

        CALENDAR_PATH.write_bytes(result)
        self.last_calendar_download_time = datetime.now()
        logger.info("日历更新成功")

    def create_calendar_text(self) -> str:
        if not CALENDAR_PATH.exists():
            return "日历文件不存在，请稍后再试"

        gcal = Calendar.from_ical(CALENDAR_PATH.read_bytes())
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
            days_left = (end_date - today).days
            if days_left <= 2:
                warn_ics.append(info_item)
            elif days_left <= 7:
                week_ics.append(info_item)
            else:
                future_ics.append(info_item)

        warn_ics.sort()
        week_ics.sort()
        future_ics.sort()

        result = "今天是 " + str(today).replace("-", ".") + "\n"
        if warn_ics:
            result += "【近2天结束】\n"
            for item in warn_ics:
                result += format_calendar_item(item) + "\n"
        if week_ics:
            result += "【近7天内】\n"
            for item in week_ics:
                result += format_calendar_item(item) + "\n"
        if future_ics:
            result += "【未来活动】\n"
            for item in future_ics:
                result += format_calendar_item(item) + "\n"

        if self.last_calendar_download_time:
            result += "\n日历更新时间: " + str(self.last_calendar_download_time).split(".")[0].replace("-", ".")
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
