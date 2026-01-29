"""
Centralized logging configuration for LinkedIn Automation.

Provides consistent logging setup across all modules with proper formatting
and configuration.
"""

import logging
from rich.console import Console
from rich.logging import RichHandler

console = Console()

def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance with rich formatting.
    
    Args:
        name: The name of the logger (typically __name__)
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if logger already exists
    if not logger.handlers:
        # Set level
        logger.setLevel(logging.INFO)
        
        # Create rich handler for console output
        rich_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=True,
            markup=True,
            rich_tracebacks=True,
            tracebacks_show_locals=True
        )
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        rich_handler.setFormatter(formatter)
        logger.addHandler(rich_handler)
    
    return logger