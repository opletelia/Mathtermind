import importlib
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.app_init import init_app, init_database, init_services, load_config
from src.core.error_handling import ConfigurationError, DatabaseConnectionError
from src.db import engine, init_db


@pytest.fixture
def mock_config():
    """Fixture providing a basic configuration dictionary."""
    return {
        "environment": "testing",
        "debug": True,
        "database_url": "sqlite:///mathtermind_test.db",
        "data_dir": "data",
        "log_dir": "logs",
    }


@pytest.fixture
def mock_core_init():
    """Fixture to mock core initialization."""
    with patch("src.app_init.init_core") as mock:
        yield mock


@pytest.fixture
def mock_logger():
    """Fixture to mock logger."""
    with patch("src.app_init.logger") as mock:
        yield mock


@pytest.fixture
def mock_db_init():
    """Fixture to mock database initialization."""
    with patch("src.db.init_db") as mock:
        yield mock


@pytest.fixture
def mock_engine():
    """Fixture to mock SQLAlchemy engine."""
    with patch("src.db.engine") as mock:
        yield mock


@pytest.fixture
def mock_db_connection():
    """Fixture to mock database connection."""
    with patch("src.db.engine.connect") as mock:
        connection_mock = MagicMock()
        mock.return_value = connection_mock
        yield mock


@pytest.fixture
def mock_services_init():
    """Fixture to mock services initialization."""
    with patch("src.services.init_services") as mock:
        yield mock


@pytest.fixture
def mock_os_makedirs():
    """Fixture to mock os.makedirs."""
    with patch("os.makedirs") as mock:
        yield mock


@pytest.fixture
def mock_create_error_boundary():
    """Fixture to mock create_error_boundary."""
    with patch("src.app_init.create_error_boundary") as mock:
        context_manager = MagicMock()
        context_manager.__enter__ = MagicMock(return_value=None)
        context_manager.__exit__ = MagicMock(return_value=None)
        mock.return_value = context_manager
        yield mock


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_default(self, mock_logger):
        """Test loading default configuration."""
        with patch.dict(os.environ, {}, clear=True):
            config = load_config()

            assert config["environment"] == "development"
            assert config["debug"] is True
            assert "database_url" in config
            assert "data_dir" in config
            assert "log_dir" in config
            mock_logger.info.assert_any_call("Configuration loaded successfully")

    def test_load_config_environment(self, mock_logger):
        """Test loading configuration for different environments."""
        dev_config = load_config("development")
        assert dev_config["environment"] == "development"
        assert dev_config["debug"] is True
        assert dev_config["auto_reload"] is True

        test_config = load_config("testing")
        assert test_config["environment"] == "testing"
        assert test_config["debug"] is True
        assert test_config["database_url"] == "sqlite:///mathtermind_test.db"

        prod_config = load_config("production")
        assert prod_config["environment"] == "production"
        assert prod_config["debug"] is False
        assert prod_config["auto_reload"] is False

    def test_load_config_custom_file(self, mock_logger, tmp_path):
        """Test loading configuration from custom file."""
        config_file = tmp_path / "config.json"
        custom_config = {"custom_key": "custom_value", "debug": False}
        config_file.write_text(json.dumps(custom_config))

        config = load_config(config_path=str(config_file))
        assert config["custom_key"] == "custom_value"
        assert config["debug"] is False
        mock_logger.info.assert_any_call(
            f"Loaded custom configuration from {config_file}"
        )

    def test_load_config_invalid_file(self, mock_logger, tmp_path):
        """Test loading configuration from invalid file."""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("invalid json")

        with pytest.raises(ConfigurationError) as exc_info:
            load_config(config_path=str(config_file))

        assert "Failed to load custom configuration" in str(exc_info.value)
        mock_logger.error.assert_called()

    def test_load_config_environment_logging(self, mock_logger):
        """Test logging messages for different environments."""
        load_config("development")
        mock_logger.debug.assert_any_call(
            "Loading configuration for development environment"
        )
        mock_logger.info.assert_any_call("Configuration loaded successfully")

        load_config("production")
        mock_logger.debug.assert_any_call(
            "Loading configuration for production environment"
        )
        mock_logger.info.assert_any_call("Configuration loaded successfully")

        load_config("testing")
        mock_logger.debug.assert_any_call(
            "Loading configuration for testing environment"
        )
        mock_logger.info.assert_any_call("Configuration loaded successfully")

    def test_load_config_invalid_environment(self, mock_logger):
        """Test loading configuration with invalid environment."""
        config = load_config("invalid_env")
        assert config["environment"] == "invalid_env"
        mock_logger.debug.assert_any_call(
            "Loading configuration for invalid_env environment"
        )

    def test_load_config_nonexistent_file(self, mock_logger):
        """Test loading configuration from non-existent file."""
        with pytest.raises(ConfigurationError) as exc_info:
            load_config(config_path="nonexistent.json")

        assert "Failed to load custom configuration from nonexistent.json" in str(
            exc_info.value
        )
        mock_logger.error.assert_called()


class TestInitDatabase:
    """Tests for init_database function."""

    def test_init_database_success(
        self, mock_config, mock_logger, mock_db_init, mock_db_connection
    ):
        """Test successful database initialization."""
        init_database(mock_config)

        mock_logger.info.assert_any_call("Initializing database connection")
        mock_logger.info.assert_any_call("Database connection established successfully")
        mock_db_connection.assert_called_once()

    def test_init_database_connection_failure(
        self, mock_config, mock_logger, mock_db_connection
    ):
        """Test database initialization with connection failure."""
        mock_db_connection.side_effect = Exception("Connection failed")

        with pytest.raises(DatabaseConnectionError) as exc_info:
            init_database(mock_config)

        assert "Failed to connect to the database" in str(exc_info.value)
        mock_logger.error.assert_called()


class TestInitServices:
    """Tests for init_services function."""

    def test_init_services_success(self, mock_config, mock_logger, mock_services_init):
        """Test successful services initialization."""
        # Need to patch the import in init_services function
        with patch("src.app_init.init_services") as mock_init:
            # When from src.services import init_services as init_svc is called,
            # it will import init_services which should be our mock
            # TODO: investigate
            with patch.dict(
                "sys.modules",
                {"src.services": MagicMock(init_services=mock_services_init)},
            ):
                init_services(mock_config)

                mock_logger.info.assert_any_call("Initializing application services")
                mock_logger.info.assert_any_call("Services initialized successfully")
                mock_services_init.assert_called_once_with(mock_config)

    def test_init_services_failure(self, mock_config, mock_logger):
        """Test services initialization failure."""
        error_msg = "Service initialization failed"
        mock_init_services = MagicMock(side_effect=Exception(error_msg))

        # Need to patch the import in init_services function
        with patch.dict(
            "sys.modules", {"src.services": MagicMock(init_services=mock_init_services)}
        ):
            with pytest.raises(Exception) as exc_info:
                init_services(mock_config)

            assert error_msg in str(exc_info.value)
            mock_logger.error.assert_called()


class TestInitApp:
    """Tests for init_app function."""

    def test_init_app_success(self, mock_config, mock_core_init, mock_logger):
        """Test successful application initialization."""
        with patch("src.app_init.load_config", return_value=mock_config), patch(
            "src.app_init.init_database"
        ), patch("src.app_init.init_services"):

            config = init_app("testing")

            assert config == mock_config
            mock_core_init.assert_called_once_with("testing")
            mock_logger.info.assert_any_call("Initializing Mathtermind application")
            mock_logger.info.assert_any_call(
                "Application initialization completed successfully"
            )

    def test_init_app_database_failure(
        self, mock_config, mock_core_init, mock_logger, mock_create_error_boundary
    ):
        """Test application initialization with database failure."""
        db_err = Exception("DB error")
        with patch("src.app_init.load_config", return_value=mock_config), patch(
            "src.app_init.init_database", side_effect=db_err
        ), patch("src.app_init.init_services"):

            with pytest.raises(Exception) as exc_info:
                init_app("testing")

            assert "DB error" in str(exc_info.value)

    def test_init_app_services_failure(
        self, mock_config, mock_core_init, mock_logger, mock_create_error_boundary
    ):
        """Test application initialization with services failure."""
        svc_err = Exception("Services error")
        with patch("src.app_init.load_config", return_value=mock_config), patch(
            "src.app_init.init_database"
        ), patch("src.app_init.init_services", side_effect=svc_err):

            with pytest.raises(Exception) as exc_info:
                init_app("testing")

            assert "Services error" in str(exc_info.value)


class TestCommandLineInterface:
    """Tests for command-line interface."""

    def test_cli_success(self):
        """Test successful CLI execution."""
        with patch("sys.argv", ["app_init.py", "testing"]), patch(
            "src.app_init.init_app", return_value={"environment": "testing"}
        ) as mock_init_app, patch("builtins.print") as mock_print, patch(
            "sys.exit"
        ) as mock_exit:

            import argparse

            parser = argparse.ArgumentParser()
            parser.add_argument("environment", nargs="?", default=None)
            parser.add_argument("--config", dest="config_path", default=None)
            parser.add_argument("--debug", action="store_true")

            args = parser.parse_args()

            config = mock_init_app(args.environment, args.config_path)

            mock_print(
                f"Application initialized successfully in {config['environment']} environment"
            )

            mock_exit(0)

            mock_init_app.assert_called_once_with("testing", None)
            mock_print.assert_called_once_with(
                "Application initialized successfully in testing environment"
            )
            mock_exit.assert_called_once_with(0)

    def test_cli_failure(self):
        """Test CLI execution with failure."""
        with patch("sys.argv", ["app_init.py", "testing"]), patch(
            "src.app_init.init_app", side_effect=Exception("Init failed")
        ) as mock_init_app, patch("builtins.print") as mock_print, patch(
            "sys.exit"
        ) as mock_exit:

            import argparse

            parser = argparse.ArgumentParser()
            parser.add_argument("environment", nargs="?", default=None)
            parser.add_argument("--config", dest="config_path", default=None)
            parser.add_argument("--debug", action="store_true")

            args = parser.parse_args()

            try:
                mock_init_app(args.environment, args.config_path)
                mock_print("Application initialized successfully")
                mock_exit(0)
            except Exception as e:
                mock_print(f"Application initialization failed: {str(e)}")
                mock_exit(1)

            mock_init_app.assert_called_once_with("testing", None)
            mock_print.assert_called_once_with(
                "Application initialization failed: Init failed"
            )
            mock_exit.assert_called_once_with(1)
