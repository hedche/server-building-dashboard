"""
Logging configuration for the Server Building Dashboard backend.
Creates separate log files for different components with rotation.
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from .config import settings


class LoggerSetup:
    """Centralized logger setup with multiple log files"""

    def __init__(self):
        self.log_dir = Path(settings.LOG_DIR)
        self.log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        self._ensure_log_directory()
        self._loggers = {}

    def _ensure_log_directory(self):
        """Create log directory if it doesn't exist"""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Fallback to local directory if we don't have permission
            print(f"Warning: Cannot write to {self.log_dir}, falling back to ./logs", file=sys.stderr)
            self.log_dir = Path("./logs")
            self.log_dir.mkdir(parents=True, exist_ok=True)

    def _create_file_handler(self, filename: str, level: int = None) -> RotatingFileHandler:
        """Create a rotating file handler"""
        log_file = self.log_dir / filename
        handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        handler.setLevel(level or self.log_level)

        # Detailed formatter with timestamp, level, module, and message
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-25s | %(funcName)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        return handler

    def _create_console_handler(self, level: int = None) -> logging.StreamHandler:
        """Create a console handler for stdout"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level or self.log_level)

        # Simpler formatter for console
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        return handler

    def get_logger(self, name: str, log_file: str = None) -> logging.Logger:
        """
        Get or create a logger with the specified name

        Args:
            name: Logger name (e.g., 'app.auth', 'app.api')
            log_file: Optional specific log file for this logger

        Returns:
            Configured logger instance
        """
        if name in self._loggers:
            return self._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        logger.propagate = False  # Don't propagate to root logger

        # Remove existing handlers to avoid duplicates
        logger.handlers = []

        # Add console handler
        logger.addHandler(self._create_console_handler())

        # Add file handler
        if log_file:
            logger.addHandler(self._create_file_handler(log_file))

        self._loggers[name] = logger
        return logger


# Global logger setup instance
logger_setup = LoggerSetup()

# Pre-configured loggers for different components
app_logger = logger_setup.get_logger('app.main', 'app.log')
auth_logger = logger_setup.get_logger('app.auth', 'auth.log')
api_logger = logger_setup.get_logger('app.api', 'api.log')
error_logger = logger_setup.get_logger('app.error', 'error.log')
security_logger = logger_setup.get_logger('app.security', 'security.log')


def log_request(endpoint: str, method: str, status_code: int, duration_ms: float, client_ip: str = None):
    """Log API request details"""
    msg = f"{method} {endpoint} - Status: {status_code} - Duration: {duration_ms:.2f}ms"
    if client_ip:
        msg += f" - IP: {client_ip}"

    if status_code >= 500:
        api_logger.error(msg)
        error_logger.error(msg)
    elif status_code >= 400:
        api_logger.warning(msg)
    else:
        api_logger.info(msg)


def log_auth_event(event: str, user_email: str = None, success: bool = True, details: str = None):
    """Log authentication events"""
    level = logging.INFO if success else logging.WARNING
    msg = f"{event}"
    if user_email:
        msg += f" - User: {user_email}"
    if details:
        msg += f" - {details}"

    auth_logger.log(level, msg)
    if not success:
        security_logger.warning(msg)


def log_security_event(event: str, severity: str = "INFO", details: dict = None):
    """Log security-related events"""
    level = getattr(logging, severity.upper(), logging.INFO)
    msg = f"SECURITY: {event}"
    if details:
        msg += f" - Details: {details}"

    security_logger.log(level, msg)
    if severity.upper() in ["WARNING", "ERROR", "CRITICAL"]:
        error_logger.log(level, msg)


def log_error(error: Exception, context: str = None, extra: dict = None):
    """Log error with full context"""
    msg = f"ERROR: {str(error)}"
    if context:
        msg = f"{context} - {msg}"

    error_logger.error(msg, exc_info=True, extra=extra or {})
    app_logger.error(msg)


# Log startup information
def log_startup():
    """Log application startup information"""
    app_logger.info("=" * 80)
    app_logger.info(f"Starting {settings.APP_NAME}")
    app_logger.info("=" * 80)

    # Define sensitive keys that should not be logged
    sensitive_keys = {
        'SECRET_KEY',
        'DATABASE_URL',  # May contain passwords
        'REDIS_URL',     # May contain passwords
    }

    # Log all non-sensitive configuration
    app_logger.info("Configuration:")
    app_logger.info("-" * 80)

    for key, value in sorted(settings.model_dump().items()):
        if key.upper() in sensitive_keys:
            app_logger.info(f"  {key}: <REDACTED>")
        elif isinstance(value, (str, int, bool)):
            app_logger.info(f"  {key}: {value}")
        elif isinstance(value, list):
            # For lists (like CORS_ORIGINS), show them nicely
            if len(value) == 0:
                app_logger.info(f"  {key}: []")
            elif len(value) <= 3:
                app_logger.info(f"  {key}: {value}")
            else:
                app_logger.info(f"  {key}: [{value[0]}, ... ({len(value)} total)]")
        elif value is None:
            app_logger.info(f"  {key}: None")
        else:
            app_logger.info(f"  {key}: {type(value).__name__}")

    app_logger.info("-" * 80)
    app_logger.info(f"Log Directory: {logger_setup.log_dir}")
    app_logger.info("=" * 80)
