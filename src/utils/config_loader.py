"""
Configuration loader for enterprise financial data processor
"""
import yaml
import os
from typing import Dict, Any

class ConfigLoader:
    """Configuration loader with dynamic category management"""
    
    def __init__(self, config_path='config/config.yaml', categories_path='config/categories.yaml', db_manager=None):
        self.config_path = config_path
        self.categories_path = categories_path
        self.db_manager = db_manager
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
        """Load categories from template file and merge with database categories"""
        # Start with template categories from YAML
        template_categories = self._load_template_categories()
        
        # Extract categories from database if available
        database_categories = self._extract_database_categories()
        
        # Merge template and database categories (database categories take precedence)
        merged_categories = self._merge_categories(template_categories, database_categories)
        
        # Update categories in YAML file if database categories were found
        if database_categories and merged_categories != template_categories:
            self._update_categories_file(merged_categories)
        
        self._config['categories'] = merged_categories

    def _load_template_categories(self):
        """Load template categories from YAML file or defaults"""
        if os.path.exists(self.categories_path):
            # Load from separate categories file
            with open(self.categories_path, 'r') as file:
                categories_config = yaml.safe_load(file) or {}
                return categories_config.get('categories', [])
        else:
            # Return default template categories
            return [
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

    def _extract_database_categories(self):
        """Extract unique categories from database (both enum and transaction categories)"""
        if not self.db_manager:
            return []
        
        session = self.db_manager.get_session()
        categories = set()
        
        try:
            # Extract categories from TransactionEnum table
            TransactionEnum = self.db_manager.models['TransactionEnum']
            enum_categories = session.query(TransactionEnum.category).distinct().all()
            for (category,) in enum_categories:
                if category and category.strip():
                    categories.add(category.strip().lower())
            
            # Extract categories from Transaction table (transaction_category field)
            Transaction = self.db_manager.models['Transaction']
            transaction_categories = session.query(Transaction.transaction_category).distinct().all()
            for (category,) in transaction_categories:
                if category and category.strip():
                    categories.add(category.strip().lower())
            
            # Convert to list of dictionaries
            return [{'name': category} for category in sorted(categories)]
            
        except Exception as e:
            print(f"⚠️  Warning: Could not extract categories from database: {e}")
            return []
        finally:
            session.close()

    def _merge_categories(self, template_categories, database_categories):
        """Merge template and database categories, keeping template order first"""
        # Create a set of category names for deduplication
        all_category_names = set()
        merged_categories = []
        
        # Add template categories first (maintain original order and numbering)
        for category in template_categories:
            category_name = category['name'].lower()
            if category_name not in all_category_names:
                all_category_names.add(category_name)
                merged_categories.append(category)
        
        # Add new database categories that don't exist in template (at the end)
        for category in database_categories:
            category_name = category['name'].lower()
            if category_name not in all_category_names:
                all_category_names.add(category_name)
                merged_categories.append(category)
        
        return merged_categories

    def _update_categories_file(self, categories):
        """Update the categories YAML file with merged categories"""
        try:
            categories_config = {'categories': categories}
            
            # Ensure config directory exists
            os.makedirs(os.path.dirname(self.categories_path), exist_ok=True)
            
            with open(self.categories_path, 'w') as file:
                yaml.dump(categories_config, file, default_flow_style=False, sort_keys=False)
            
            print(f"📂 Updated categories file with {len(categories)} categories (including database categories)")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not update categories file: {e}")
    
    def add_category(self, category_name: str):
        """Add a new category while maintaining proper order (template first, custom last)"""
        category_name = category_name.lower().strip()
        
        # Check if category already exists
        existing_categories = [cat['name'].lower() for cat in self._config.get('categories', [])]
        if category_name in existing_categories:
            return  # Category already exists
        
        # Reload template categories to ensure we have the base list
        template_categories = self._load_template_categories()
        template_names = [cat['name'].lower() for cat in template_categories]
        
        # Build new categories list: template first, then existing custom, then new custom
        current_categories = self._config.get('categories', [])
        new_categories = []
        
        # Add template categories in their original order
        for template_cat in template_categories:
            new_categories.append(template_cat)
        
        # Add existing custom categories that aren't in template
        for current_cat in current_categories:
            if current_cat['name'].lower() not in template_names:
                new_categories.append(current_cat)
        
        # Add the new category at the end
        new_categories.append({'name': category_name})
        
        # Save and update
        self.save_categories(new_categories)

    def save_categories(self, categories: list):
        """Save categories to the separate categories file and refresh config"""
        categories_config = {'categories': categories}
        
        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.categories_path), exist_ok=True)
        
        with open(self.categories_path, 'w') as file:
            yaml.dump(categories_config, file, default_flow_style=False, sort_keys=False)
        
        # Update in-memory config
        self._config['categories'] = categories
        
        # Re-merge with database categories to ensure we have the latest
        if self.db_manager:
            self._load_categories() 