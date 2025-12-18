from .error_handling import (MathtermindError, create_error_boundary,
                             handle_db_errors, handle_service_errors,
                             handle_ui_errors, report_error, safe_execute,
                             with_error_boundary)
from .logging import (CRITICAL, DEBUG, ERROR, INFO, WARNING, debug_mode,
                      get_logger, set_level)
from .logging import setup as setup_logging


def initialize(environment=None):
    """
    Initialize the core framework.

    This function initializes both the logging and error handling systems.

    Args:
        environment: The application environment (development, testing, production)
    """
    setup_logging(environment)

    logger = get_logger("mathtermind.core")
    logger.info(
        f"Core framework initialized in {environment or 'development'} environment"
    )

    return True
