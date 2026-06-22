"""Focused tests for plugin behavior independent of a running AstrBot instance."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def plugin_module(monkeypatch):
    """Import main.py with the small AstrBot API surface it requires."""
    astrbot = types.ModuleType("astrbot")
    api = types.ModuleType("astrbot.api")
    api.logger = types.SimpleNamespace(info=lambda *_: None, warning=lambda *_: None)
    event = types.ModuleType("astrbot.api.event")
    event.AstrMessageEvent = object
    event.filter = types.SimpleNamespace(command=lambda *_: lambda handler: handler)
    components = types.ModuleType("astrbot.api.message_components")
    star = types.ModuleType("astrbot.api.star")
    star.Context = object

    class Star:
        def __init__(self, _context) -> None:
            pass

    star.Star = Star
    star.register = lambda *_args, **_kwargs: lambda cls: cls

    monkeypatch.setitem(sys.modules, "astrbot", astrbot)
    monkeypatch.setitem(sys.modules, "astrbot.api", api)
    monkeypatch.setitem(sys.modules, "astrbot.api.event", event)
    monkeypatch.setitem(sys.modules, "astrbot.api.message_components", components)
    monkeypatch.setitem(sys.modules, "astrbot.api.star", star)

    spec = importlib.util.spec_from_file_location(
        "tataru_test_module", ROOT / "main.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_plugin_configuration_schema_is_valid() -> None:
    """Ensure the plugin configuration schema remains valid JSON."""
    schema = json.loads((ROOT / "_conf_schema.json").read_text(encoding="utf-8"))
    assert schema["debug_mode"]["type"] == "bool"
    assert schema["proxy_enabled"]["type"] == "bool"
    assert schema["proxy_port"]["type"] == "int"


def test_sensitive_debug_values_are_masked(plugin_module) -> None:
    """Keep credentials out of debug output while retaining an identifiable suffix."""
    assert plugin_module.mask_debug_secret("abcdefgh") == "ab****gh"
    assert plugin_module.mask_debug_secret("abcd") == "****"
    assert plugin_module.sanitize_debug_url(
        "https://example.test/?token=abcdef"
    ).endswith("token=ab**ef")
    assert (
        plugin_module.sanitize_debug_value("curl sensitive-value", "curl")
        == "cu****************ue"
    )


def test_proxy_settings_require_complete_authentication(plugin_module) -> None:
    """Reject incomplete proxy credentials instead of silently using direct traffic."""
    plugin_module.configure_network_settings(
        {
            "proxy_enabled": True,
            "proxy_host": "127.0.0.1",
            "proxy_port": 7890,
            "proxy_username": "only-user",
        }
    )
    with pytest.raises(plugin_module.ProxyConfigurationError):
        plugin_module.proxy_request_options()


def test_proxy_host_rejects_embedded_port(plugin_module) -> None:
    """Reject host:port input while preserving valid IPv6 proxy hosts."""
    plugin_module.configure_network_settings(
        {
            "proxy_enabled": True,
            "proxy_host": "127.0.0.1:7890",
            "proxy_port": 7890,
        }
    )
    with pytest.raises(plugin_module.ProxyConfigurationError):
        plugin_module.proxy_request_options()

    plugin_module.configure_network_settings(
        {
            "proxy_enabled": True,
            "proxy_host": "127.0.0.1:abc",
            "proxy_port": 7890,
        }
    )
    with pytest.raises(plugin_module.ProxyConfigurationError):
        plugin_module.proxy_request_options()

    plugin_module.configure_network_settings(
        {
            "proxy_enabled": True,
            "proxy_host": "::1",
            "proxy_port": 7890,
        }
    )
    assert plugin_module.proxy_request_options()["proxy"] == "http://[::1]:7890"


def test_risingstones_posts_query_and_formatting(plugin_module) -> None:
    """Keep public Rising Stones content lookups bounded and human-readable."""
    query = plugin_module.parse_risingstones_posts_query("攻略 零式 99")
    assert query.kind == "strat"
    assert query.keyword == "零式"
    assert query.limit == 20

    text = plugin_module.format_risingstones_posts(
        query,
        [
            {
                "posts_id": 123,
                "title": "零式攻略",
                "part_name": "攻略",
                "character_name": "塔塔露",
                "area_name": "海猫茶屋",
                "read_count": 120,
                "comment_count": 4,
                "like_count": 9,
                "created_at": "2026-06-22 12:00:00",
            }
        ],
    )
    assert "【石之家攻略】 关键词：零式 数量：1" in text
    assert "浏览：120 | 评论：4 | 点赞：9" in text
    assert "#/strat/detail/123" in text


def test_risingstones_recruit_query_and_formatting(plugin_module) -> None:
    """Preserve public recruitment type selection and bounded output."""
    query = plugin_module.parse_risingstones_recruit_query("副本 妖星乱舞 30")
    assert query.kind == "party"
    assert query.keyword == "妖星乱舞"
    assert query.limit == 20

    text = plugin_module.format_risingstones_recruits(
        query,
        [
            {
                "id": 53483,
                "fb_name": "妖星乱舞绝境战",
                "fb_type": "绝境战",
                "character_name": "尹辞",
                "area_name": "莫古力",
                "group_name": "拂晓之间",
                "fb_time": "晚8-12 2h",
                "progress": "P3",
                "strategy": "寿司优化",
                "jobInfo": [{"value": "防护职业"}],
                "updated_at": "2026-06-22 02:20:01",
            }
        ],
    )
    assert "【石之家招募】类型：副本 关键词：妖星乱舞 数量：1" in text
    assert "需求：防护职业" in text
    assert "#/recruit/party?id=53483" in text


def test_risingstones_account_store_and_credentials(plugin_module, tmp_path) -> None:
    """Keep credentials isolated per account and auto check-ins bounded by day."""
    store = plugin_module.RisingstonesAccountStore(tmp_path / "risingstones.sqlite3")
    store.initialize()
    credentials = plugin_module.RisingstonesCredentials(
        cookie="ff14risingstones=abc", user_agent="Mozilla/5.0 Test"
    )
    store.set_credential("qq:10001", credentials)
    assert store.get_credential("qq:10001") == "ff14risingstones=abc"
    assert store.get_credentials("qq:10001") == credentials
    assert store.due_auto_checkins("2026-06-22") == []

    assert store.set_auto_checkin("qq:10001", True)
    assert store.due_auto_checkins("2026-06-22") == [("qq:10001", credentials)]
    store.mark_attempt("qq:10001", "2026-06-22")
    assert store.due_auto_checkins("2026-06-22") == []
    assert store.due_auto_checkins("2026-06-23") == [("qq:10001", credentials)]
    assert store.remove("qq:10001")
    assert store.get_credential("qq:10001") is None

    assert (
        plugin_module.normalize_risingstones_cookie(
            "other=value; ff14risingstones=abc; trailing=value"
        )
        == "ff14risingstones=abc"
    )
    assert (
        plugin_module.parse_risingstones_binding(
            "ff14risingstones=abc | Mozilla/5.0 Test"
        )
        == credentials
    )
    curl_binding = """curl 'https://apiff14risingstones.web.sdo.com/api/home/userInfo/getUserInfo' \\
  -H 'cookie: other=value; ff14risingstones=abc; trailing=value' \\
  -H 'user-agent: Mozilla/5.0 Test'"""
    assert plugin_module.parse_risingstones_curl_binding(curl_binding) == credentials
    windows_curl_binding = r'''curl ^"https://apiff14risingstones.web.sdo.com/api/home/userInfo/getUserInfo^" ^
  -b ^"other=value; ff14risingstones=abc^%^3Avalue; trailing=value^" ^
  -H ^"user-agent: Mozilla/5.0 Test^"'''
    assert plugin_module.parse_risingstones_curl_binding(windows_curl_binding) == (
        plugin_module.RisingstonesCredentials(
            cookie="ff14risingstones=abc%3Avalue", user_agent="Mozilla/5.0 Test"
        )
    )
    assert plugin_module.parse_risingstones_binding("ff14risingstones=abc") is None
    assert (
        plugin_module.configured_risingstones_credentials(
            {
                "risingstones_owner_curl": (
                    "curl 'https://apiff14risingstones.web.sdo.com/api/home/userInfo/getUserInfo' "
                    "-b 'other=value; ff14risingstones=abc' "
                    "-H 'user-agent: Mozilla/5.0 Test'"
                ),
            }
        )
        == credentials
    )
    assert plugin_module.configured_risingstones_credentials(None) is None
    guide = plugin_module.risingstones_binding_guide()
    assert "getUserInfo" in guide
    assert "Copy as cURL (bash)" in guide


def test_risingstones_personal_actions_never_use_owner_cookie(
    plugin_module, monkeypatch
) -> None:
    """Personal account data must be rejected before any global fallback is considered."""

    class GroupEvent:
        def is_private_chat(self) -> bool:
            return False

    plugin = object.__new__(plugin_module.TataruPlugin)
    plugin.config = {
        "risingstones_owner_curl": (
            "curl 'https://apiff14risingstones.web.sdo.com/api/home/userInfo/getUserInfo' "
            "-b 'ff14risingstones=owner' -H 'user-agent: Mozilla/5.0 Test'"
        ),
    }

    async def no_glamour_rows(*_args, **_kwargs) -> list[dict]:
        return []

    monkeypatch.setattr(plugin_module, "risingstones_glamour_rows", no_glamour_rows)

    personal_result = asyncio.run(
        plugin.risingstones_private_action(GroupEvent(), "我的")
    )
    session_result = asyncio.run(
        plugin.risingstones_private_action(GroupEvent(), "幻化")
    )

    assert "仅支持私聊" in personal_result
    assert session_result == "没有找到符合条件的石之家幻化投稿。"


def test_risingstones_private_response_formatting(plugin_module) -> None:
    """Render private profile and notification payloads without raw identifiers."""
    profile = plugin_module.format_risingstones_profile(
        {
            "character_name": "塔塔露",
            "area_name": "陆行鸟",
            "group_name": "红玉海",
            "experience": 120,
            "followFansiNum": {"followNum": 3, "fansNum": 4},
            "beLikedNum": 5,
            "characterDetail": [{"play_time": "100小时"}],
        }
    )
    assert "【石之家档案】塔塔露 @ 陆行鸟@红玉海" in profile
    assert "游戏时长：100小时" in profile

    notifications = plugin_module.format_risingstones_notifications(
        {"sysNum": "2", "commentMsgNum": 1, "newFensNum": 3}
    )
    assert "系统消息：2" in notifications
    assert "评论：1" in notifications
    assert "新粉丝：3" in notifications


def test_risingstones_glamour_action_returns_individual_messages(
    plugin_module, monkeypatch
) -> None:
    """Each glamour result should carry its own image and formatted equipment text."""

    class GroupEvent:
        def is_private_chat(self) -> bool:
            return False

    plugin = object.__new__(plugin_module.TataruPlugin)
    plugin.config = {
        "risingstones_owner_curl": (
            "curl 'https://apiff14risingstones.web.sdo.com/api/home/userInfo/getUserInfo' "
            "-b 'ff14risingstones=owner' -H 'user-agent: Mozilla/5.0 Test'"
        ),
    }

    async def glamour_rows(*_args, **_kwargs) -> list[dict]:
        return [
            {
                "id": 265250,
                "title": "夏日白衣",
                "main_image": "https://example.com/glamour.jpg",
                "equipments": [{"slot": "BODY", "name": "夏暮沙滩罩衫"}],
            }
        ]

    monkeypatch.setattr(plugin_module, "risingstones_glamour_rows", glamour_rows)
    response = asyncio.run(plugin.risingstones_private_action(GroupEvent(), "幻化"))

    assert isinstance(response, plugin_module.RisingstonesGlamourResponse)
    assert len(response.messages) == 1
    assert response.messages[0].image_url == "https://example.com/glamour.jpg"
    assert "上衣：夏暮沙滩罩衫" in response.messages[0].text


def test_risingstones_statistics_formatting(plugin_module) -> None:
    """Only verified statistic fields should be included in summary output."""
    assert plugin_module.parse_risingstones_stat_kind("零式") == "savage"
    assert plugin_module.risingstones_stat_lines(
        "savage", {"territory_num": 4, "enter_num": 10, "finish_times": 2}
    ) == ["已记录副本数：4个", "进入次数：10次", "完成次数：2次"]
    text = plugin_module.format_risingstones_statistics(
        {"savage": ["已记录副本数：4个"]}
    )
    assert "[零式数据]" in text


def test_risingstones_glamour_query_and_formatting(plugin_module) -> None:
    """Support list, equipment and detail lookup forms without leaking payloads."""
    query = plugin_module.parse_risingstones_glamour_query("装备 纯白长袍 30")
    assert query.mode == "equipment"
    assert query.value == "纯白长袍"
    assert query.limit == 20

    detail = plugin_module.parse_risingstones_glamour_query("详情 265250")
    assert detail.mode == "detail"
    assert detail.value == "265250"

    text = plugin_module.format_risingstones_glamour(
        query,
        [
            {
                "id": 265250,
                "title": "夏日白衣",
                "character_name": "塔塔露",
                "area_name": "陆行鸟",
                "group_name": "红玉海",
                "desc": "清爽搭配",
                "likes": 12,
                "favorites": 3,
            }
        ],
    )
    assert "【石之家幻化】装备检索 数量：1" in text
    assert "点赞：12 | 收藏：3" in text
    assert "#/glamour/detail/265250" in text

    message = plugin_module.format_risingstones_glamour_message(
        query,
        {
            "id": 265250,
            "title": "夏日白衣",
            "character_name": "塔塔露",
            "main_image": "https://example.com/glamour.jpg",
            "equipments": [
                {
                    "slot": "BODY",
                    "name": "夏暮沙滩罩衫",
                    "dyes": [{"name": "柔彩粉染剂"}, {"name": "煤烟黑染剂"}],
                }
            ],
        },
        1,
        1,
    )
    assert message.image_url == "https://example.com/glamour.jpg"
    assert "装备：\n上衣：夏暮沙滩罩衫（柔彩粉染剂 / 煤烟黑染剂）" in message.text


def test_risingstones_guild_query_and_formatting(plugin_module) -> None:
    """Render private guild recruitment list and detail URLs consistently."""
    query = plugin_module.parse_risingstones_guild_query("星海 50")
    assert query.mode == "list"
    assert query.value == "星海"
    assert query.limit == 20
    detail = plugin_module.parse_risingstones_guild_query("详情 12345")
    assert detail.mode == "detail"
    assert detail.value == "12345"

    text = plugin_module.format_risingstones_guilds(
        query,
        [
            {
                "id": 12345,
                "guild_name": "星海旅团",
                "character_name": "塔塔露",
                "area_name": "陆行鸟",
                "group_name": "红玉海",
                "target_area_name": "陆行鸟",
                "target_group_name": "红玉海",
                "labelInfo": [{"name": "休闲"}],
                "active_member_num": "6-20",
                "weekday_time": "20:00-23:00",
                "detail_mask": "欢迎加入",
            }
        ],
    )
    assert "【石之家部队招待】数量：1" in text
    assert "标签：休闲" in text
    assert "#/recruit/guild/detail/12345" in text


def test_admin_store_persists_feature_flags_and_masks_activity(
    plugin_module, tmp_path
) -> None:
    """Admin state is persistent while activity details never retain secrets."""
    store = plugin_module.PluginAdminStore(tmp_path / "admin.sqlite3")
    store.initialize()

    store.set_feature_flags({"logs_dps": False, "risingstones_content": True})
    assert store.get_feature_flags()["logs_dps"] is False
    assert store.get_feature_flags()["risingstones_content"] is True

    store.record_activity("test", "success", "cookie=secret-value")
    activity = store.recent_activity(limit=1)
    assert activity[0]["source"] == "test"
    assert activity[0]["status"] == "success"
    assert "secret-value" not in activity[0]["detail"]


def test_admin_feature_flags_and_overview_are_real(plugin_module, tmp_path) -> None:
    """Overview reports runtime values and feature flags default to enabled."""
    store = plugin_module.PluginAdminStore(tmp_path / "admin.sqlite3")
    store.initialize()
    store.set_feature_flags({"logs_dps": False})

    assert plugin_module.feature_enabled(store, "logs_dps") is False
    assert plugin_module.feature_enabled(store, "risingstones_content") is True

    overview = plugin_module.build_admin_overview(
        store,
        version="1.0.25",
        started_at=plugin_module.datetime.now(plugin_module.RISINGSTONES_TIMEZONE),
        risingstones_accounts=3,
        auto_checkin_accounts=2,
    )
    assert overview["version"] == "1.0.25"
    assert overview["risingstones_accounts"] == 3
    assert overview["auto_checkin_accounts"] == 2
    assert overview["feature_flags"]["logs_dps"] is False


def test_admin_test_results_and_owner_curl_are_sanitized(plugin_module) -> None:
    """Page test responses never expose credentials and accept only getUserInfo cURL."""
    result = plugin_module.sanitize_admin_test_result(
        {"cookie": "secret", "latency_ms": 12, "message": "ok"}
    )
    assert "cookie" not in result
    assert result == {"latency_ms": 12, "message": "ok"}
    assert plugin_module.validate_owner_curl_for_admin(
        "curl 'https://apiff14risingstones.web.sdo.com/api/home/userInfo/getUserInfo' "
        "-b 'ff14risingstones=abc' -H 'user-agent: Mozilla/5.0'"
    )
    assert not plugin_module.validate_owner_curl_for_admin("curl https://example.test")


def test_admin_command_groups_and_cache_summary(plugin_module, tmp_path) -> None:
    """The Page can control command groups and report only real cache files."""
    cache_dir = tmp_path / ".cache"
    cache_dir.mkdir()
    (cache_dir / "response.jpg").write_bytes(b"1234")
    (cache_dir / "ignored").mkdir()

    assert plugin_module.admin_feature_for_command("输出") == "logs_dps"
    assert plugin_module.admin_feature_for_command("房屋") == "house"
    assert plugin_module.admin_feature_for_command("未知指令") is None
    assert plugin_module.plugin_cache_size(cache_dir) == 4


def test_admin_database_summary_reserves_fflogs_tracking(
    plugin_module, tmp_path
) -> None:
    """The admin database always reserves a separate FFLogs tracking table."""
    store = plugin_module.PluginAdminStore(tmp_path / "admin.sqlite3")
    store.initialize()

    summary = store.database_summary()

    assert "fflogs_tracking_accounts" in summary["tables"]
    assert summary["row_counts"]["fflogs_tracking_accounts"] == 0


def test_admin_page_registers_authenticated_operations_routes(plugin_module) -> None:
    """Plugin construction registers all Page routes on the AstrBot context."""
    routes = []

    class Context:
        def register_web_api(self, route, handler, methods, description) -> None:
            routes.append((route, handler, methods, description))

    plugin_module.TataruPlugin(Context(), {})

    registered = {
        (route, tuple(methods)) for route, _handler, methods, _description in routes
    }
    base = f"/{plugin_module.PLUGIN_NAME}/admin"
    expected = {
        (f"{base}/overview", ("GET",)),
        (f"{base}/settings", ("GET",)),
        (f"{base}/settings", ("POST",)),
        (f"{base}/features", ("GET",)),
        (f"{base}/features", ("POST",)),
        (f"{base}/tests/proxy", ("POST",)),
        (f"{base}/tests/fflogs", ("POST",)),
        (f"{base}/tests/risingstones", ("POST",)),
        (f"{base}/tests/sources", ("POST",)),
        (f"{base}/risingstones/owner-curl", ("GET",)),
        (f"{base}/risingstones/owner-curl", ("POST",)),
        (f"{base}/risingstones/accounts", ("GET",)),
        (f"{base}/database/summary", ("GET",)),
        (f"{base}/database/backup", ("POST",)),
        (f"{base}/database/clear-cache", ("POST",)),
        (f"{base}/activity", ("GET",)),
    }
    assert expected.issubset(registered)


def test_admin_overview_reports_sanitized_runtime_state(
    plugin_module, tmp_path
) -> None:
    """The overview route emits operational fields without any credentials."""

    class Context:
        def register_web_api(self, *_args) -> None:
            pass

    plugin = plugin_module.TataruPlugin(Context(), {})
    plugin.cache_dir = tmp_path / ".cache"
    plugin.cache_dir.mkdir()
    plugin.admin_store = plugin_module.PluginAdminStore(tmp_path / "admin.sqlite3")
    plugin.risingstones_accounts = plugin_module.RisingstonesAccountStore(
        tmp_path / "risingstones.sqlite3"
    )
    plugin.admin_store.initialize()
    plugin.risingstones_accounts.initialize()

    overview = asyncio.run(plugin.admin_overview())

    assert overview["version"] == plugin_module.PLUGIN_VERSION
    assert overview["sources"]["risingstones_owner_configured"] is False
    assert "risingstones_owner_curl" not in overview


def test_admin_feature_flags_are_individual_and_migrate_legacy_groups(
    plugin_module, tmp_path
) -> None:
    """Old grouped switches migrate to separate command and Rising Stones flags."""
    store = plugin_module.PluginAdminStore(tmp_path / "admin.sqlite3")
    store.initialize()
    store.set_setting(
        "feature_flags",
        json.dumps({"core": False, "risingstones": False}),
    )

    flags = store.get_feature_flags()

    assert flags["calendar"] is False
    assert flags["help"] is False
    assert flags["risingstones_content"] is False
    assert flags["risingstones_guild"] is False

    store.set_feature_flags({"calendar": True})
    flags = store.get_feature_flags()
    assert flags["calendar"] is True
    assert flags["help"] is False
    assert (
        plugin_module.risingstones_feature_for_query("解绑") == "risingstones_binding"
    )
    assert (
        plugin_module.risingstones_feature_for_query("幻化 夏日")
        == "risingstones_glamour"
    )


def test_admin_settings_hide_secrets_and_validate_updates(plugin_module) -> None:
    """Settings Page reads secret state only and validates editable fields."""
    config = {
        "debug_mode": True,
        "proxy_enabled": True,
        "proxy_port": 7890,
        "weibo_cookie": "private-cookie",
        "fflogs_client_id": "client-id",
        "fflogs_client_secret": "client-secret",
        "proxy_password": "proxy-password",
    }

    public = plugin_module.admin_settings_public_view(config)
    assert "private-cookie" not in public.values()
    assert public["weibo_cookie_set"] is True
    assert public["fflogs_client_secret_set"] is True
    assert public["proxy_password_set"] is True

    updates = plugin_module.validate_admin_settings_update(
        {
            "settings": {
                "debug_mode": False,
                "proxy_port": 8080,
                "font_path": "/fonts/SimHei.ttf",
                "weibo_cookie": "",
            },
            "clear_secrets": ["weibo_cookie"],
        }
    )
    assert updates["debug_mode"] is False
    assert updates["proxy_port"] == 8080
    assert updates["font_path"] == "/fonts/SimHei.ttf"
    assert updates["weibo_cookie"] == ""


def test_admin_display_mask_keeps_short_prefix_suffix(plugin_module) -> None:
    """Page summaries preserve three boundary characters with at most ten stars."""
    masked = plugin_module.mask_admin_display_secret("abcdefghijklmnopqrst")
    assert masked.startswith("abc")
    assert masked.endswith("rst")
    assert masked.count("*") == 10
