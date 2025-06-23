"""
Configuration loader for enterprise financial data processor
"""
import yaml
import os
from typing import Dict, Any

class ConfigLoader:
    """Configuration loader"""
    
    def __init__(self, config_path='config/config.yaml'):
        self.config_path = config_path
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