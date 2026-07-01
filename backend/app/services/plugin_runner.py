"""
插件运行器：根据国家配置加载并执行相应插件。

插件调用签名:
    def apply(conn, scored, profile, bg, rule, context) -> list[dict]

使用方式:
    from ..services.plugin_runner import run_plugins
    scored = run_plugins(conn, scored, profile, bg, rule, context)
"""

import importlib
import logging

from .country_rules import get_rule


logger = logging.getLogger(__name__)


def _load_plugin(name: str):
    """动态加载插件模块"""
    try:
        return importlib.import_module(f"backend.app.services.plugins.{name}")
    except ImportError:
        try:
            return importlib.import_module(f"app.services.plugins.{name}")
        except ImportError:
            return None


def run_plugins(conn, scored, profile, bg, rule, context):
    """根据国家配置运行所有插件"""
    plugin_names = rule.get("plugins", [])

    for plugin_name in plugin_names:
        plugin_mod = _load_plugin(plugin_name)
        if plugin_mod and hasattr(plugin_mod, "apply"):
            try:
                scored = plugin_mod.apply(conn, scored, profile, bg, rule, context)
            except Exception as e:
                logger.warning("Plugin %s failed: %s", plugin_name, e)

    return scored
