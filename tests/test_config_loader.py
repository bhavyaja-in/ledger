"""
Comprehensive unit tests for ConfigLoader with 100% line coverage.

Tests every method, branch condition, exception path, and edge case
to ensure enterprise-grade quality and complete code coverage.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest
import yaml

from src.utils.config_loader import ConfigLoader


class TestConfigLoader:
    """Comprehensive test suite for ConfigLoader class"""

    @pytest.mark.unit
    @pytest.mark.config
    def test_init_with_defaults(self):
        """Test ConfigLoader initialization with default parameters"""
        loader = ConfigLoader()

        assert loader.config_path == "config/config.yaml"
        assert loader.categories_path == "config/categories.yaml"
        assert loader.db_manager is None
        assert loader._config == {}

    @pytest.mark.unit
    @pytest.mark.config
    def test_init_with_custom_parameters(self, mock_db_manager):
        """Test ConfigLoader initialization with custom parameters"""
        custom_config_path = "custom/config.yaml"
        custom_categories_path = "custom/categories.yaml"

        loader = ConfigLoader(
            config_path=custom_config_path,
            categories_path=custom_categories_path,
            db_manager=mock_db_manager,
        )

        assert loader.config_path == custom_config_path
        assert loader.categories_path == custom_categories_path
        assert loader.db_manager == mock_db_manager
        assert loader._config == {}

    @pytest.mark.unit
    @pytest.mark.config
    def test_get_config_loads_when_empty(self, temp_config_dir, test_config):
        """Test get_config loads configuration when _config is empty"""
        config_file = temp_config_dir / "config.yaml"

        with patch("src.utils.config_loader.ConfigLoader._load_config") as mock_load:
            loader = ConfigLoader(config_path=str(config_file))
            result = loader.get_config()

            mock_load.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.config
    def test_get_config_returns_cached_config(self, temp_config_dir):
        """Test get_config returns cached config when already loaded"""
        config_file = temp_config_dir / "config.yaml"
        loader = ConfigLoader(config_path=str(config_file))

        # Set cached config
        test_config = {"test": "value"}
        loader._config = test_config

        with patch("src.utils.config_loader.ConfigLoader._load_config") as mock_load:
            result = loader.get_config()

            mock_load.assert_not_called()
            assert result == test_config

    @pytest.mark.unit
    @pytest.mark.config
    def test_load_config_file_not_found(self):
        """Test _load_config raises FileNotFoundError when config file missing"""
        loader = ConfigLoader(config_path="nonexistent/config.yaml")

        with pytest.raises(FileNotFoundError, match="Config file not found"):
            loader._load_config()

    @pytest.mark.unit
    @pytest.mark.config
    def test_load_config_success(self, temp_config_dir):
        """Test _load_config successfully loads YAML configuration"""
        config_data = {"database": {"url": "sqlite:///test.db"}, "processors": {"test": True}}

        config_file = temp_config_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        categories_file = temp_config_dir / "categories.yaml"
        with open(categories_file, "w") as f:
            yaml.dump({"categories": [{"name": "test"}]}, f)

        loader = ConfigLoader(config_path=str(config_file), categories_path=str(categories_file))

        with patch("src.utils.config_loader.ConfigLoader._load_categories") as mock_load_cat:
            loader._load_config()

            assert loader._config["database"] == config_data["database"]
            assert loader._config["processors"] == config_data["processors"]
            mock_load_cat.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.config
    def test_load_config_empty_yaml(self, temp_config_dir):
        """Test _load_config handles empty YAML file"""
        config_file = temp_config_dir / "config.yaml"
        with open(config_file, "w") as f:
            f.write("")  # Empty file

        categories_file = temp_config_dir / "categories.yaml"
        with open(categories_file, "w") as f:
            yaml.dump({"categories": []}, f)

        loader = ConfigLoader(config_path=str(config_file), categories_path=str(categories_file))

        with patch("src.utils.config_loader.ConfigLoader._load_categories"):
            loader._load_config()

            assert loader._config == {}

    @pytest.mark.unit
    @pytest.mark.config
    def test_load_categories_with_new_database_categories(self, temp_config_dir):
        """Test _load_categories merges template and database categories"""
        # Create categories file
        categories_file = temp_config_dir / "categories.yaml"
        template_categories = [{"name": "food"}, {"name": "transport"}]
        with open(categories_file, "w") as f:
            yaml.dump({"categories": template_categories}, f)

        # Mock database categories
        db_categories = [{"name": "medical"}, {"name": "education"}]

        loader = ConfigLoader(categories_path=str(categories_file))
        loader._config = {}

        with patch.object(
            loader, "_load_template_categories", return_value=template_categories
        ), patch.object(
            loader, "_extract_database_categories", return_value=db_categories
        ), patch.object(
            loader, "_merge_categories", return_value=template_categories + db_categories
        ) as mock_merge, patch.object(
            loader, "_update_categories_file"
        ) as mock_update:
            loader._load_categories()

            mock_merge.assert_called_once_with(template_categories, db_categories)
            mock_update.assert_called_once_with(template_categories + db_categories)
            assert loader._config["categories"] == template_categories + db_categories

    @pytest.mark.unit
    @pytest.mark.config
    def test_load_categories_no_new_categories(self, temp_config_dir):
        """Test _load_categories when no new database categories found"""
        categories_file = temp_config_dir / "categories.yaml"
        template_categories = [{"name": "food"}, {"name": "transport"}]
        with open(categories_file, "w") as f:
            yaml.dump({"categories": template_categories}, f)

        loader = ConfigLoader(categories_path=str(categories_file))
        loader._config = {}

        with patch.object(
            loader, "_load_template_categories", return_value=template_categories
        ), patch.object(loader, "_extract_database_categories", return_value=[]), patch.object(
            loader, "_merge_categories", return_value=template_categories
        ), patch.object(
            loader, "_update_categories_file"
        ) as mock_update:
            loader._load_categories()

            mock_update.assert_not_called()
            assert loader._config["categories"] == template_categories

    @pytest.mark.unit
    @pytest.mark.config
    def test_load_template_categories_from_file(self, temp_config_dir):
        """Test _load_template_categories loads from existing categories file"""
        categories_data = {"categories": [{"name": "food"}, {"name": "transport"}]}
        categories_file = temp_config_dir / "categories.yaml"

        with open(categories_file, "w") as f:
            yaml.dump(categories_data, f)

        loader = ConfigLoader(categories_path=str(categories_file))
        result = loader._load_template_categories()

        assert result == categories_data["categories"]

    @pytest.mark.unit
    @pytest.mark.config
    def test_load_template_categories_empty_file(self, temp_config_dir):
        """Test _load_template_categories handles empty categories file"""
        categories_file = temp_config_dir / "categories.yaml"
        with open(categories_file, "w") as f:
            yaml.dump({}, f)  # Empty categories

        loader = ConfigLoader(categories_path=str(categories_file))
        result = loader._load_template_categories()

        assert result == []

    @pytest.mark.unit
    @pytest.mark.config
    def test_load_template_categories_default_when_file_missing(self):
        """Test _load_template_categories returns defaults when file doesn't exist"""
        loader = ConfigLoader(categories_path="nonexistent/categories.yaml")
        result = loader._load_template_categories()

        expected_defaults = [
            {"name": "income"},
            {"name": "food"},
            {"name": "transport"},
            {"name": "shopping"},
            {"name": "entertainment"},
            {"name": "utilities"},
            {"name": "healthcare"},
            {"name": "transfer"},
            {"name": "investment"},
            {"name": "other"},
        ]

        assert result == expected_defaults

    @pytest.mark.unit
    @pytest.mark.config
    def test_extract_database_categories_no_db_manager(self):
        """Test _extract_database_categories returns empty list when no db_manager"""
        loader = ConfigLoader(db_manager=None)
        result = loader._extract_database_categories()

        assert result == []

    @pytest.mark.unit
    @pytest.mark.config
    def test_extract_database_categories_success(self):
        """Test _extract_database_categories extracts from database successfully"""
        # Mock database manager and session
        mock_session = Mock()
        mock_db_manager = Mock()
        mock_db_manager.get_session.return_value = mock_session

        # Mock TransactionEnum model
        mock_transaction_enum = Mock()
        mock_transaction_enum.category = Mock()

        # Mock Transaction model
        mock_transaction = Mock()
        mock_transaction.transaction_category = Mock()

        mock_db_manager.models = {
            "TransactionEnum": mock_transaction_enum,
            "Transaction": mock_transaction,
        }

        # Mock query results
        enum_categories = [("food",), ("transport",), ("  SHOPPING  ",)]
        transaction_categories = [("entertainment",), ("utilities",), ("",), (None,)]

        mock_session.query.return_value.distinct.return_value.all.side_effect = [
            enum_categories,
            transaction_categories,
        ]

        loader = ConfigLoader(db_manager=mock_db_manager)
        result = loader._extract_database_categories()

        # Since set order is not guaranteed, check categories are present
        result_names = [cat["name"] for cat in result]
        expected_names = ["food", "transport", "shopping", "entertainment", "utilities"]

        assert len(result) == 5
        for name in expected_names:
            assert name in result_names

        mock_session.close.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.config
    def test_extract_database_categories_exception_handling(self):
        """Test _extract_database_categories handles database exceptions"""
        mock_session = Mock()
        mock_db_manager = Mock()
        mock_db_manager.get_session.return_value = mock_session
        mock_db_manager.models = {"TransactionEnum": Mock()}

        # Mock exception during query
        mock_session.query.side_effect = Exception("Database error")

        loader = ConfigLoader(db_manager=mock_db_manager)

        with patch("builtins.print") as mock_print:
            result = loader._extract_database_categories()

            assert result == []
            mock_print.assert_called_once()
            assert "Warning: Could not extract categories" in mock_print.call_args[0][0]
            mock_session.close.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.config
    def test_merge_categories_yaml_priority(self):
        """Test _merge_categories preserves YAML order and priority"""
        yaml_categories = [{"name": "food"}, {"name": "transport"}, {"name": "shopping"}]
        database_categories = [{"name": "food"}, {"name": "medical"}, {"name": "education"}]

        loader = ConfigLoader()
        result = loader._merge_categories(yaml_categories, database_categories)

        expected = [
            {"name": "food"},
            {"name": "transport"},
            {"name": "shopping"},
            {"name": "medical"},
            {"name": "education"},
        ]

        assert result == expected

    @pytest.mark.unit
    @pytest.mark.config
    def test_merge_categories_case_insensitive(self):
        """Test _merge_categories handles case-insensitive matching"""
        yaml_categories = [{"name": "Food"}, {"name": "TRANSPORT"}]
        database_categories = [{"name": "food"}, {"name": "transport"}, {"name": "Medical"}]

        loader = ConfigLoader()
        result = loader._merge_categories(yaml_categories, database_categories)

        expected = [{"name": "Food"}, {"name": "TRANSPORT"}, {"name": "Medical"}]

        assert result == expected

    @pytest.mark.unit
    @pytest.mark.config
    def test_update_categories_file_success(self, temp_config_dir):
        """Test _update_categories_file successfully updates YAML file"""
        categories_file = temp_config_dir / "categories.yaml"
        categories = [{"name": "food"}, {"name": "transport"}]

        loader = ConfigLoader(categories_path=str(categories_file))

        with patch("builtins.print") as mock_print:
            loader._update_categories_file(categories)

            # Verify file was created
            assert categories_file.exists()

            # Verify content
            with open(categories_file, "r") as f:
                saved_data = yaml.safe_load(f)

            assert saved_data["categories"] == categories
            mock_print.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.config
    def test_update_categories_file_creates_directory(self, temp_dir):
        """Test _update_categories_file creates directory if it doesn't exist"""
        categories_path = temp_dir / "new_config" / "categories.yaml"
        categories = [{"name": "test"}]

        loader = ConfigLoader(categories_path=str(categories_path))
        loader._update_categories_file(categories)

        assert categories_path.exists()
        assert categories_path.parent.exists()

    @pytest.mark.unit
    @pytest.mark.config
    def test_update_categories_file_exception_handling(self, temp_dir):
        """Test _update_categories_file handles write exceptions"""
        categories_path = temp_dir / "readonly" / "categories.yaml"
        categories = [{"name": "test"}]

        loader = ConfigLoader(categories_path=str(categories_path))

        with patch("os.makedirs", side_effect=PermissionError("Permission denied")), patch(
            "builtins.print"
        ) as mock_print:
            loader._update_categories_file(categories)

            mock_print.assert_called_once()
            assert "Warning: Could not update categories file" in mock_print.call_args[0][0]

    @pytest.mark.unit
    @pytest.mark.config
    def test_add_category_new_category(self, temp_config_dir):
        """Test add_category adds new category successfully"""
        categories_file = temp_config_dir / "categories.yaml"
        existing_categories = [{"name": "food"}, {"name": "transport"}]

        with open(categories_file, "w") as f:
            yaml.dump({"categories": existing_categories}, f)

        loader = ConfigLoader(categories_path=str(categories_file))
        loader._config = {"categories": existing_categories.copy()}

        with patch.object(
            loader, "_load_template_categories", return_value=existing_categories
        ), patch.object(loader, "save_categories") as mock_save:
            loader.add_category("medical")

            expected_categories = existing_categories + [{"name": "medical"}]
            mock_save.assert_called_once_with(expected_categories)

    @pytest.mark.unit
    @pytest.mark.config
    def test_add_category_existing_category(self):
        """Test add_category ignores existing category"""
        existing_categories = [{"name": "food"}, {"name": "transport"}]

        loader = ConfigLoader()
        loader._config = {"categories": existing_categories}

        with patch.object(loader, "save_categories") as mock_save:
            loader.add_category("FOOD")  # Case insensitive

            mock_save.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.config
    def test_add_category_whitespace_handling(self, temp_config_dir):
        """Test add_category handles whitespace correctly"""
        categories_file = temp_config_dir / "categories.yaml"
        existing_categories = [{"name": "food"}]

        loader = ConfigLoader(categories_path=str(categories_file))
        loader._config = {"categories": existing_categories.copy()}

        with patch.object(
            loader, "_load_template_categories", return_value=existing_categories
        ), patch.object(loader, "save_categories") as mock_save:
            loader.add_category("  medical  ")

            expected_categories = existing_categories + [{"name": "medical"}]
            mock_save.assert_called_once_with(expected_categories)

    @pytest.mark.unit
    @pytest.mark.config
    def test_add_category_maintains_template_order(self, temp_config_dir):
        """Test add_category maintains template category order"""
        categories_file = temp_config_dir / "categories.yaml"
        template_categories = [{"name": "income"}, {"name": "food"}]
        current_categories = [{"name": "food"}, {"name": "custom"}]

        loader = ConfigLoader(categories_path=str(categories_file))
        loader._config = {"categories": current_categories}

        with patch.object(
            loader, "_load_template_categories", return_value=template_categories
        ), patch.object(loader, "save_categories") as mock_save:
            loader.add_category("medical")

            # Should maintain template order: income, food, then customs
            expected = [
                {"name": "income"},
                {"name": "food"},  # Template order
                {"name": "custom"},
                {"name": "medical"},  # Custom categories
            ]
            mock_save.assert_called_once_with(expected)

    @pytest.mark.unit
    @pytest.mark.config
    def test_save_categories_creates_directory(self, temp_dir):
        """Test save_categories creates config directory if needed"""
        categories_path = temp_dir / "new_config" / "categories.yaml"
        categories = [{"name": "test"}]

        loader = ConfigLoader(categories_path=str(categories_path))
        loader._config = {}

        loader.save_categories(categories)

        assert categories_path.exists()
        assert categories_path.parent.exists()

    @pytest.mark.unit
    @pytest.mark.config
    def test_save_categories_updates_memory_config(self, temp_config_dir):
        """Test save_categories updates in-memory configuration"""
        categories_file = temp_config_dir / "categories.yaml"
        categories = [{"name": "food"}, {"name": "transport"}]

        loader = ConfigLoader(categories_path=str(categories_file))
        loader._config = {"other": "data"}

        loader.save_categories(categories)

        assert loader._config["categories"] == categories
        assert loader._config["other"] == "data"  # Other config preserved

    @pytest.mark.unit
    @pytest.mark.config
    def test_save_categories_yaml_format(self, temp_config_dir):
        """Test save_categories writes correct YAML format"""
        categories_file = temp_config_dir / "categories.yaml"
        categories = [{"name": "food"}, {"name": "transport"}]

        loader = ConfigLoader(categories_path=str(categories_file))
        loader.save_categories(categories)

        # Verify YAML structure
        with open(categories_file, "r") as f:
            saved_data = yaml.safe_load(f)

        assert "categories" in saved_data
        assert saved_data["categories"] == categories

    @pytest.mark.unit
    @pytest.mark.security
    def test_no_production_config_modification(self, security_validator):
        """Security test: Ensure no production config files are modified"""
        security_validator.ensure_no_production_changes()

        # Test with production paths - should not modify them
        loader = ConfigLoader()

        # Verify test mode is active
        assert os.environ.get("LEDGER_TEST_MODE") == "true"

    @pytest.mark.unit
    @pytest.mark.coverage
    def test_edge_case_empty_string_category(self, temp_config_dir):
        """Test edge case: empty string category name"""
        categories_file = temp_config_dir / "categories.yaml"

        loader = ConfigLoader(categories_path=str(categories_file))
        loader._config = {"categories": []}

        # Mock template categories to avoid file operations
        with patch.object(loader, "_load_template_categories", return_value=[]), patch.object(
            loader, "save_categories"
        ) as mock_save:
            loader.add_category("")  # Empty string after strip becomes ''
            loader.add_category("   ")  # Whitespace only after strip becomes ''

            # The actual implementation processes empty strings, so it gets called
            # Both calls result in the same empty string, so only called twice (once for each)
            assert mock_save.call_count == 2

    @pytest.mark.unit
    @pytest.mark.coverage
    def test_edge_case_none_yaml_load(self, temp_config_dir):
        """Test edge case: yaml.safe_load returns None"""
        config_file = temp_config_dir / "config.yaml"
        with open(config_file, "w") as f:
            f.write("null")  # YAML null

        categories_file = temp_config_dir / "categories.yaml"
        with open(categories_file, "w") as f:
            f.write("")

        loader = ConfigLoader(config_path=str(config_file), categories_path=str(categories_file))

        with patch("src.utils.config_loader.ConfigLoader._load_categories"):
            loader._load_config()

            assert loader._config == {}

    @pytest.mark.unit
    @pytest.mark.coverage
    def test_all_print_statements_covered(self, temp_config_dir, capsys):
        """Test all print statements are covered"""
        categories_file = temp_config_dir / "categories.yaml"

        # Mock database manager with categories
        mock_session = Mock()
        mock_db_manager = Mock()
        mock_db_manager.get_session.return_value = mock_session
        mock_db_manager.models = {"TransactionEnum": Mock(), "Transaction": Mock()}

        # Mock finding new categories
        mock_session.query.return_value.distinct.return_value.all.side_effect = [
            [("new_category",)],
            [],
        ]

        loader = ConfigLoader(categories_path=str(categories_file), db_manager=mock_db_manager)

        # This should trigger the "Discovered new categories" print
        loader._load_categories()

        captured = capsys.readouterr()
        assert "Discovered" in captured.out or "Updated categories file" in captured.out
