"""
This module provides utility functions for logging messages with ANSI colour codes.
It includes functions for standard, error, verbose, and debug logging.

the script is intended specifically to override the built-in print for ease of use with colour,
printc is a separate, more feature-rich option extending the custom print function.

to import in script

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Utils')))
from printer import print, Colours, print_error, print_verbose, print_debug, printct


# example usages
print(Colours.GRAY, "This is a test message in gray.", file=sys.stderr)
printc("This is a test message in green.", "green", "Test", file=sys.stderr)

"""

import builtins
import sys
import os  # Import os for environment variable check
from typing import Optional, TextIO

class Console:
    @staticmethod
    def log(*objects, sep: str = ' ', end: str = '\n', file: Optional[TextIO] = None, flush: bool = False) -> None:
        """
        Logs a message to the console, duplicating the behavior of the built-in print function.
        :param objects: The objects to print.
        :param sep: String inserted between values, default is a space.
        :param end: String appended after the last value, default is a newline.
        :param file: A file-like object (stream); defaults to the current sys.stdout.
        :param flush: Whether to forcibly flush the stream.
        """
        builtins.print(*objects, sep=sep, end=end, file=file, flush=flush)

# --- ANSI colour Codes ---
class Colours:
    """
    A collection of ANSI colour codes for terminal text formatting.
    """
    RESET = '\033[0m'
    WHITE = '\033[97m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    GRAY = '\033[90m'
    GREY = GRAY
    DARK_GREEN = '\033[32m'
    DARKGRAY = '\033[38;5;240m'
    DARKGREY = DARKGRAY
    DARKCYAN = '\033[36m'
    DARKYELLOW = '\033[33m'
    DARKRED = '\033[31m'
    Strings = {
        'red': RED,
        'green': GREEN,
        'yellow': YELLOW,
        'blue': BLUE,
        'magenta': MAGENTA,
        'cyan': CYAN,
        'white': WHITE,
        'gray': GRAY,
        'grey': GRAY,
        'darkgreen': DARK_GREEN,
        'darkgray': DARKGRAY,
        'darkgrey': DARKGRAY,
        'darkcyan': DARKCYAN,
        'darkyellow': DARKYELLOW,
        'darkred': DARKRED,
        'reset': RESET,
    }


# --- old Logging Function ---
def print(colour: str, message: str) -> None:
    """
    Logs a message to the standard output stream with the specified colour.

    :param colour: The ANSI colour code to format the message.
    :param message: The message to log.
    """
    builtins.print(f"{colour}{message}{Colours.RESET}", file=sys.stdout)


# --- new Logging Functions ---

"""
Intentional conflict overriding built-in print()
Overriding print() is powerful but can cause confusion or break introspection/debugging
thats why all variables are optional
some built-in functions are not provided in the override and require the use of builtins.print() to use
this is a non issue as the built-in.print() is still available
"""
def printerprint(colour: str | None = "", prefix: str | None = "", prefixcolour: str | None = "", msg: str | None = None, fileout: Optional[TextIO] = sys.stdout, flush: Optional[bool] = False) -> None:
    """Prints a message to the console with optional colour and prefix support."""

    if msg is None or msg == "":
        printy(message="", fileout=fileout, flushParam=False)
    else:
        if prefix != "":
            prefix = f"{prefix}:{Colours.RESET} "
            if prefixcolour is None or prefixcolour == "":
                prefixcolour = Colours.GREEN
            else:
                if prefixcolour and prefixcolour.lower() in Colours.Strings:
                    prefixcolour = Colours.Strings[prefixcolour.lower()]

        if colour and colour.lower() in Colours.Strings:
            colour = Colours.Strings[colour.lower()]

        # outputs are printed in a two colour format, the first colour is the prefix always green or darkcyan
        # the second colour is the message colour, if not specified it defaults no colour

        printy(message=f"{prefixcolour}{prefix}{colour}{msg}{Colours.RESET}", fileout=fileout, flushParam=flush)


def printc(message: str | None = None, colour: str | None = None, prefix: str | None = None, fileout: Optional[TextIO] = sys.stdout, flush: Optional[bool] = False) -> None:
    """Prints a message to the console with optional colour and prefix support."""

    if message is None or message == "":
        printy(message="", fileout=fileout, flushParam=False)
    else:
        if prefix is None or prefix == "":
            prefix = ""
        else:
            prefix = f"{prefix}: {Colours.RESET}"

        # outputs are printed in a two colour format, the first colour is the prefix always green or darkcyan
        # the second colour is the message colour, if not specified it defaults no colour

        if colour and colour.lower() in Colours.Strings:
            printy(message=f"{Colours.Strings['green']}{prefix}{Colours.Strings[colour.lower()]}{message}{Colours.RESET}", fileout=fileout, flushParam=flush)
        else:
            printy(message=f"{Colours.Strings['darkcyan']}{prefix}{Colours.Strings['darkcyan']}{message}{Colours.RESET}", fileout=fileout, flushParam=flush)

def printy(
    colour: Optional[str] = None,
    message: Optional[str] = None,
    fileout: Optional[TextIO] = sys.stdout,
    flushParam: Optional[bool] = False
) -> None:
    """
    Logs a message to the standard output stream with the specified colour.

    :param colour: The ANSI colour code to format the message.
    :param message: The message to log.
    """

    if colour is None:
        colour = Colours.RESET

    if message is None or message == "":
        builtins.print("", file=fileout, flush=flushParam)
    elif colour not in Colours.__dict__.values():
        builtins.print(message, file=fileout, flush=flushParam)
    else:
        builtins.print(f"{colour}{message}{Colours.RESET}", file=fileout, flush=flushParam)


def print_error(message: str) -> None:
    """
    Logs an error message to the standard error stream.

    :param message: The error message to log.
    """
    printc(f"{message}", "red", "ERROR")

def print_verbose(message: str) -> None:
    """
    Logs a verbose message if verbose logging is enabled.

    :param message: The verbose message to log.
    """
    if "VERBOSE" in os.environ and os.environ["VERBOSE"].lower() == "true":
        printc(f"VERBOSE: {message}", "grey", "VERBOSE")

def print_debug(message: str) -> None:
    """
    Logs a debug message if debugging is enabled.

    :param message: The debug message to log.
    """
    if "DEBUG" in os.environ and os.environ["DEBUG"].lower() == "true":
        printc(f"DEBUG: {message}", "magenta", "DEBUG")
