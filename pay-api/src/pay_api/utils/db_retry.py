"""Database retry utilities for handling network connectivity issues."""

import time
from functools import wraps
from typing import Any, Callable

from flask import current_app
from sqlalchemy.exc import InterfaceError, OperationalError
from pg8000.exceptions import InterfaceError as PG8000InterfaceError


def db_retry(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry database operations on network errors.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            retry_count = 0
            current_delay = delay
            
            while retry_count < max_retries:
                try:
                    return func(*args, **kwargs)
                except (InterfaceError, OperationalError, PG8000InterfaceError) as e:
                    retry_count += 1
                    error_msg = str(e).lower()
                    
                    # Only retry on network-related errors
                    if any(term in error_msg for term in ['network error', 'broken pipe', 'connection closed', 'timeout']):
                        if retry_count < max_retries:
                            current_app.logger.warning(
                                f"Database network error (attempt {retry_count}/{max_retries}): {e}. "
                                f"Retrying in {current_delay} seconds..."
                            )
                            time.sleep(current_delay)
                            current_delay *= backoff
                            continue
                    
                    # Re-raise if not a retryable error or max retries reached
                    current_app.logger.error(f"Database error after {retry_count} attempts: {e}")
                    raise
                except Exception as e:
                    # Don't retry non-database errors
                    current_app.logger.error(f"Non-database error: {e}")
                    raise
            
            # This shouldn't be reached, but just in case
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
