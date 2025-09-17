"""
ASCEND Plugin Manager
Provides plugin loading, management, and lifecycle management functionality.
Supports the following features:
- Plugin lifecycle management (load, initialize, start, stop, unload)
- Plugin configuration management
- Plugin dependency management
- Plugin status monitoring
"""

import importlib
import pkg_resources
import logging
from typing import Dict, Any, List, Optional, Type
from pathlib import Path
from pydantic import ValidationError

from .base import IPlugin, BasePlugin, PluginRegistry
from .discovery import PluginDiscovery
from .types import PluginInfo, PluginState, PluginStatus
from ..core.exceptions import PluginError, PluginNotFoundError, PluginLoadError
from ..core.types import Config

logger = logging.getLogger(__name__)

class BasePluginManager:
    """Base plugin manager class.
    
    Responsible for plugin lifecycle management and status maintenance.
    
    Attributes:
        discovery: Plugin discoverer
        plugins: Loaded plugin instances
        plugin_status: Plugin status information
    """
    
    def __init__(self, plugin_paths: Optional[List[str]] = None) -> None:
        """Initialize plugin manager
        
        Args:
            plugin_paths: Plugin search paths
        """
        self.discovery = PluginDiscovery(plugin_paths)
        self.plugins: Dict[str, IPlugin] = {}
        self.plugin_status: Dict[str, PluginStatus] = {}
        # 自动发现内置插件
        self.discover_plugins()
        
    def discover_plugins(self) -> Dict[str, PluginInfo]:
        """Discover available plugins

        Returns:
            Dictionary of plugin information
        """
        # 通过discovery机制发现所有插件（包括内置插件）
        discovered = self.discovery.discover_plugins()
        logger.info(f"Discovered plugins: {list(discovered.keys())}")
        
        # 更新每个插件的状态
        for name, info in discovered.items():
            if name not in self.plugin_status:
                dependencies = getattr(info, 'dependencies', [])
                self.plugin_status[name] = PluginStatus(
                    state=PluginState.DISCOVERED,
                    dependencies={dep: False for dep in dependencies}
                )
                logger.info(f"Added plugin status for: {name}")
                
        return discovered
    
    def load_plugin(self, name: str) -> IPlugin:
        """Load a plugin
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin instance
            
        Raises:
            PluginError: If plugin loading fails
        """
        try:
            logger.info(f"Attempting to load plugin: {name}")
            logger.info(f"Currently discovered plugins: {list(self.discovery._discovered_plugins.keys())}")
            
            # Check plugin info
            info = self.discovery._discovered_plugins.get(name)
            if not info:
                logger.error(f"Plugin {name} not found in discovered plugins")
                raise PluginError(f"Plugin {name} not found")
                
            for dep in info.dependencies:
                if dep not in self.plugins:
                    self.load_plugin(dep)
            
            # Load plugin
            info = self.discovery._discovered_plugins[name]
            plugin_class = info.plugin_class
            if plugin_class:
                plugin = plugin_class()
                self.plugins[name] = plugin
            else:
                raise PluginError(f"No plugin class found for {name}")
            
            # Update status
            status = self.plugin_status.get(name)
            if status:
                status.state = PluginState.LOADED
                for dep in info.dependencies:
                    status.dependencies[dep] = True
            
            return plugin
            
        except Exception as e:
            if name in self.plugin_status:
                self.plugin_status[name].state = PluginState.ERROR
                self.plugin_status[name].error = str(e)
            raise PluginError(f"Failed to load plugin {name}: {e}")
    
    def initialize_plugin(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize plugin
        
        Args:
            name: Plugin name
            config: Plugin configuration
        """
        plugin = self.plugins.get(name)
        if not plugin:
            raise PluginError(f"Plugin {name} not loaded")
            
        try:
            if config:
                plugin.configure(config)
                
            status = self.plugin_status[name]
            status.state = PluginState.INITIALIZED
            status.config = config
            
        except Exception as e:
            self.plugin_status[name].state = PluginState.ERROR
            self.plugin_status[name].error = str(e)
            raise PluginError(f"Failed to initialize plugin {name}: {e}")
    
    def start_plugin(self, name: str) -> None:
        """Start plugin
        
        Args:
            name: Plugin name
        """
        status = self.plugin_status.get(name)
        if not status or status.state != PluginState.INITIALIZED:
            raise PluginError(f"Plugin {name} not initialized")
        
        try:
            # Call start method if available
            plugin = self.plugins[name]
            if hasattr(plugin, 'start') and callable(getattr(plugin, 'start')):
                plugin.start()
            
            status.state = PluginState.RUNNING
            
        except Exception as e:
            status.state = PluginState.ERROR
            status.error = str(e)
            raise PluginError(f"Failed to start plugin {name}: {e}")
    
    def stop_plugin(self, name: str) -> None:
        """Stop plugin
        
        Args:
            name: Plugin name
        """
        status = self.plugin_status.get(name)
        if not status or status.state != PluginState.RUNNING:
            raise PluginError(f"Plugin {name} not running")
        
        try:
            # Call stop method if available
            plugin = self.plugins[name]
            if hasattr(plugin, 'stop') and callable(getattr(plugin, 'stop')):
                plugin.stop()
            
            status.state = PluginState.STOPPED
            
        except Exception as e:
            status.state = PluginState.ERROR
            status.error = str(e)
            raise PluginError(f"Failed to stop plugin {name}: {e}")
    
    def unload_plugin(self, name: str) -> None:
        """Unload plugin
        
        Args:
            name: Plugin name
        """
        if name not in self.plugins:
            return
            
        # Stop plugin first
        status = self.plugin_status.get(name)
        if status and status.state == PluginState.RUNNING:
            self.stop_plugin(name)
        
        # Unload plugin
        self.discovery.unload_plugin(name)
        del self.plugins[name]
        if name in self.plugin_status:
            del self.plugin_status[name]
    
    def get_plugin(self, name: str) -> Optional[IPlugin]:
        """Get plugin instance
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin instance or None
        """
        return self.plugins.get(name)
    
    def get_plugin_status(self, name: str) -> Optional[PluginStatus]:
        """Get plugin status
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin status or None
        """
        return self.plugin_status.get(name)
    
    def list_plugins(self) -> List[str]:
        """List all loaded plugins
        
        Returns:
            List of plugin names
        """
        return list(self.plugins.keys())

class PluginManager(BasePluginManager):
    """Plugin manager implementation"""
    
    def __init__(self, plugin_paths: Optional[List[str]] = None):
        super().__init__(plugin_paths)
        self.registry = PluginRegistry()
        self._loaded_plugins: Dict[str, BasePlugin] = {}
        self._entry_points_cache: Optional[Dict[str, Any]] = None
    
    def discover_plugins(self) -> Dict[str, PluginInfo]:
        """Discover available plugins"""
        discovered = super().discover_plugins()
        self._entry_points_cache = None  # Clear cache to force rediscovery
        return discovered

    def _discover_plugin_entry_point(self, plugin_name: str) -> Optional[Any]:
        """Discover plugin entry point
        
        Args:
            plugin_name: Plugin name
            
        Returns:
            Entry point instance or None
        """
        entry_points = self._discover_all_entry_points()
        return entry_points.get(plugin_name)
    
    def _discover_all_entry_points(self) -> Dict[str, Any]:
        """Discover all plugin entry points
        
        Returns:
            Dictionary of entry points
        """
        if self._entry_points_cache is not None:
            return self._entry_points_cache
        
        entry_points = {}
        try:
            for entry_point in pkg_resources.iter_entry_points('ascend.plugins'):
                entry_points[entry_point.name] = entry_point
        except Exception as e:
            # Use fallback discovery if pkg_resources is not available
            entry_points = self._discover_entry_points_fallback()
        
        self._entry_points_cache = entry_points
        return entry_points
    
    def _discover_entry_points_fallback(self) -> Dict[str, Any]:
        """Fallback entry point discovery mechanism
        
        Returns:
            Dictionary of entry points
        """
        # Implement custom plugin discovery logic here
        # For example: scan specific directories, read config files, etc.
        return {}
    
    def __contains__(self, plugin_name: str) -> bool:
        """Check if plugin is loaded
        
        Args:
            plugin_name: Plugin name
            
        Returns:
            True if loaded, False otherwise
        """
        return plugin_name in self._loaded_plugins
    
    def __len__(self) -> int:
        """Get number of loaded plugins
        
        Returns:
            Number of plugins
        """
        return len(self._loaded_plugins)
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup all plugins"""
        self.clear_all_plugins()
    
    def clear_all_plugins(self) -> None:
        """Clear all loaded plugins"""
        for plugin_name in list(self._loaded_plugins.keys()):
            try:
                self.unload_plugin(plugin_name)
            except PluginError:
                # Ignore unload errors and continue with other plugins
                continue


# Create default plugin manager instance
default_manager = PluginManager()