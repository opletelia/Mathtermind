from unittest.mock import MagicMock, patch

import pytest

from src.services.cs_tools_service import CSToolsService


@pytest.fixture
def service():
    """Create a test instance of CSToolsService with mocked dependencies."""
    service = CSToolsService()
    service.tracking_service = MagicMock()
    service.db = MagicMock()
    return service


def test_validate_code_syntax(cs_tools_service):
    """Test code syntax validation."""
    result = cs_tools_service.validate_code_syntax("print('Hello, world!')", "python")
    assert result["is_valid"] is True
    assert result["success"] is True

    result = cs_tools_service.validate_code_syntax("print('Hello, world!'", "python")
    assert result["is_valid"] is False
    assert result["success"] is True
    assert "SyntaxError" in result["error"]

    result = cs_tools_service.validate_code_syntax(
        "console.log('Hello, world!');", "javascript"
    )
    assert result["is_valid"] is True
    assert result["success"] is True

    result = cs_tools_service.validate_code_syntax(
        "console.log('Hello, world!';", "javascript"
    )
    assert result["is_valid"] is False
    assert result["success"] is True


def test_check_code_output(cs_tools_service):
    """Test code output checking against expected output."""
    code = "print('Hello, world!')"
    expected_output = "Hello, world!"
    result = cs_tools_service.check_code_output(code, expected_output, "python")
    assert result["is_correct"] is True
    assert result["success"] is True

    code = "print('Hi, world!')"
    expected_output = "Hello, world!"
    result = cs_tools_service.check_code_output(code, expected_output, "python")
    assert result["is_correct"] is False
    assert result["success"] is True


def test_validate_code_against_testcases(cs_tools_service):
    """Test validation of code against multiple test cases."""
    code = "def add(a, b): return a + b"
    test_cases = [
        {"input": {"a": 1, "b": 2}, "expected_output": 3},
        {"input": {"a": -1, "b": 5}, "expected_output": 4},
        {"input": {"a": 0, "b": 0}, "expected_output": 0},
    ]
    result = cs_tools_service.validate_code_against_testcases(
        code, test_cases, "python"
    )
    assert result["all_passed"] is True
    assert result["passed_count"] == 3
    assert result["success"] is True

    code = "def add(a, b): return a - b"  # Subtraction instead of addition
    result = cs_tools_service.validate_code_against_testcases(
        code, test_cases, "python"
    )
    assert result["all_passed"] is False
    assert result["success"] is True


def test_prepare_algorithm_visualization(cs_tools_service):
    """Test preparation of algorithm visualization data."""
    algorithm = "bubble_sort"
    data = [5, 3, 8, 4, 2]
    result = cs_tools_service.prepare_algorithm_visualization(algorithm, data)
    assert result["success"] is True
    assert "steps" in result
    assert len(result["steps"]) > 0


def test_prepare_data_structure_visualization(cs_tools_service):
    """Test preparation of data structure visualization."""
    structure = "binary_tree"
    data = [10, 5, 15, 3, 7, 12, 20]
    result = cs_tools_service.prepare_data_structure_visualization(structure, data)
    assert result["success"] is True
    assert "visualization_data" in result


def test_tracking_service_integration(cs_tools_service):
    """Test that user tracking is called when a user ID is provided."""
    cs_tools_service.validate_code_syntax(
        "print('Hello, world!')", "python", user_id="test_user"
    )

    cs_tools_service.tracking_service.track_tool_usage.assert_called_once_with(
        user_id="test_user",
        tool_type="code_validator",
        action="validate_code_syntax",
        data={"code": "print('Hello, world!')", "language": "python"},
    )
