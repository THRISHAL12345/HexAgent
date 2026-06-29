import os
import tomllib
import importlib.util
from typing import Dict, List, Optional
import logging
from tools.base import Tool

logger = logging.getLogger(__name__)

class ToolRegistry:
    def __init__(self, plugins_dir: str = "tools/plugins"):
        self.plugins_dir = plugins_dir
        self._tools: Dict[str, Tool] = {}
        self.discover_tools()

    def discover_tools(self) -> List[Tool]:
        if not os.path.exists(self.plugins_dir):
            return []
            
        for entry in os.scandir(self.plugins_dir):
            if entry.is_dir():
                manifest_path = os.path.join(entry.path, "manifest.toml")
                plugin_path = os.path.join(entry.path, "plugin.py")
                if os.path.exists(manifest_path) and os.path.exists(plugin_path):
                    self._load_plugin(entry.path, manifest_path, plugin_path)
        return list(self._tools.values())

    def _load_plugin(self, plugin_dir: str, manifest_path: str, plugin_path: str):
        try:
            with open(manifest_path, 'rb') as f:
                manifest = tomllib.load(f)
            
            tool_name = manifest['tool']['name']
            
            spec = importlib.util.spec_from_file_location(f"plugin_{tool_name}", plugin_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find the Tool subclass
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, Tool) and attr is not Tool:
                        tool_instance = attr()
                        
                        # Inject manifest attributes
                        tool_instance.name = manifest['tool'].get('name', tool_name)
                        tool_instance.description = manifest['tool'].get('description', '')
                        tool_instance.category = manifest['tool'].get('category', 'util')
                        tool_instance.requires_root = manifest['tool'].get('requires_root', False)
                        tool_instance.network_facing = manifest['tool'].get('network_facing', False)
                        tool_instance.destructive = manifest['tool'].get('destructive', False)
                        tool_instance.input_schema = manifest.get('input', {})
                        tool_instance.output_schema = manifest.get('output', {})
                        
                        self._tools[tool_instance.name] = tool_instance
                        logger.debug(f"Loaded tool plugin: {tool_instance.name}")
                        break
        except Exception as e:
            logger.error(f"Failed to load plugin from {plugin_dir}: {e}")

    def choose_tool(self, objective: str, context: dict) -> Optional[Tool]:
        # Uses embedding similarity against tool descriptions and keywords.
        # Falls back to LLM selection if similarity score < 0.75.
        # TODO: Implement semantic search
        return None

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_by_category(self, category: str) -> List[Tool]:
        return [tool for tool in self._tools.values() if tool.category == category]
