"""
This module provides utility functions for logging messages with ANSI colour codes.
It includes functions for standard, error, verbose, and debug logging.
"""

import builtins
import sys
import os  # Import os for environment variable check

# --- ANSI colour Codes ---
class colours(object):
    """
    A collection of ANSI colour codes for terminal text formatting.
    """
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    GRAY = '\033[90m'
    DARK_GREEN = '\033[32m'

# --- Logging Functions ---
def print(colour: str, message: str) -> None:  # Removed default colour
    """
    Logs a message to the standard output stream with the specified colour.

    :param colour: The ANSI colour code to format the message.
    :param message: The message to log.
    """
    builtins.print(f"{colour}{message}{colours.RESET}", file=sys.stdout)

def print_error(message: str) -> None:
    """
    Logs an error message to the standard error stream.

    :param message: The error message to log.
    """
    builtins.print(f"{colours.RED}{message}{colours.RESET}", file=sys.stderr)

def print_verbose(message: str) -> None:
    """
    Logs a verbose message if verbose logging is enabled.

    :param message: The verbose message to log.
    """
    if "VERBOSE" in os.environ and os.environ["VERBOSE"].lower() == "true":
        print(colours.GRAY, f"VERBOSE: {message}")

def print_debug(message: str) -> None:
    """
    Logs a debug message if debugging is enabled.

    :param message: The debug message to log.
    """
    if "DEBUG" in os.environ and os.environ["DEBUG"].lower() == "true":
        print(colours.MAGENTA, f"DEBUG: {message}")
