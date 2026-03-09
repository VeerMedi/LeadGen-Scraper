"""
Logging configuration for Lead Scraper System
Provides centralized logging with file rotation
"""
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
from pathlib import Path


# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent.parent / 'logs'
LOGS_DIR.mkdir(exist_ok=True)


class ScraperLogger:
    """Centralized logger for the scraper system"""
    
    def __init__(self, name: str = 'lead_scraper'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup file and console handlers"""
        # File handler with rotation (10MB max, keep 5 backups)
        log_file = LOGS_DIR / f'scraper_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str, exc_info=False):
        """Log error message"""
        self.logger.error(message, exc_info=exc_info)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def scraping_started(self, platform: str, query: str):
        """Log scraping start"""
        self.info(f"[{platform.upper()}] Scraping started: {query}")
    
    def scraping_completed(self, platform: str, leads_found: int, duration: float):
        """Log scraping completion"""
        self.info(f"[{platform.upper()}] Completed: {leads_found} leads in {duration:.2f}s")
    
    def scraping_failed(self, platform: str, error: str):
        """Log scraping failure"""
        self.error(f"[{platform.upper()}] Failed: {error}")
    
    def processing_started(self, stage: str, count: int):
        """Log processing start"""
        self.info(f"[PROCESSING] {stage} started: {count} items")
    
    def processing_completed(self, stage: str, count: int):
        """Log processing completion"""
        self.info(f"[PROCESSING] {stage} completed: {count} items")
    
    def llm_request(self, operation: str, tokens_used: int = None):
        """Log LLM API request"""
        msg = f"[LLM] {operation}"
        if tokens_used:
            msg += f" - {tokens_used} tokens"
        self.info(msg)
    
    def database_operation(self, operation: str, count: int):
        """Log database operation"""
        self.info(f"[DATABASE] {operation}: {count} records")
    
    def api_rate_limit(self, service: str, retry_after: int):
        """Log rate limit hit"""
        self.warning(f"[RATE LIMIT] {service} - retry after {retry_after}s")


# Global logger instance
logger = ScraperLogger()


# Convenience functions
def log_info(message: str):
    """Log info message"""
    logger.info(message)


def log_warning(message: str):
    """Log warning message"""
    logger.warning(message)


def log_error(message: str, exc_info=False):
    """Log error message"""
    logger.error(message, exc_info=exc_info)


def log_debug(message: str):
    """Log debug message"""
    logger.debug(message)


def log_scraping_event(platform: str, event: str, **kwargs):
    """
    Log scraping events
    
    Args:
        platform: Platform name (linkedin, reddit, etc.)
        event: Event type (started, completed, failed)
        **kwargs: Additional data (leads_found, duration, error, etc.)
    """
    if event == 'started':
        logger.scraping_started(platform, kwargs.get('query', ''))
    elif event == 'completed':
        logger.scraping_completed(
            platform, 
            kwargs.get('leads_found', 0),
            kwargs.get('duration', 0)
        )
    elif event == 'failed':
        logger.scraping_failed(platform, kwargs.get('error', 'Unknown error'))


# Example usage
if __name__ == "__main__":
    # Test logging
    print("Testing logger...")
    
    logger.info("System started")
    logger.scraping_started("linkedin", "Software Engineer in NYC")
    logger.scraping_completed("linkedin", 25, 45.3)
    logger.processing_started("deduplication", 100)
    logger.processing_completed("deduplication", 85)
    logger.llm_request("keyword_extraction", 150)
    logger.database_operation("insert", 85)
    
    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.error(f"Test error occurred: {e}", exc_info=True)
    
    print(f"\nLogs written to: {LOGS_DIR}")
    print("Check the log file for output")
