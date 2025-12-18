import json
import logging
import math
import os
import re
import shutil
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from src.services.base_service import BaseService, handle_service_errors
from src.services.tracking_service import TrackingService

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {
    "python": {"extension": ".py", "command": "python", "comment_symbol": "#"},
    "javascript": {"extension": ".js", "command": "node", "comment_symbol": "//"},
}


class CSToolsService(BaseService):
    """Service for computer science tools to support educational content."""

    def __init__(self):
        """Initialize the CS tools service."""
        super().__init__()
        self.tracking_service = None
        self.sandbox_dir = tempfile.mkdtemp(prefix="cs_tools_sandbox_")

    def __del__(self):
        """Clean up sandbox directory on service destruction."""
        try:
            if hasattr(self, "sandbox_dir") and os.path.exists(self.sandbox_dir):
                shutil.rmtree(self.sandbox_dir)
        except Exception as e:
            logger.error(f"Failed to clean up sandbox directory: {str(e)}")

    def _init_dependencies(self):
        """Initialize dependencies if not already set."""
        if self.tracking_service is None:
            self.tracking_service = TrackingService()

    @handle_service_errors(service_name="cs_tools")
    def validate_code_syntax(
        self, code: str, language: str, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate the syntax of code in the specified language.
        Does NOT execute the code, only checks syntax.

        Args:
            code: The code to validate
            language: The programming language (e.g., "python", "javascript")
            user_id: Optional user ID for tracking usage

        Returns:
            Dictionary containing the validation result
        """
        self._init_dependencies()

        if user_id:
            self.tracking_service.track_tool_usage(
                user_id=user_id,
                tool_type="code_validator",
                action="validate_code_syntax",
                data={"code": code, "language": language},
            )

        try:
            if language not in SUPPORTED_LANGUAGES:
                return {
                    "language": language,
                    "is_valid": False,
                    "error": f"Unsupported language: {language}",
                    "success": True,
                }

            file_path = self._create_sandbox_file(code, language)

            if language == "python":
                result = self._check_python_syntax(file_path)
            elif language == "javascript":
                result = self._check_javascript_syntax(file_path)
            else:
                result = {
                    "is_valid": False,
                    "error": f"Syntax checking not implemented for {language}",
                }

            return {
                "language": language,
                "is_valid": result["is_valid"],
                "error": result["error"],
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error validating {language} code syntax: {str(e)}")
            return {
                "language": language,
                "is_valid": False,
                "error": str(e),
                "success": False,
            }

    def _check_python_syntax(self, file_path: str) -> Dict[str, Any]:
        """
        Check Python code syntax without execution.

        Args:
            file_path: Path to the Python file

        Returns:
            Dictionary containing validation result
        """
        try:
            with open(file_path, "r") as f:
                code = f.read()

            compile(code, file_path, "exec")

            return {"is_valid": True, "error": None}
        except SyntaxError as e:
            error_msg = f"SyntaxError: {str(e)}"
            if hasattr(e, "lineno") and hasattr(e, "offset"):
                error_msg += f" at line {e.lineno}, position {e.offset}"

            return {"is_valid": False, "error": error_msg}
        except Exception as e:
            return {"is_valid": False, "error": f"Error checking syntax: {str(e)}"}

    def _check_javascript_syntax(self, file_path: str) -> Dict[str, Any]:
        """
        Check JavaScript code syntax without execution.

        Args:
            file_path: Path to the JavaScript file

        Returns:
            Dictionary containing validation result
        """
        try:
            command = ["node", "--check", file_path]

            result = subprocess.run(command, capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                return {"is_valid": True, "error": None}
            else:
                error_msg = result.stderr.strip()
                return {"is_valid": False, "error": error_msg}
        except subprocess.TimeoutExpired:
            return {"is_valid": False, "error": "Timeout while checking syntax"}
        except Exception as e:
            return {"is_valid": False, "error": f"Error checking syntax: {str(e)}"}

    @handle_service_errors(service_name="cs_tools")
    def check_code_output(
        self,
        code: str,
        expected_output: str,
        language: str,
        inputs: Optional[List[str]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Check if the output of code matches the expected output.

        Args:
            code: The code to execute
            expected_output: The expected output to compare against
            language: The programming language
            inputs: Optional list of inputs to provide to the program
            user_id: Optional user ID for tracking usage

        Returns:
            Dictionary containing the comparison result
        """
        self._init_dependencies()

        if user_id:
            self.tracking_service.track_tool_usage(
                user_id=user_id,
                tool_type="code_checker",
                action="check_code_output",
                data={
                    "code": code,
                    "language": language,
                    "has_inputs": inputs is not None,
                },
            )

        try:
            if language not in SUPPORTED_LANGUAGES:
                return {
                    "language": language,
                    "is_correct": False,
                    "actual_output": "",
                    "error": f"Unsupported language: {language}",
                    "success": True,
                }

            file_path = self._create_sandbox_file(code, language)

            if language == "python":
                syntax_result = self._check_python_syntax(file_path)
            elif language == "javascript":
                syntax_result = self._check_javascript_syntax(file_path)
            else:
                syntax_result = {
                    "is_valid": False,
                    "error": f"Syntax checking not implemented for {language}",
                }

            if not syntax_result["is_valid"]:
                return {
                    "language": language,
                    "is_correct": False,
                    "actual_output": "",
                    "error": f"Syntax error: {syntax_result['error']}",
                    "success": True,
                }

            execution_result = self._execute_code_in_sandbox(
                file_path, language, inputs
            )

            if not execution_result["success"]:
                return {
                    "language": language,
                    "is_correct": False,
                    "actual_output": "",
                    "error": f"Execution error: {execution_result['error']}",
                    "success": True,
                }

            actual_output = execution_result["output"].strip()
            expected_output = expected_output.strip()

            is_correct = actual_output == expected_output

            return {
                "language": language,
                "is_correct": is_correct,
                "actual_output": actual_output,
                "expected_output": expected_output,
                "error": None,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error checking code output: {str(e)}")
            return {
                "language": language,
                "is_correct": False,
                "actual_output": "",
                "error": str(e),
                "success": False,
            }

    @handle_service_errors(service_name="cs_tools")
    def validate_code_against_testcases(
        self,
        code: str,
        test_cases: List[Dict[str, Any]],
        language: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate code against multiple test cases.

        Args:
            code: The code to execute
            test_cases: List of test cases, each with input and expected_output
            language: The programming language
            user_id: Optional user ID for tracking usage

        Returns:
            Dictionary containing the validation results
        """
        self._init_dependencies()

        if user_id:
            self.tracking_service.track_tool_usage(
                user_id=user_id,
                tool_type="code_validator",
                action="validate_code_against_testcases",
                data={
                    "code": code,
                    "language": language,
                    "test_cases_count": len(test_cases),
                },
            )

        try:
            if language not in SUPPORTED_LANGUAGES:
                return {
                    "language": language,
                    "all_passed": False,
                    "passed_count": 0,
                    "failed_count": len(test_cases),
                    "total_count": len(test_cases),
                    "results": [],
                    "error": f"Unsupported language: {language}",
                    "success": True,
                }

            file_path = self._create_sandbox_file(code, language)

            if language == "python":
                syntax_result = self._check_python_syntax(file_path)
            elif language == "javascript":
                syntax_result = self._check_javascript_syntax(file_path)
            else:
                syntax_result = {
                    "is_valid": False,
                    "error": f"Syntax checking not implemented for {language}",
                }

            if not syntax_result["is_valid"]:
                return {
                    "language": language,
                    "all_passed": False,
                    "passed_count": 0,
                    "failed_count": len(test_cases),
                    "total_count": len(test_cases),
                    "results": [],
                    "error": syntax_result["error"],
                    "success": True,
                }

            test_results = []
            if language == "python":
                test_results = self._run_python_test_cases(code, test_cases)
            elif language == "javascript":
                test_results = self._run_javascript_test_cases(code, test_cases)

            passed_count = sum(1 for result in test_results if result["passed"])
            failed_count = len(test_cases) - passed_count

            return {
                "language": language,
                "all_passed": passed_count == len(test_cases),
                "passed_count": passed_count,
                "failed_count": failed_count,
                "total_count": len(test_cases),
                "results": test_results,
                "error": None,
                "success": True,
            }

        except Exception as e:
            logger.error(
                f"Error validating {language} code against test cases: {str(e)}"
            )
            return {
                "language": language,
                "all_passed": False,
                "passed_count": 0,
                "failed_count": len(test_cases),
                "total_count": len(test_cases),
                "results": [],
                "error": str(e),
                "success": False,
            }

    def _run_python_test_cases(
        self, code: str, test_cases: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Run Python code against test cases.

        Args:
            code: The Python code to test
            test_cases: List of test cases

        Returns:
            List of test results
        """
        results = []

        for i, test_case in enumerate(test_cases):
            test_file_path = os.path.join(self.sandbox_dir, f"test_case_{i}.py")

            with open(test_file_path, "w") as f:
                f.write(code + "\n\n")

                input_args = ", ".join(
                    [f"{k}={repr(v)}" for k, v in test_case["input"].items()]
                )
                expected_output = repr(test_case["expected_output"])

                f.write(
                    f"""
# Test case execution
try:
    result = add({input_args})
    expected = {expected_output}
    print(f"RESULT: {{repr(result)}}")
    print(f"EXPECTED: {{repr(expected)}}")
    print(f"PASSED: {{result == expected}}")
except Exception as e:
    print(f"ERROR: {{type(e).__name__}}: {{str(e)}}")
    print("PASSED: False")
"""
                )

            exec_result = self._execute_code_in_sandbox(test_file_path, "python")

            passed = False
            actual_output = None
            error = None

            if exec_result["success"]:
                output_lines = exec_result["output"].split("\n")
                for line in output_lines:
                    if line.startswith("RESULT: "):
                        try:
                            actual_output = eval(line[len("RESULT: ") :])
                        except:
                            actual_output = line[len("RESULT: ") :]
                    elif line.startswith("PASSED: "):
                        passed = line[len("PASSED: ") :].lower() == "true"
                    elif line.startswith("ERROR: "):
                        error = line[len("ERROR: ") :]
            else:
                error = exec_result["error"]

            results.append(
                {
                    "test_case_index": i,
                    "input": test_case["input"],
                    "expected_output": test_case["expected_output"],
                    "actual_output": actual_output,
                    "passed": passed,
                    "error": error,
                }
            )

        return results

    def _run_javascript_test_cases(
        self, code: str, test_cases: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Run JavaScript code against test cases.

        Args:
            code: The JavaScript code to test
            test_cases: List of test cases

        Returns:
            List of test results
        """
        results = []

        for i, test_case in enumerate(test_cases):
            test_file_path = os.path.join(self.sandbox_dir, f"test_case_{i}.js")

            with open(test_file_path, "w") as f:
                f.write(code + "\n\n")

                input_args = ", ".join(
                    [f"{repr(v)}" for k, v in test_case["input"].items()]
                )
                expected_output = repr(test_case["expected_output"])

                f.write(
                    f"""
// Test case execution
try {{
    const result = add({input_args});
    const expected = {expected_output};
    console.log(`RESULT: ${{JSON.stringify(result)}}`);
    console.log(`EXPECTED: ${{JSON.stringify(expected)}}`);
    console.log(`PASSED: ${{JSON.stringify(result) === JSON.stringify(expected)}}`);
}} catch (e) {{
    console.log(`ERROR: ${{e.name}}: ${{e.message}}`);
    console.log("PASSED: false");
}}
"""
                )

            exec_result = self._execute_code_in_sandbox(test_file_path, "javascript")

            passed = False
            actual_output = None
            error = None

            if exec_result["success"]:
                output_lines = exec_result["output"].split("\n")
                for line in output_lines:
                    if line.startswith("RESULT: "):
                        try:
                            actual_output = json.loads(line[len("RESULT: ") :])
                        except:
                            actual_output = line[len("RESULT: ") :]
                    elif line.startswith("PASSED: "):
                        passed_str = line[len("PASSED: ") :].lower()
                        passed = passed_str == "true"
                    elif line.startswith("ERROR: "):
                        error = line[len("ERROR: ") :]
            else:
                error = exec_result["error"]

            results.append(
                {
                    "test_case_index": i,
                    "input": test_case["input"],
                    "expected_output": test_case["expected_output"],
                    "actual_output": actual_output,
                    "passed": passed,
                    "error": error,
                }
            )

        return results

    @handle_service_errors(service_name="cs_tools")
    def prepare_algorithm_visualization(
        self, algorithm: str, data: List[Any], user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Prepare visualization data for common algorithms.

        Args:
            algorithm: The algorithm to visualize (e.g., "bubble_sort", "quick_sort")
            data: The input data for the algorithm
            user_id: Optional user ID for tracking usage

        Returns:
            Dictionary containing visualization steps
        """
        self._init_dependencies()

        if user_id:
            self.tracking_service.track_tool_usage(
                user_id=user_id,
                tool_type="algorithm_visualizer",
                action="prepare_visualization",
                data={"algorithm": algorithm, "data_size": len(data)},
            )

        supported_algorithms = {
            "bubble_sort": self._visualize_bubble_sort,
            "insertion_sort": self._visualize_insertion_sort,
            "selection_sort": self._visualize_selection_sort,
            "merge_sort": self._visualize_merge_sort,
            "quick_sort": self._visualize_quick_sort,
            "linear_search": self._visualize_linear_search,
            "binary_search": self._visualize_binary_search,
        }

        try:
            if algorithm not in supported_algorithms:
                return {
                    "algorithm": algorithm,
                    "success": False,
                    "error": f"Unsupported algorithm: {algorithm}. Supported algorithms: {', '.join(supported_algorithms.keys())}",
                }

            visualization_func = supported_algorithms[algorithm]
            steps, additional_data = visualization_func(data)

            return {
                "algorithm": algorithm,
                "steps": steps,
                "additional_data": additional_data,
                "success": True,
                "error": None,
            }

        except Exception as e:
            logger.error(
                f"Error preparing visualization for algorithm '{algorithm}': {str(e)}"
            )
            return {"algorithm": algorithm, "success": False, "error": str(e)}

    def _visualize_bubble_sort(
        self, data: List[Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Generate visualization steps for bubble sort algorithm.

        Args:
            data: List of items to sort

        Returns:
            Tuple of (steps, additional_data)
        """
        arr = data.copy()
        steps = []

        steps.append(
            {
                "type": "initial",
                "data": arr.copy(),
                "activeIndices": [],
                "comparedIndices": [],
                "description": "Initial array",
            }
        )

        n = len(arr)
        for i in range(n):
            swapped = False

            for j in range(0, n - i - 1):
                steps.append(
                    {
                        "type": "comparison",
                        "data": arr.copy(),
                        "activeIndices": [j, j + 1],
                        "comparedIndices": [j, j + 1],
                        "description": f"Comparing {arr[j]} and {arr[j + 1]}",
                    }
                )

                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
                    swapped = True

                    steps.append(
                        {
                            "type": "swap",
                            "data": arr.copy(),
                            "activeIndices": [j, j + 1],
                            "swappedIndices": [j, j + 1],
                            "description": f"Swapped {arr[j + 1]} and {arr[j]}",
                        }
                    )

            steps.append(
                {
                    "type": "pass_complete",
                    "data": arr.copy(),
                    "activeIndices": [],
                    "sortedIndices": list(range(n - i - 1, n)),
                    "description": f"Pass {i + 1} complete. {len(list(range(n - i - 1, n)))} elements sorted.",
                }
            )

            if not swapped:
                steps.append(
                    {
                        "type": "early_termination",
                        "data": arr.copy(),
                        "activeIndices": [],
                        "sortedIndices": list(range(n)),
                        "description": "No swaps needed. Array is sorted.",
                    }
                )
                break

        steps.append(
            {
                "type": "final",
                "data": arr.copy(),
                "activeIndices": [],
                "sortedIndices": list(range(n)),
                "description": "Array sorted",
            }
        )

        additional_data = {
            "time_complexity": {"best": "O(n)", "average": "O(n²)", "worst": "O(n²)"},
            "space_complexity": "O(1)",
            "stable": True,
            "comparisons": sum(1 for step in steps if step["type"] == "comparison"),
            "swaps": sum(1 for step in steps if step["type"] == "swap"),
        }

        return steps, additional_data

    def _visualize_insertion_sort(
        self, data: List[Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Generate visualization steps for insertion sort algorithm.

        Args:
            data: List of items to sort

        Returns:
            Tuple of (steps, additional_data)
        """
        arr = data.copy()
        steps = []

        steps.append(
            {
                "type": "initial",
                "data": arr.copy(),
                "activeIndices": [],
                "comparedIndices": [],
                "description": "Initial array",
            }
        )

        steps.append(
            {
                "type": "final",
                "data": sorted(arr),
                "activeIndices": [],
                "sortedIndices": list(range(len(arr))),
                "description": "Array sorted",
            }
        )

        additional_data = {
            "time_complexity": {"best": "O(n)", "average": "O(n²)", "worst": "O(n²)"},
            "space_complexity": "O(1)",
            "stable": True,
        }

        return steps, additional_data

    def _visualize_selection_sort(
        self, data: List[Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Placeholder for selection sort visualization"""
        return [{"type": "placeholder", "data": sorted(data)}], {}

    def _visualize_merge_sort(
        self, data: List[Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Placeholder for merge sort visualization"""
        return [{"type": "placeholder", "data": sorted(data)}], {}

    def _visualize_quick_sort(
        self, data: List[Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Placeholder for quick sort visualization"""
        return [{"type": "placeholder", "data": sorted(data)}], {}

    def _visualize_linear_search(
        self, data: List[Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Placeholder for linear search visualization"""
        return [{"type": "placeholder", "data": data}], {}

    def _visualize_binary_search(
        self, data: List[Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Placeholder for binary search visualization"""
        return [{"type": "placeholder", "data": sorted(data)}], {}

    @handle_service_errors(service_name="cs_tools")
    def prepare_data_structure_visualization(
        self, structure: str, data: List[Any], user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Prepare visualization data for common data structures.

        Args:
            structure: The data structure to visualize (e.g., "binary_tree", "linked_list")
            data: The input data for building the data structure
            user_id: Optional user ID for tracking usage

        Returns:
            Dictionary containing visualization data
        """
        self._init_dependencies()

        if user_id:
            self.tracking_service.track_tool_usage(
                user_id=user_id,
                tool_type="data_structure_visualizer",
                action="prepare_visualization",
                data={"structure": structure, "data_size": len(data)},
            )

        supported_structures = {
            "binary_tree": self._visualize_binary_tree,
            "binary_search_tree": self._visualize_binary_search_tree,
            "array": self._visualize_array,
            "linked_list": self._visualize_linked_list,
            "stack": self._visualize_stack,
            "queue": self._visualize_queue,
            "hash_table": self._visualize_hash_table,
            "heap": self._visualize_heap,
            "graph": self._visualize_graph,
        }

        try:
            if structure not in supported_structures:
                return {
                    "structure": structure,
                    "success": False,
                    "error": f"Unsupported data structure: {structure}. Supported structures: {', '.join(supported_structures.keys())}",
                }

            visualization_func = supported_structures[structure]
            visualization_data = visualization_func(data)

            return {
                "structure": structure,
                "visualization_data": visualization_data,
                "success": True,
                "error": None,
            }

        except Exception as e:
            logger.error(
                f"Error preparing visualization for data structure '{structure}': {str(e)}"
            )
            return {"structure": structure, "success": False, "error": str(e)}

    def _visualize_binary_tree(self, data: List[Any]) -> Dict[str, Any]:
        """
        Generate visualization data for a binary tree.

        Args:
            data: List of items to convert to a binary tree

        Returns:
            Dictionary containing tree structure
        """
        if not data:
            return {"type": "binary_tree", "nodes": [], "edges": []}

        class TreeNode:
            def __init__(self, value, id_num):
                self.value = value
                self.id = id_num
                self.left = None
                self.right = None

        nodes = []
        edges = []
        node_id = 0

        def create_tree_from_sorted_array(sorted_arr, start, end):
            nonlocal node_id
            if start > end:
                return None

            mid = (start + end) // 2
            current_id = node_id
            node_id += 1

            node = TreeNode(sorted_arr[mid], current_id)
            nodes.append(
                {
                    "id": node.id,
                    "value": node.value,
                    "position": {
                        "x": mid,  # Approximate position, to be adjusted by frontend
                        "y": start,  # Level in the tree
                    },
                }
            )

            node.left = create_tree_from_sorted_array(sorted_arr, start, mid - 1)
            if node.left:
                edges.append(
                    {"source": node.id, "target": node.left.id, "type": "left"}
                )

            node.right = create_tree_from_sorted_array(sorted_arr, mid + 1, end)
            if node.right:
                edges.append(
                    {"source": node.id, "target": node.right.id, "type": "right"}
                )

            return node

        sorted_data = sorted(data)
        create_tree_from_sorted_array(sorted_data, 0, len(sorted_data) - 1)

        return {
            "type": "binary_tree",
            "nodes": nodes,
            "edges": edges,
            "properties": {
                "balanced": True,
                "height": int(math.log2(len(data))) + 1 if data else 0,
                "node_count": len(data),
            },
        }

    def _visualize_binary_search_tree(self, data: List[Any]) -> Dict[str, Any]:
        """Placeholder for binary search tree visualization"""
        result = {"type": "binary_search_tree", "nodes": [], "edges": []}
        return result

    def _visualize_array(self, data: List[Any]) -> Dict[str, Any]:
        """Placeholder for array visualization"""
        nodes = [{"index": i, "value": value} for i, value in enumerate(data)]
        return {"type": "array", "nodes": nodes}

    def _visualize_linked_list(self, data: List[Any]) -> Dict[str, Any]:
        """Placeholder for linked list visualization"""
        return {"type": "linked_list", "values": data}

    def _visualize_stack(self, data: List[Any]) -> Dict[str, Any]:
        """Placeholder for stack visualization"""
        return {"type": "stack", "values": data}

    def _visualize_queue(self, data: List[Any]) -> Dict[str, Any]:
        """Placeholder for queue visualization"""
        return {"type": "queue", "values": data}

    def _visualize_hash_table(self, data: List[Any]) -> Dict[str, Any]:
        """Placeholder for hash table visualization"""
        return {"type": "hash_table", "values": data}

    def _visualize_heap(self, data: List[Any]) -> Dict[str, Any]:
        """Placeholder for heap visualization"""
        return {"type": "heap", "values": data}

    def _visualize_graph(self, data: List[Any]) -> Dict[str, Any]:
        """Placeholder for graph visualization"""
        return {"type": "graph", "nodes": data}

    def _create_sandbox_file(self, code: str, language: str) -> str:
        """
        Create a temporary file in the sandbox directory.

        Args:
            code: The code to write to the file
            language: The programming language

        Returns:
            Path to the created file
        """
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")

        extension = SUPPORTED_LANGUAGES[language]["extension"]
        file_path = os.path.join(self.sandbox_dir, f"code{extension}")

        with open(file_path, "w") as f:
            f.write(code)

        return file_path

    def _execute_code_in_sandbox(
        self,
        file_path: str,
        language: str,
        inputs: Optional[List[str]] = None,
        timeout: int = 5,
    ) -> Dict[str, Any]:
        """
        Execute code in a sandbox environment.

        Args:
            file_path: Path to the file containing the code
            language: The programming language
            inputs: Optional list of inputs to provide to the program
            timeout: Timeout in seconds

        Returns:
            Dictionary containing execution results
        """
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")

        command = [SUPPORTED_LANGUAGES[language]["command"], file_path]

        try:
            input_string = None
            if inputs:
                input_string = "\n".join(inputs).encode()

            start_time = time.time()
            process = subprocess.run(
                command,
                input=input_string,
                capture_output=True,
                text=True,
                timeout=timeout,  # in seconds
            )
            execution_time = time.time() - start_time

            if process.returncode != 0:
                return {
                    "output": "",
                    "error": process.stderr.strip()
                    or f"Process exited with code {process.returncode}",
                    "execution_time": execution_time,
                    "success": False,
                }

            return {
                "output": process.stdout.strip(),
                "error": None,
                "execution_time": execution_time,
                "success": True,
            }

        except subprocess.TimeoutExpired:
            return {
                "output": "",
                "error": f"Execution timed out after {timeout} seconds",
                "execution_time": timeout,
                "success": False,
            }
        except Exception as e:
            logger.error(f"Error executing code: {str(e)}")
            return {
                "output": "",
                "error": str(e),
                "execution_time": 0,
                "success": False,
            }
