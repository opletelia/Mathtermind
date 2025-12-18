import pytest
from unittest.mock import MagicMock, patch
import math

from src.services.math_tools_service import MathToolsService


@pytest.fixture
def service():
    """Create a test instance of MathToolsService with mocked dependencies."""
    service = MathToolsService()
    service.tracking_service = MagicMock()
    service.db = MagicMock()
    return service


def test_validate_expression_valid(math_tools_service):
    """Test expression validation with valid expressions."""
    result = math_tools_service.validate_expression("2 + 3")
    assert result["is_valid"] is True
    assert result["success"] is True
    
    result = math_tools_service.validate_expression("3 + 4 * 2 / (1 - 5) ^ 2")
    assert result["is_valid"] is True
    assert result["success"] is True
    
    result = math_tools_service.validate_expression("sqrt(16) + sin(0)")
    assert result["is_valid"] is True
    assert result["success"] is True
    
    result = math_tools_service.validate_expression("pi * 2")
    assert result["is_valid"] is True
    assert result["success"] is True


def test_validate_expression_invalid(math_tools_service):
    """Test expression validation with invalid expressions."""
    result = math_tools_service.validate_expression("(5 + 3")
    assert result["is_valid"] is False
    assert result["success"] is True
    assert "Unbalanced parentheses" in result["error"]
    
    result = math_tools_service.validate_expression("5 +* 3")
    assert result["is_valid"] is False
    assert result["success"] is True
    
    result = math_tools_service.validate_expression("foo(5)")
    assert result["is_valid"] is False
    assert result["success"] is True


def test_check_answer_numerical(math_tools_service):
    """Test answer checking for numerical answers."""
    result = math_tools_service.check_answer("10", "10")
    assert result["is_correct"] is True
    assert result["success"] is True
    
    result = math_tools_service.check_answer("2+3", "5")
    assert result["is_correct"] is True
    assert result["success"] is True
    
    result = math_tools_service.check_answer("3.1415", "3.14159", tolerance=0.001)
    assert result["is_correct"] is True
    assert result["success"] is True
    
    result = math_tools_service.check_answer("3.1", "3.2", tolerance=0.01)
    assert result["is_correct"] is False
    assert result["success"] is True


def test_check_answer_expressions(math_tools_service):
    """Test answer checking for equivalent expressions."""
    result = math_tools_service.check_answer("x^2 + 2*x + 1", "x**2+2*x+1")
    assert result["is_correct"] is True
    assert result["success"] is True
    
    result = math_tools_service.check_answer("x^2 + 3*x + 1", "x^2 + 2*x + 1")
    assert result["is_correct"] is False
    assert result["success"] is True


def test_validate_formula(math_tools_service):
    """Test formula validation."""
    result = math_tools_service.validate_formula("2 + 3 * 4")
    assert result["is_valid"] is True
    assert result["success"] is True
    
    result = math_tools_service.validate_formula("sqrt(16) + sin(0)")
    assert result["is_valid"] is True
    assert result["success"] is True
    
    result = math_tools_service.validate_formula("(2 + 3")
    assert result["is_valid"] is False
    assert result["error"] == "Unbalanced parentheses"
    assert result["success"] is True
    
    result = math_tools_service.validate_formula("2 ++ 3")
    assert result["is_valid"] is False
    assert result["success"] is True
    
    result = math_tools_service.validate_formula("notafunction(5)")
    assert result["is_valid"] is False
    assert result["success"] is True


def test_format_expression(math_tools_service):
    """Test expression formatting."""
    result = math_tools_service.format_expression("2+3*4")
    assert result["formatted"] == "2 + 3 * 4"
    assert result["success"] is True
    
    result = math_tools_service.format_expression("2^3")
    assert result["formatted"] == "2 ** 3"
    assert result["success"] is True
    
    result = math_tools_service.format_expression("sqrt (16)")
    assert result["formatted"] == "sqrt(16)"
    assert result["success"] is True
    
    result = math_tools_service.format_expression("2+3^2*sqrt(4)+sin(0)")
    assert result["formatted"] == "2 + 3 ** 2 * sqrt(4) + sin(0)"
    assert result["success"] is True


def test_prepare_geometry_visualization(math_tools_service):
    """Test geometry visualization data preparation."""
    result = math_tools_service.prepare_geometry_visualization("circle", {"radius": 5})
    assert result["success"] is True
    assert result["error"] is None
    assert result["shape"] == "circle"
    assert "points" in result
    assert len(result["points"]) > 0
    assert "properties" in result
    assert abs(result["properties"]["area"] - (math.pi * 25)) < 0.01
    assert abs(result["properties"]["circumference"] - (2 * math.pi * 5)) < 0.01
    
    result = math_tools_service.prepare_geometry_visualization("circle", {"radius": -5})
    assert result["success"] is False
    assert "error" in result
    
    result = math_tools_service.prepare_geometry_visualization("rectangle", {"width": 10, "height": 5})
    assert result["success"] is True
    assert result["error"] is None
    assert result["shape"] == "rectangle"
    assert "vertices" in result
    assert len(result["vertices"]) == 5  # 4 corners plus the first point repeated to close the shape
    assert "properties" in result
    assert result["properties"]["area"] == 50
    assert result["properties"]["perimeter"] == 30
    
    result = math_tools_service.prepare_geometry_visualization("rectangle", {"width": 10})
    assert result["success"] is False
    assert "error" in result
    
    vertices = [
        {"x": 0, "y": 0},
        {"x": 4, "y": 0},
        {"x": 0, "y": 3}
    ]
    result = math_tools_service.prepare_geometry_visualization("triangle", {"vertices": vertices})
    assert result["success"] is True
    assert result["error"] is None
    assert result["shape"] == "triangle"
    assert "vertices" in result
    assert len(result["vertices"]) == 4  # 3 vertices plus the first repeated to close the shape
    assert "properties" in result
    assert abs(result["properties"]["area"] - 6.0) < 0.01  # Triangle area = 6
    assert "sides" in result["properties"]
    assert len(result["properties"]["sides"]) == 3
    
    result = math_tools_service.prepare_geometry_visualization("triangle", {
        "side_a": 3,
        "side_b": 4,
        "side_c": 5
    })
    assert result["success"] is True
    assert result["error"] is None
    assert result["shape"] == "triangle"
    assert "vertices" in result
    assert "properties" in result
    assert abs(result["properties"]["area"] - 6.0) < 0.01  # 3-4-5 triangle area = 6
    assert result["properties"]["perimeter"] == 12
    
    result = math_tools_service.prepare_geometry_visualization("triangle", {
        "side_a": 1,
        "side_b": 1,
        "side_c": 10  # Violates triangle inequality
    })
    assert result["success"] is False
    assert "error" in result
    
    result = math_tools_service.prepare_geometry_visualization("hexagon", {"side_length": 5})
    assert result["success"] is False
    assert "error" in result
    assert "Unsupported shape" in result["error"]


def test_prepare_statistics_visualization(math_tools_service):
    """Test the preparation of statistical visualization data"""
    service = MathToolsService()
    
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    result = service.prepare_statistics_visualization(data, "histogram")
    
    assert result["success"] is True
    assert result["error"] is None
    assert result["visualization_type"] == "histogram"
    assert "bins" in result
    assert "data_summary" in result
    assert result["data_summary"]["count"] == 10
    assert result["data_summary"]["min"] == 1
    assert result["data_summary"]["max"] == 10
    assert result["data_summary"]["mean"] == 5.5
    
    result = service.prepare_statistics_visualization(data, "boxplot")
    
    assert result["success"] is True
    assert result["error"] is None
    assert result["visualization_type"] == "boxplot"
    assert "quartiles" in result
    assert result["quartiles"]["q1"] == 3.25
    assert result["quartiles"]["q2"] == 5.5
    assert result["quartiles"]["q3"] == 7.75
    assert result["iqr"] == 4.5
    assert "whiskers" in result
    assert "outliers" in result
    
    result = service.prepare_statistics_visualization(data, "scatter")
    
    assert result["success"] is True
    assert result["error"] is None
    assert result["visualization_type"] == "scatter"
    assert "points" in result
    assert len(result["points"]) == 10
    assert "regression" in result
    assert "slope" in result["regression"]
    assert "intercept" in result["regression"]
    assert "r_squared" in result["regression"]
    assert "trendline" in result["regression"]
    
    result = service.prepare_statistics_visualization(data, "bar")
    
    assert result["success"] is True
    assert result["error"] is None
    assert result["visualization_type"] == "bar"
    assert "bars" in result
    assert len(result["bars"]) == 10
    assert result["bars"][0]["value"] == 1.0
    assert result["bars"][9]["value"] == 10.0
    
    result = service.prepare_statistics_visualization(data, "line")
    
    assert result["success"] is True
    assert result["error"] is None
    assert result["visualization_type"] == "line"
    assert "points" in result
    assert len(result["points"]) == 10
    assert "bounds" in result
    assert result["bounds"]["y_min"] == 1.0
    assert result["bounds"]["y_max"] == 10.0
    
    result = service.prepare_statistics_visualization([], "histogram")
    assert result["success"] is False
    assert "error" in result
    
    result = service.prepare_statistics_visualization(["a", "b", "c"], "histogram")
    assert result["success"] is False
    assert "error" in result
    
    result = service.prepare_statistics_visualization(data, "invalid_type")
    assert result["success"] is False
    assert "error" in result
    assert "Unsupported visualization type" in result["error"]
    
    mock_tracking_service = MagicMock()
    service.tracking_service = mock_tracking_service
    
    result = service.prepare_statistics_visualization(data, "histogram", user_id="test_user")
    
    mock_tracking_service.track_tool_usage.assert_called_once_with(
        user_id="test_user",
        tool_type="statistics_tool",
        action="prepare_statistics_visualization",
        data={"visualization_type": "histogram", "data_points_count": 10}
    )


def test_prepare_function_graph_data(math_tools_service):
    """Test function graph data preparation."""
    result = math_tools_service.prepare_function_graph_data("2*x + 3", (-10, 10), 100)
    assert result["success"] is True
    assert result["error"] is None
    assert len(result["data_points"]) > 0  # At least some valid points
    assert "x_range" in result
    assert "y_range" in result
    
    # Check some sample points for linear function y = 2x + 3
    data_points = result["data_points"]
    
    # Find points closest to x = 1, 5, and 10
    x_1_point = min(data_points, key=lambda p: abs(p["x"] - 1))
    x_5_point = min(data_points, key=lambda p: abs(p["x"] - 5))
    x_10_point = min(data_points, key=lambda p: abs(p["x"] - 10))
    
    assert abs(x_1_point["y"] - 5) < 0.2  # y = 2*1 + 3 = 5
    assert abs(x_5_point["y"] - 13) < 0.2  # y = 2*5 + 3 = 13
    assert abs(x_10_point["y"] - 23) < 0.2  # y = 2*10 + 3 = 23
    
    # Quadratic function
    result = math_tools_service.prepare_function_graph_data("x^2 - 4", (-5, 5), 50)
    assert result["success"] is True
    assert result["error"] is None
    assert len(result["data_points"]) > 0
    assert "x_range" in result
    assert "y_range" in result
    
    # Check some sample points for quadratic function y = x^2 - 4
    data_points = result["data_points"]
    
    # Find points closest to positive x values
    x_1_point = min(data_points, key=lambda p: abs(p["x"] - 1))
    x_3_point = min(data_points, key=lambda p: abs(p["x"] - 3))
    
    # Check that y values are approximately correct
    assert abs(x_1_point["y"] - (-3)) < 0.2  # y = 1^2 - 4 = -3
    assert abs(x_3_point["y"] - 5) < 0.3  # y = 3^2 - 4 = 5
    
    result = math_tools_service.prepare_function_graph_data("1/(x-2)", (-5, 10), 100)
    assert result["success"] is True
    assert "discontinuities" in result
    assert len(result["discontinuities"]) > 0  # There should be at least one discontinuity near x=2
    
    result = math_tools_service.prepare_function_graph_data("x+*2", (-5, 5), 50)
    assert result["success"] is False
    assert "error" in result


def test_preprocess_expression(math_tools_service):
    """Test expression preprocessing."""
    assert math_tools_service._preprocess_expression("pi") == str(math.pi)

    assert math_tools_service._preprocess_expression("2^3") == "2**3"

    assert math_tools_service._preprocess_expression("2(3+4)") == "2*(3+4)"


def test_has_balanced_parentheses(math_tools_service):
    """Test parentheses balancing check."""
    assert math_tools_service._has_balanced_parentheses("(2 + 3) * 4") is True
    assert math_tools_service._has_balanced_parentheses("((2 + 3) * (4 - 1))") is True
    
    assert math_tools_service._has_balanced_parentheses("(2 + 3") is False
    assert math_tools_service._has_balanced_parentheses("2 + 3)") is False
    assert math_tools_service._has_balanced_parentheses("((2 + 3) * 4") is False


def test_has_invalid_operators(math_tools_service):
    """Test invalid operator detection."""
    assert math_tools_service._has_invalid_operators("2 + 3 * 4") is False
    assert math_tools_service._has_invalid_operators("-2 + 3") is False
    
    assert math_tools_service._has_invalid_operators("2 ++ 3") is True
    assert math_tools_service._has_invalid_operators("2 */ 3") is True
    assert math_tools_service._has_invalid_operators("* 2 + 3") is True
    assert math_tools_service._has_invalid_operators("2 + 3 *") is True


def test_has_invalid_functions(math_tools_service):
    """Test invalid function detection."""
    assert math_tools_service._has_invalid_functions("sqrt(16)") is False
    assert math_tools_service._has_invalid_functions("sin(0) + cos(0)") is False
    
    assert math_tools_service._has_invalid_functions("notafunction(5)") is True
    assert math_tools_service._has_invalid_functions("foo(5) + sin(0)") is True


def test_normalize_expression(math_tools_service):
    """Test expression normalization."""
    assert math_tools_service._normalize_expression("2 + 3") == "2+3"
    assert math_tools_service._normalize_expression("2^3") == "2**3"


def test_tracking_service_integration(math_tools_service):
    """Test that user tracking is called when a user ID is provided."""
    math_tools_service.validate_expression("2 + 3", user_id="test_user")
    
    math_tools_service.tracking_service.track_tool_usage.assert_called_once_with(
        user_id="test_user",
        tool_type="expression_validator",
        action="validate_expression",
        data={"expression": "2 + 3"}
    ) 
