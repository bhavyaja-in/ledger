"""
Configuration loader for enterprise financial data processor
"""
import yaml
import os
from typing import Dict, Any

class ConfigLoader:
    """Configuration loader"""
    
    def __init__(self, config_path='config/config.yaml', categories_path='config/categories.yaml'):
        self.config_path = config_path
        self.categories_path = categories_path
        self._config: Dict[str, Any] = {}
    
    def get_config(self) -> Dict[str, Any]:
        """Load and return configuration"""
        if not self._config:
            self._load_config()
        return self._config
    
    def _load_config(self):
        """Load configuration from YAML file"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as file:
            self._config = yaml.safe_load(file) or {}
        
        # Load categories from separate file
        self._load_categories()
    
    def _load_categories(self):
        """Load categories from separate file or use defaults"""
        if os.path.exists(self.categories_path):
            # Load from separate categories file
            with open(self.categories_path, 'r') as file:
                categories_config = yaml.safe_load(file) or {}
                self._config['categories'] = categories_config.get('categories', [])
        elif 'categories' not in self._config:
            # Fallback to default categories if no separate file and no categories in main config
            self._config['categories'] = [
                {'name': 'income'},
                {'name': 'food'},
                {'name': 'transport'},
                {'name': 'shopping'},
                {'name': 'entertainment'},
                {'name': 'utilities'},
                {'name': 'healthcare'},
                {'name': 'transfer'},
                {'name': 'investment'},
                {'name': 'other'}
            ]
    
    def save_categories(self, categories: list):
        """Save categories to the separate categories file"""
        categories_config = {'categories': categories}
        
        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.categories_path), exist_ok=True)
        
        with open(self.categories_path, 'w') as file:
            yaml.dump(categories_config, file, default_flow_style=False, sort_keys=False)
        
        # Update in-memory config
        self._config['categories'] = categories 