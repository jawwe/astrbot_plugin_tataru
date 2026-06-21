"""Focused tests for plugin behavior independent of a running AstrBot instance."""

from __future__ import annotations

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
    star.Star = object
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
