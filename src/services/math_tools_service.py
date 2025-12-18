import logging
import math
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

try:
    from scipy import stats

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

    class DummyStats:
        def percentile(self, *args, **kwargs):
            return 0

        def linregress(self, *args, **kwargs):
            return (0, 0, 0, 0, 0)  # slope, intercept, r_value, p_value, std_err

    stats = DummyStats()
import sympy as sp

from src.services.base_service import BaseService, handle_service_errors
from src.services.tracking_service import TrackingService

logger = logging.getLogger(__name__)

OPERATORS = {"+": 1, "-": 1, "*": 2, "/": 2, "^": 3, "**": 3}

FUNCTIONS = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "sqrt": math.sqrt,
    "log": math.log10,
    "ln": math.log,
    "abs": abs,
    "exp": math.exp,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
}

CONSTANTS = {"pi": math.pi, "e": math.e}


class MathToolsService(BaseService):
    """Service for mathematical tools to support educational content."""

    def __init__(self):
        """Initialize the math tools service."""
        super().__init__()
        self.tracking_service = None

    def _init_dependencies(self):
        """Initialize dependencies if not already set."""
        if self.tracking_service is None:
            self.tracking_service = TrackingService()

    @handle_service_errors(service_name="math_tools")
    def validate_expression(
        self, expression: str, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate a mathematical expression and check if the syntax is correct.
        Does NOT provide the solution, only validates correctness.

        Args:
            expression: The mathematical expression to validate
            user_id: Optional user ID for tracking usage

        Returns:
            Dictionary containing the validation result
        """
        self._init_dependencies()

        if user_id:
            self.tracking_service.track_tool_usage(
                user_id=user_id,
                tool_type="expression_validator",
                action="validate_expression",
                data={"expression": expression},
            )

        try:
            cleaned_expression = self._preprocess_expression(expression)

            if not self._has_balanced_parentheses(cleaned_expression):
                return {
                    "expression": expression,
                    "is_valid": False,
                    "error": "Unbalanced parentheses",
                    "success": True,
                }

            if self._has_invalid_operators(cleaned_expression):
                return {
                    "expression": expression,
                    "is_valid": False,
                    "error": "Invalid operator usage",
                    "success": True,
                }

            if self._has_invalid_functions(cleaned_expression):
                return {
                    "expression": expression,
                    "is_valid": False,
                    "error": "Invalid function usage",
                    "success": True,
                }

            try:
                self._tokenize_expression(cleaned_expression)
                return {
                    "expression": expression,
                    "is_valid": True,
                    "error": None,
                    "success": True,
                }
            except Exception as e:
                logger.error(f"Error tokenizing expression '{expression}': {str(e)}")
                return {
                    "expression": expression,
                    "is_valid": False,
                    "error": str(e),
                    "success": True,
                }

        except Exception as e:
            logger.error(f"Error validating expression '{expression}': {str(e)}")
            return {
                "expression": expression,
                "is_valid": False,
                "error": str(e),
                "success": False,
            }

    @handle_service_errors(service_name="math_tools")
    def check_answer(
        self,
        student_answer: str,
        correct_answer: str,
        tolerance: float = 0.001,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Check if a student's answer matches the correct answer within a given tolerance.

        Args:
            student_answer: The student's submitted answer
            correct_answer: The correct answer to compare against
            tolerance: Tolerance for numerical comparison (default: 0.001)
            user_id: Optional user ID for tracking usage

        Returns:
            Dictionary containing the result and additional information
        """
        self._init_dependencies()

        if user_id:
            self.tracking_service.track_tool_usage(
                user_id=user_id,
                tool_type="answer_checker",
                action="check_answer",
                data={"student_answer": student_answer, "tolerance": tolerance},
            )

        try:
            cleaned_student = self._preprocess_expression(student_answer)
            cleaned_correct = self._preprocess_expression(correct_answer)

            try:
                student_value = self._evaluate_parsed_expression(cleaned_student)
                correct_value = self._evaluate_parsed_expression(cleaned_correct)

                is_correct = abs(student_value - correct_value) <= tolerance

                return {
                    "student_answer": student_answer,
                    "is_correct": is_correct,
                    "error": None,
                    "success": True,
                }

            except Exception as e:
                student_normalized = self._normalize_expression(cleaned_student)
                correct_normalized = self._normalize_expression(cleaned_correct)

                is_correct = student_normalized == correct_normalized

                return {
                    "student_answer": student_answer,
                    "is_correct": is_correct,
                    "error": None,
                    "success": True,
                }

        except Exception as e:
            logger.error(f"Error checking answer '{student_answer}': {str(e)}")
            return {
                "student_answer": student_answer,
                "is_correct": False,
                "error": str(e),
                "success": False,
            }

    @handle_service_errors(service_name="math_tools")
    def validate_formula(
        self, formula: str, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate a mathematical formula for syntax correctness.

        Args:
            formula: The formula to validate
            user_id: Optional user ID for tracking usage

        Returns:
            Dictionary containing validation results
        """
        self._init_dependencies()

        if user_id:
            self.tracking_service.track_tool_usage(
                user_id=user_id,
                tool_type="formula_validator",
                action="validate_formula",
                data={"formula": formula},
            )

        try:
            cleaned_formula = self._preprocess_expression(formula)

            if not self._has_balanced_parentheses(cleaned_formula):
                return {
                    "formula": formula,
                    "is_valid": False,
                    "error": "Unbalanced parentheses",
                    "success": True,
                }

            if self._has_invalid_operators(cleaned_formula):
                return {
                    "formula": formula,
                    "is_valid": False,
                    "error": "Invalid operator usage",
                    "success": True,
                }

            if self._has_invalid_functions(cleaned_formula):
                return {
                    "formula": formula,
                    "is_valid": False,
                    "error": "Invalid function usage",
                    "success": True,
                }

            try:
                self._tokenize_expression(cleaned_formula)
                return {
                    "formula": formula,
                    "is_valid": True,
                    "error": None,
                    "success": True,
                }
            except Exception as e:
                logger.error(f"Error tokenizing formula '{formula}': {str(e)}")
                return {
                    "formula": formula,
                    "is_valid": False,
                    "error": str(e),
                    "success": True,
                }

        except Exception as e:
            logger.error(f"Error validating formula '{formula}': {str(e)}")
            return {
                "formula": formula,
                "is_valid": False,
                "error": str(e),
                "success": False,
            }

    @handle_service_errors(service_name="math_tools")
    def format_expression(
        self, expression: str, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format a mathematical expression to ensure correct syntax.

        Args:
            expression: The expression to format
            user_id: Optional user ID for tracking usage

        Returns:
            Dictionary containing the formatted expression
        """
        self._init_dependencies()

        if user_id:
            self.tracking_service.track_tool_usage(
                user_id=user_id,
                tool_type="expression_formatter",
                action="format_expression",
                data={"expression": expression},
            )

        try:
            # 1. Replace multiple spaces with single space
            formatted = re.sub(r"\s+", " ", expression.strip())

            # 2. Convert power operator from ^ to ** first
            formatted = formatted.replace("^", "**")

            # 3. Ensure space around single operators (but not around **)
            for op in ["+", "-", "/", "="]:
                formatted = re.sub(
                    r"([^\s])" + re.escape(op) + r"([^\s])",
                    r"\1 " + op + r" \2",
                    formatted,
                )

            # Special handling for multiplication and power operators
            # Add spaces around * but not if it's part of **
            formatted = re.sub(r"([^\s\*])\*([^\*])", r"\1 * \2", formatted)
            formatted = re.sub(r"([^\*])\*([^\s\*])", r"\1 * \2", formatted)

            # Add spaces around ** without adding space between the asterisks
            formatted = re.sub(r"([^\s])\*\*([^\s])", r"\1 ** \2", formatted)

            # 4. Format functions - ensure no space between function name and opening parenthesis
            for func in FUNCTIONS.keys():
                formatted = re.sub(r"(" + func + r")\s+\(", r"\1(", formatted)

            # 5. Remove spaces inside parentheses next to the parenthesis
            formatted = re.sub(r"\(\s+", "(", formatted)
            formatted = re.sub(r"\s+\)", ")", formatted)

            # 6. Remove unnecessary + at the beginning
            if formatted.startswith("+"):
                formatted = formatted[1:].strip()

            return {
                "original": expression,
                "formatted": formatted,
                "error": None,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error formatting expression '{expression}': {str(e)}")
            return {
                "original": expression,
                "formatted": None,
                "error": str(e),
                "success": False,
            }

    @handle_service_errors(service_name="math_tools")
    def prepare_geometry_visualization(
        self, shape: str, parameters: Dict[str, float], user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Prepare data for visualizing a geometric shape.

        Args:
            shape: Type of shape to visualize (e.g., "circle", "rectangle", "triangle")
            parameters: Dictionary of shape parameters (e.g., {"radius": 5} for circle)
            user_id: Optional user ID for tracking usage

        Returns:
            Dictionary containing visualization data for the shape
        """
        self._init_dependencies()

        if user_id:
            self.tracking_service.track_tool_usage(
                user_id=user_id,
                tool_type="geometry_tool",
                action="prepare_geometry_visualization",
                data={"shape": shape, "parameters": parameters},
            )

        try:
            shape = shape.lower()

            if shape == "circle":
                if "radius" not in parameters:
                    return {
                        "shape": shape,
                        "error": "Radius is required for circle visualization",
                        "success": False,
                    }

                radius = parameters["radius"]
                if radius <= 0:
                    return {
                        "shape": shape,
                        "error": "Radius must be positive",
                        "success": False,
                    }

                center_x = parameters.get("center_x", 0)
                center_y = parameters.get("center_y", 0)

                num_points = 100
                points = []
                for i in range(num_points):
                    angle = 2 * math.pi * i / num_points
                    x = center_x + radius * math.cos(angle)
                    y = center_y + radius * math.sin(angle)
                    points.append({"x": float(x), "y": float(y)})

                area = math.pi * radius**2
                circumference = 2 * math.pi * radius

                return {
                    "shape": "circle",
                    "parameters": {
                        "radius": radius,
                        "center_x": center_x,
                        "center_y": center_y,
                    },
                    "points": points,
                    "properties": {"area": area, "circumference": circumference},
                    "bounds": {
                        "x_min": center_x - radius,
                        "x_max": center_x + radius,
                        "y_min": center_y - radius,
                        "y_max": center_y + radius,
                    },
                    "error": None,
                    "success": True,
                }

            elif shape == "rectangle":
                if "width" not in parameters or "height" not in parameters:
                    return {
                        "shape": shape,
                        "error": "Width and height are required for rectangle visualization",
                        "success": False,
                    }

                width = parameters["width"]
                height = parameters["height"]

                if width <= 0 or height <= 0:
                    return {
                        "shape": shape,
                        "error": "Width and height must be positive",
                        "success": False,
                    }

                center_x = parameters.get("center_x", 0)
                center_y = parameters.get("center_y", 0)

                half_width = width / 2
                half_height = height / 2

                vertices = [
                    {
                        "x": center_x - half_width,
                        "y": center_y - half_height,
                    },  # Bottom-left
                    {
                        "x": center_x + half_width,
                        "y": center_y - half_height,
                    },  # Bottom-right
                    {
                        "x": center_x + half_width,
                        "y": center_y + half_height,
                    },  # Top-right
                    {
                        "x": center_x - half_width,
                        "y": center_y + half_height,
                    },  # Top-left
                    {
                        "x": center_x - half_width,
                        "y": center_y - half_height,
                    },  # Close the shape
                ]

                area = width * height
                perimeter = 2 * (width + height)

                return {
                    "shape": "rectangle",
                    "parameters": {
                        "width": width,
                        "height": height,
                        "center_x": center_x,
                        "center_y": center_y,
                    },
                    "vertices": vertices,
                    "properties": {"area": area, "perimeter": perimeter},
                    "bounds": {
                        "x_min": center_x - half_width,
                        "x_max": center_x + half_width,
                        "y_min": center_y - half_height,
                        "y_max": center_y + half_height,
                    },
                    "error": None,
                    "success": True,
                }

            elif shape == "triangle":
                if "vertices" in parameters:
                    vertices = parameters["vertices"]
                    if not isinstance(vertices, list) or len(vertices) != 3:
                        return {
                            "shape": shape,
                            "error": "Triangle must be specified with exactly 3 vertices",
                            "success": False,
                        }

                    try:
                        points = [
                            {"x": float(v["x"]), "y": float(v["y"])} for v in vertices
                        ]
                        points.append(
                            {"x": float(vertices[0]["x"]), "y": float(vertices[0]["y"])}
                        )
                    except (KeyError, TypeError):
                        return {
                            "shape": shape,
                            "error": "Each vertex must have x and y coordinates",
                            "success": False,
                        }

                    area = 0.5 * abs(
                        (points[0]["x"] * (points[1]["y"] - points[2]["y"]))
                        + (points[1]["x"] * (points[2]["y"] - points[0]["y"]))
                        + (points[2]["x"] * (points[0]["y"] - points[1]["y"]))
                    )

                    side1 = math.sqrt(
                        (points[0]["x"] - points[1]["x"]) ** 2
                        + (points[0]["y"] - points[1]["y"]) ** 2
                    )
                    side2 = math.sqrt(
                        (points[1]["x"] - points[2]["x"]) ** 2
                        + (points[1]["y"] - points[2]["y"]) ** 2
                    )
                    side3 = math.sqrt(
                        (points[2]["x"] - points[0]["x"]) ** 2
                        + (points[2]["y"] - points[0]["y"]) ** 2
                    )
                    perimeter = side1 + side2 + side3

                    # Calculate bounds
                    x_values = [
                        p["x"] for p in points[:-1]
                    ]  # Exclude the repeated point
                    y_values = [p["y"] for p in points[:-1]]

                    return {
                        "shape": "triangle",
                        "parameters": {"vertices": vertices},
                        "vertices": points,
                        "properties": {
                            "area": area,
                            "perimeter": perimeter,
                            "sides": [side1, side2, side3],
                        },
                        "bounds": {
                            "x_min": min(x_values),
                            "x_max": max(x_values),
                            "y_min": min(y_values),
                            "y_max": max(y_values),
                        },
                        "error": None,
                        "success": True,
                    }

                elif all(p in parameters for p in ["side_a", "side_b", "side_c"]):
                    side_a = parameters["side_a"]
                    side_b = parameters["side_b"]
                    side_c = parameters["side_c"]

                    if side_a <= 0 or side_b <= 0 or side_c <= 0:
                        return {
                            "shape": shape,
                            "error": "All sides must be positive",
                            "success": False,
                        }

                    if (
                        (side_a + side_b <= side_c)
                        or (side_a + side_c <= side_b)
                        or (side_b + side_c <= side_a)
                    ):
                        return {
                            "shape": shape,
                            "error": "The sum of any two sides must be greater than the third side",
                            "success": False,
                        }

                    perimeter = side_a + side_b + side_c
                    s = perimeter / 2  # Semi-perimeter
                    area = math.sqrt(
                        s * (s - side_a) * (s - side_b) * (s - side_c)
                    )  # Heron's formula

                    cos_angle = (side_a**2 + side_c**2 - side_b**2) / (
                        2 * side_a * side_c
                    )
                    if cos_angle < -1:
                        cos_angle = -1
                    elif cos_angle > 1:
                        cos_angle = 1
                    angle = math.acos(cos_angle)

                    vertices = [
                        {"x": 0, "y": 0},  # First vertex at origin
                        {"x": side_a, "y": 0},  # Second vertex
                        {
                            "x": side_c * math.cos(angle),
                            "y": side_c * math.sin(angle),
                        },  # Third vertex
                    ]

                    vertices.append({"x": 0, "y": 0})

                    return {
                        "shape": "triangle",
                        "parameters": {
                            "side_a": side_a,
                            "side_b": side_b,
                            "side_c": side_c,
                        },
                        "vertices": vertices,
                        "properties": {
                            "area": area,
                            "perimeter": perimeter,
                            "sides": [side_a, side_b, side_c],
                        },
                        "bounds": {
                            "x_min": 0,
                            "x_max": max(side_a, side_c * math.cos(angle)),
                            "y_min": 0,
                            "y_max": side_c * math.sin(angle),
                        },
                        "error": None,
                        "success": True,
                    }

                else:
                    return {
                        "shape": shape,
                        "error": "Triangle must be specified with either 3 vertices or 3 sides",
                        "success": False,
                    }

            else:
                return {
                    "shape": shape,
                    "error": f"Unsupported shape: {shape}. Supported shapes are: circle, rectangle, triangle",
                    "success": False,
                }

        except Exception as e:
            logger.error(
                f"Error preparing geometry visualization for {shape}: {str(e)}"
            )
            return {"shape": shape, "error": str(e), "success": False}

    @handle_service_errors(service_name="math_tools")
    def prepare_statistics_visualization(
        self, data: List[float], visualization_type: str, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Prepare data for statistical visualization.

        Args:
            data: List of numerical data points
            visualization_type: Type of visualization ("histogram", "boxplot", "scatter", etc.)
            user_id: Optional user ID for tracking usage

        Returns:
            Dictionary containing prepared visualization data
        """
        self._init_dependencies()

        if user_id:
            self.tracking_service.track_tool_usage(
                user_id=user_id,
                tool_type="statistics_tool",
                action="prepare_statistics_visualization",
                data={
                    "visualization_type": visualization_type,
                    "data_points_count": len(data),
                },
            )

        try:
            if not data:
                return {
                    "visualization_type": visualization_type,
                    "error": "No data provided for visualization",
                    "success": False,
                }

            try:
                data = [float(x) for x in data]
            except (ValueError, TypeError):
                return {
                    "visualization_type": visualization_type,
                    "error": "Data must contain only numerical values",
                    "success": False,
                }

            basic_stats = {
                "count": len(data),
                "min": min(data),
                "max": max(data),
                "mean": float(np.mean(data)),
                "median": float(np.median(data)),
                "std_dev": float(np.std(data)),
                "variance": float(np.var(data)),
            }

            visualization_type = visualization_type.lower()

            if visualization_type == "histogram":
                n = len(data)
                num_bins = int(np.ceil(np.log2(n) + 1))

                hist, bin_edges = np.histogram(data, bins=num_bins)

                bins = []
                for i in range(len(hist)):
                    bins.append(
                        {
                            "bin_start": float(bin_edges[i]),
                            "bin_end": float(bin_edges[i + 1]),
                            "count": int(hist[i]),
                            "frequency": float(hist[i] / n),
                        }
                    )

                return {
                    "visualization_type": "histogram",
                    "data_summary": basic_stats,
                    "bins": bins,
                    "bin_count": num_bins,
                    "error": None,
                    "success": True,
                }

            elif visualization_type == "boxplot":
                q1 = np.percentile(data, 25, method="linear")
                q2 = np.percentile(data, 50, method="linear")
                q3 = np.percentile(data, 75, method="linear")
                min_val = np.min(data)
                max_val = np.max(data)

                lower_whisker = float(max(min_val, q1 - 1.5 * (q3 - q1)))
                upper_whisker = float(min(max_val, q3 + 1.5 * (q3 - q1)))

                outliers = [
                    float(x) for x in data if x < lower_whisker or x > upper_whisker
                ]

                return {
                    "visualization_type": "boxplot",
                    "data_summary": basic_stats,
                    "quartiles": {"q1": q1, "q2": q2, "q3": q3},
                    "iqr": q3 - q1,
                    "whiskers": {"lower": lower_whisker, "upper": upper_whisker},
                    "outliers": outliers,
                    "error": None,
                    "success": True,
                }

            elif visualization_type == "scatter":
                points = [
                    {"x": float(i), "y": float(val)} for i, val in enumerate(data)
                ]

                x_values = [p["x"] for p in points]
                y_values = [p["y"] for p in points]

                if len(points) > 1:
                    slope, intercept, r_value, p_value, std_err = stats.linregress(
                        x_values, y_values
                    )

                    trendline = [
                        {"x": float(x), "y": float(slope * x + intercept)}
                        for x in [min(x_values), max(x_values)]
                    ]

                    return {
                        "visualization_type": "scatter",
                        "data_summary": basic_stats,
                        "points": points,
                        "regression": {
                            "slope": float(slope),
                            "intercept": float(intercept),
                            "r_squared": float(r_value**2),
                            "p_value": float(p_value),
                            "std_error": float(std_err),
                            "trendline": trendline,
                        },
                        "bounds": {
                            "x_min": float(min(x_values)),
                            "x_max": float(max(x_values)),
                            "y_min": float(min(y_values)),
                            "y_max": float(max(y_values)),
                        },
                        "error": None,
                        "success": True,
                    }
                else:
                    return {
                        "visualization_type": "scatter",
                        "data_summary": basic_stats,
                        "points": points,
                        "error": None,
                        "success": True,
                    }

            elif visualization_type == "bar":
                bars = [{"index": i, "value": float(val)} for i, val in enumerate(data)]

                return {
                    "visualization_type": "bar",
                    "data_summary": basic_stats,
                    "bars": bars,
                    "error": None,
                    "success": True,
                }

            elif visualization_type == "line":
                points = [
                    {"x": float(i), "y": float(val)} for i, val in enumerate(data)
                ]

                return {
                    "visualization_type": "line",
                    "data_summary": basic_stats,
                    "points": points,
                    "bounds": {
                        "x_min": 0,
                        "x_max": float(len(data) - 1),
                        "y_min": float(min(data)),
                        "y_max": float(max(data)),
                    },
                    "error": None,
                    "success": True,
                }

            else:
                return {
                    "visualization_type": visualization_type,
                    "error": f"Unsupported visualization type: {visualization_type}. Supported types are: histogram, boxplot, scatter, bar, line",
                    "success": False,
                }

        except Exception as e:
            logger.error(f"Error preparing statistics visualization: {str(e)}")
            return {
                "visualization_type": visualization_type,
                "error": str(e),
                "success": False,
            }

    @handle_service_errors(service_name="math_tools")
    def prepare_function_graph_data(
        self,
        function_expression: str,
        x_range: Tuple[float, float],
        num_points: int = 100,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Prepare data points for graphing a mathematical function.

        Args:
            function_expression: Mathematical expression representing the function (e.g., "x^2 + 2*x - 1")
            x_range: Tuple containing the range of x values (min_x, max_x)
            num_points: Number of data points to generate
            user_id: Optional user ID for tracking usage

        Returns:
            Dictionary containing data points for visualization
        """
        self._init_dependencies()

        if user_id:
            self.tracking_service.track_tool_usage(
                user_id=user_id,
                tool_type="graphing_tool",
                action="prepare_function_graph_data",
                data={
                    "function": function_expression,
                    "x_range": x_range,
                    "num_points": num_points,
                },
            )

        try:
            validation_result = self.validate_expression(function_expression)
            if not validation_result["is_valid"]:
                return {
                    "function": function_expression,
                    "x_range": x_range,
                    "data_points": [],
                    "error": f"Invalid function expression: {validation_result['error']}",
                    "success": False,
                }

            preprocessed_expression = self._preprocess_expression(function_expression)

            expression_template = preprocessed_expression.replace("x", "{x}")

            min_x, max_x = x_range
            x_values = np.linspace(min_x, max_x, num_points)

            data_points = []
            discontinuities = []

            for x in x_values:
                try:
                    expr = expression_template.format(x=x)
                    y = self._evaluate_parsed_expression(expr)

                    if not math.isfinite(y) or abs(y) > 1e10:
                        discontinuities.append(x)
                        continue

                    data_points.append({"x": float(x), "y": float(y)})
                except Exception as e:
                    discontinuities.append(x)
                    logger.debug(f"Error evaluating function at x={x}: {str(e)}")

            if len(data_points) < 2:
                return {
                    "function": function_expression,
                    "x_range": x_range,
                    "data_points": [],
                    "error": "Could not generate enough valid data points. The function may have too many discontinuities in the specified range.",
                    "success": False,
                }

            y_values = [point["y"] for point in data_points]
            y_min = min(y_values)
            y_max = max(y_values)

            y_padding = (y_max - y_min) * 0.1 if y_max > y_min else 1.0
            y_range = (y_min - y_padding, y_max + y_padding)

            if abs(y_max - y_min) < 1e-10:
                y_range = (y_min - 1, y_max + 1)

            return {
                "function": function_expression,
                "x_range": x_range,
                "y_range": y_range,
                "data_points": data_points,
                "discontinuities": discontinuities,
                "error": None,
                "success": True,
            }
        except Exception as e:
            logger.error(
                f"Error preparing graph data for function '{function_expression}': {str(e)}"
            )
            return {
                "function": function_expression,
                "x_range": x_range,
                "data_points": [],
                "error": str(e),
                "success": False,
            }

    def _preprocess_expression(self, expression: str) -> str:
        """
        Preprocess an expression for validation or evaluation.

        Args:
            expression: The expression to preprocess

        Returns:
            Preprocessed expression
        """
        expression = expression.replace(" ", "")

        for const, value in CONSTANTS.items():
            pattern = r"(?<![a-zA-Z0-9_])" + const + r"(?![a-zA-Z0-9_])"
            expression = re.sub(pattern, str(value), expression)

        # Replace ^ with ** for exponentiation
        expression = expression.replace("^", "**")

        # Ensure proper multiplication (e.g., 2(3+4) becomes 2*(3+4))
        expression = re.sub(r"(\d+)(\()", r"\1*\2", expression)

        return expression

    def _normalize_expression(self, expression: str) -> str:
        """
        Normalize an expression for string comparison.

        Args:
            expression: The expression to normalize

        Returns:
            Normalized expression string
        """
        normalized = expression.replace(" ", "").replace("^", "**")

        return normalized

    def _tokenize_expression(self, expression: str) -> List[str]:
        """
        Tokenize an expression into its components.

        Args:
            expression: The expression to tokenize

        Returns:
            List of tokens
        """
        tokens = []
        i = 0

        while i < len(expression):
            char = expression[i]

            if char.isdigit() or char == ".":
                j = i
                while j < len(expression) and (
                    expression[j].isdigit() or expression[j] == "."
                ):
                    j += 1
                tokens.append(expression[i:j])
                i = j
                continue

            if char in OPERATORS or (
                char == "*" and i + 1 < len(expression) and expression[i + 1] == "*"
            ):
                if char == "*" and i + 1 < len(expression) and expression[i + 1] == "*":
                    tokens.append("**")
                    i += 2
                else:
                    tokens.append(char)
                    i += 1
                continue

            if char.isalpha():
                j = i
                while j < len(expression) and (
                    expression[j].isalnum() or expression[j] == "_"
                ):
                    j += 1
                name = expression[i:j]
                tokens.append(name)
                i = j
                continue

            if char in "()":
                tokens.append(char)
                i += 1
                continue

            i += 1

        return tokens

    def _has_balanced_parentheses(self, expression: str) -> bool:
        """
        Check if parentheses are balanced in an expression.

        Args:
            expression: The expression to check

        Returns:
            True if parentheses are balanced, False otherwise
        """
        count = 0
        for char in expression:
            if char == "(":
                count += 1
            elif char == ")":
                count -= 1
                if count < 0:
                    return False
        return count == 0

    def _has_invalid_operators(self, expression: str) -> bool:
        """
        Check if the expression has invalid operator usage.

        Args:
            expression: The expression to check

        Returns:
            True if there are invalid operators, False otherwise
        """
        # Check for consecutive operators (++, --, +*, etc.)
        for i in range(len(expression) - 1):
            if expression[i] in "+-*/^" and expression[i + 1] in "+-*/^":
                # Allow for double asterisk (**) for exponentiation
                if not (expression[i] == "*" and expression[i + 1] == "*"):
                    return True

        # Check for operators at the beginning (except + and -)
        if expression and expression[0] in "*/^":
            return True

        # Check for operators at the end
        if expression and expression[-1] in "+-*/^":
            return True

        return False

    def _has_invalid_functions(self, expression: str) -> bool:
        """
        Check if the expression has invalid function usage.

        Args:
            expression: The expression to check

        Returns:
            True if there are invalid functions, False otherwise
        """
        function_pattern = r"([a-zA-Z_][a-zA-Z0-9_]*)\("
        for match in re.finditer(function_pattern, expression):
            func_name = match.group(1)
            if func_name not in FUNCTIONS:
                return True

        return False

    def _is_number(self, s: str) -> bool:
        """
        Check if a string can be converted to a number.

        Args:
            s: The string to check

        Returns:
            True if the string is a number, False otherwise
        """
        try:
            float(s)
            return True
        except ValueError:
            return False

    def _evaluate_parsed_expression(self, expression: str) -> float:
        """
        Evaluate a preprocessed expression.
        Used for answer validation only, not as a user-facing calculator.

        Args:
            expression: The preprocessed expression

        Returns:
            The evaluation result
        """
        if not expression:
            raise ValueError("Empty expression")

        tokens = self._tokenize_expression(expression)
        return self._evaluate_tokens(tokens)

    def _evaluate_tokens(self, tokens: List[str]) -> float:
        """
        Evaluate a list of tokens using the shunting-yard algorithm.
        Used for answer validation only, not as a user-facing calculator.

        Args:
            tokens: List of tokens to evaluate

        Returns:
            The evaluation result
        """
        output_queue = []
        operator_stack = []

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if self._is_number(token):
                output_queue.append(float(token))

            elif token in FUNCTIONS:
                operator_stack.append(token)

            elif token in OPERATORS:
                while (
                    operator_stack
                    and operator_stack[-1] != "("
                    and (
                        operator_stack[-1] in OPERATORS
                        and OPERATORS[operator_stack[-1]] >= OPERATORS[token]
                    )
                ):
                    output_queue.append(operator_stack.pop())
                operator_stack.append(token)

            elif token == "(":
                operator_stack.append(token)

            elif token == ")":
                while operator_stack and operator_stack[-1] != "(":
                    output_queue.append(operator_stack.pop())

                if operator_stack and operator_stack[-1] == "(":
                    operator_stack.pop()
                else:
                    raise ValueError("Mismatched parentheses")

                if operator_stack and operator_stack[-1] in FUNCTIONS:
                    output_queue.append(operator_stack.pop())

            else:
                raise ValueError(f"Unknown token: {token}")

            i += 1

        while operator_stack:
            if operator_stack[-1] == "(":
                raise ValueError("Mismatched parentheses")
            output_queue.append(operator_stack.pop())

        return self._evaluate_rpn(output_queue)

    def _evaluate_rpn(self, rpn: List[Any]) -> float:
        """
        Evaluate a Reverse Polish Notation (RPN) expression.
        Used for answer validation only, not as a user-facing calculator.

        Args:
            rpn: The RPN expression as a list

        Returns:
            The evaluation result
        """
        stack = []

        for token in rpn:
            if isinstance(token, (int, float)):
                stack.append(token)
            elif token in OPERATORS:
                if len(stack) < 2:
                    raise ValueError(f"Not enough operands for operator: {token}")

                b = stack.pop()
                a = stack.pop()

                if token == "+":
                    stack.append(a + b)
                elif token == "-":
                    stack.append(a - b)
                elif token == "*":
                    stack.append(a * b)
                elif token == "/":
                    if b == 0:
                        raise ValueError("Division by zero")
                    stack.append(a / b)
                elif token in ["^", "**"]:
                    stack.append(a**b)

            elif token in FUNCTIONS:
                if len(stack) < 1:
                    raise ValueError(f"Not enough operands for function: {token}")

                a = stack.pop()
                func = FUNCTIONS[token]

                try:
                    stack.append(func(a))
                except Exception as e:
                    raise ValueError(f"Error applying function {token}: {str(e)}")

            else:
                raise ValueError(f"Unknown token in RPN: {token}")

        if len(stack) != 1:
            raise ValueError("Invalid expression: too many values left on stack")

        return stack[0]
