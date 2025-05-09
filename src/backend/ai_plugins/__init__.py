# src/backend/ai_plugins/__init__.py
import pkgutil
import importlib
from .base import AIPlugin

# Global registry for discovered AI plugins
AVAILABLE_PLUGINS: dict[str, AIPlugin] = {}

def load_plugins():
    """Discovers and loads all AI plugins from the ai_plugins directory."""
    if AVAILABLE_PLUGINS: # Avoid reloading if already populated
        return

    plugin_module_path = __path__
    plugin_package_name = __name__

    for _, module_name, _ in pkgutil.iter_modules(plugin_module_path):
        if module_name == "base" or module_name == "__init__": # Skip base and self
            continue
        try:
            module = importlib.import_module(f".{module_name}", package=plugin_package_name)
            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)
                if isinstance(attribute, type) and issubclass(attribute, AIPlugin) and attribute is not AIPlugin:
                    try:
                        plugin_instance = attribute() # Instantiate the plugin
                        plugin_name = plugin_instance.get_name()
                        if plugin_name in AVAILABLE_PLUGINS:
                            print(f"Warning: Duplicate AI plugin name '{plugin_name}' found. Overwriting.")
                        AVAILABLE_PLUGINS[plugin_name] = plugin_instance
                        print(f"Successfully loaded AI plugin: {plugin_name}")
                    except Exception as e:
                        print(f"Error instantiating AI plugin {attribute_name} from {module_name}: {e}")
        except Exception as e:
            print(f"Error loading AI plugin module {module_name}: {e}")

def get_plugin(name: str) -> AIPlugin | None:
    """Retrieves a loaded AI plugin by its name."""
    return AVAILABLE_PLUGINS.get(name)

def get_available_plugins() -> list[dict[str, str]]:
    """Returns a list of available plugins with their names and descriptions."""
    return [
        {"name": plugin.get_name(), "description": plugin.get_description()}
        for plugin in AVAILABLE_PLUGINS.values()
    ]

# Automatically load plugins when this package is imported
# load_plugins() # Call this explicitly when the app starts instead
