import re
import sys
from subprocess import CompletedProcess
from typing import Callable, Tuple


# ---------------------------------------------------------------------------
# Core helper — 256-color ANSI wrapper (replaces the old 8-color _wrap_with)
# ---------------------------------------------------------------------------

def c(code: int, payload: str) -> str:
    """
    Wrap text with 256-color ANSI coloring.

    :param code: 256-color ANSI color code (0-255)
    :param payload: text to colorize immediately
    :return: returns a colored ANSI string
    """
    start = f"\033[38;5;{code}m"
    end = "\033[0m"

    result: str
    if not isinstance(payload, str):
        payload = str(payload)

    if "\033[" in payload:
        # Nested coloring — reapply outer color after every inner reset
        result = f"{start}{payload.replace(end, end + start)}{end}"
    else:
        result = f"{start}{payload}{end}"
    return result

def c_subprocess(code: int, payload: Tuple[Callable, Tuple]) -> CompletedProcess:
    """
    Wrap text with 256-color ANSI coloring.

    :param code: 256-color ANSI color code (0-255)
    :param payload: a function that requires
                    deferred RESET handling (e.g. For Direct TTY prompts).
                    Expected structure:
                      - Tuple[Callable, Tuple[Any]]: treated as (function, args)
                        to call with function(*args) and color active during execution
    :return: the result of calling the provided function with the appropriate
             coloring applied as a wrapper to ensure the color is active during
             the function's execution and properly reset afterward.
    """
    start = f"\033[38;5;{code}m"
    end = "\033[0m"

    print(start, end="", flush=True)
    result: CompletedProcess = payload[0](*payload[1])
    print(end, end="", flush=True)
    return result


def strip_ansi_color_codes(text: str) -> str:
    """
    Removes ANSI escape sequences from a string.

    :param text: The string to strip ANSI color codes from.
    :return: The string with ANSI color codes removed.
    """
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def clear_previous_lines(n: int, stream=sys.stdout, count_current_line: bool = True) -> None:
    """Move cursor up n lines, erasing each one."""
    if count_current_line:
        n += 1

    for _ in range(n):
        stream.write('\033[1A'  # move cursor up one line
                     '\033[2K') # erase entire line
    stream.flush()


RESET = "\033[0m"

# ---------------------------------------------------------------------------
# Gradient color tables (matching shell script palette exactly)
# ---------------------------------------------------------------------------

PURPLE_CODES = (54, 54, 91, 91, 129, 129, 171, 171)   # dark → light
BLUE_CODES   = (17, 17, 18, 19, 19, 20, 21, 21)        # navy → cyan-blue

# ---------------------------------------------------------------------------
# Retained unicode emoji variables
# ---------------------------------------------------------------------------

success = "\U00002705"
failed  = "\U0000274C"
warning = "\U000026A0"

# ---------------------------------------------------------------------------
# Gradient helper
# ---------------------------------------------------------------------------

def _gradient_str(text: str, *codes: int) -> str:
    """Spread color codes evenly across the characters of text."""
    length = len(text)
    if length == 0:
        return ""
    num_colors = len(codes)
    result = {}
    for i, ch in enumerate(text):
        ci = i * (num_colors - 1) // (length - 1 if length > 1 else 1)
        result[codes[ci]] = ch + result.get(codes[ci], "")
    return "".join([c(segment_color, segment_text) for segment_color, segment_text in result.items()])


# ---------------------------------------------------------------------------
# Header / footer builders (return str — callers decide when to print)
# ---------------------------------------------------------------------------

def section_header_string(title: str) -> str:
    """Purple gradient 80-char section header."""
    title_padded = f" {title} "
    total = 80
    prefix_eq = 5
    suffix_eq = total - prefix_eq - len(title_padded)
    if suffix_eq < 0:
        suffix_eq = 0
    prefix = _gradient_str("=" * prefix_eq, *PURPLE_CODES)
    suffix = _gradient_str("=" * suffix_eq, *reversed(PURPLE_CODES))
    return f"{prefix}{c(105, title_padded)}{suffix}"


def section_footer_string() -> str:
    """Full-width purple gradient footer bar (mirrors shell script exactly)."""
    total = 80
    prefix_eq = 5
    suffix_eq = total - prefix_eq // 2   # = 78; total printed chars = 83 (matches shell)
    prefix = _gradient_str("=" * prefix_eq, *PURPLE_CODES)
    suffix = _gradient_str("=" * suffix_eq, *reversed(PURPLE_CODES))
    return f"{prefix}{suffix}"


def step_header_string(title: str) -> str:
    """Blue gradient 80-char step header."""
    title_padded = f" {title} "
    total = 80
    prefix_eq = 5
    suffix_eq = total - prefix_eq - len(title_padded)
    if suffix_eq < 0:
        suffix_eq = 0
    prefix = _gradient_str("=" * prefix_eq, *BLUE_CODES)
    suffix = _gradient_str("=" * suffix_eq, *reversed(BLUE_CODES))
    return f"{prefix}{c(184, title_padded)}{suffix}"


def step_footer_string() -> str:
    """Full-width blue gradient footer bar (mirrors shell script exactly)."""
    total = 80
    prefix_eq = 5
    suffix_eq = total - prefix_eq // 2   # = 78; total printed chars = 83 (matches shell)
    prefix = _gradient_str("=" * prefix_eq, *BLUE_CODES)
    suffix = _gradient_str("=" * suffix_eq, *reversed(BLUE_CODES))
    return f"{prefix}{suffix}"


# ---------------------------------------------------------------------------
# 256-color palette grid
# ---------------------------------------------------------------------------

def _ansi_256_to_rgb(n: int) -> tuple[int, int, int]:
    """Approximate the RGB value of a 256-color ANSI index.

    The palette has three regions:
      0–15   : standard/system colors (hardcoded approximations)
      16–231 : 6×6×6 color cube
      232–255: 24-step grayscale ramp
    """
    if n < 16:
        standard = [
            (0,   0,   0  ), (128, 0,   0  ), (0,   128, 0  ), (128, 128, 0  ),
            (0,   0,   128), (128, 0,   128), (0,   128, 128), (192, 192, 192),
            (128, 128, 128), (255, 0,   0  ), (0,   255, 0  ), (255, 255, 0  ),
            (0,   0,   255), (255, 0,   255), (0,   255, 255), (255, 255, 255),
        ]
        return standard[n]
    elif n < 232:
        idx = n - 16
        b = idx % 6
        g = (idx // 6) % 6
        r = idx // 36
        def _v(x: int) -> int:
            return 0 if x == 0 else 55 + x * 40
        return _v(r), _v(g), _v(b)
    else:
        val = 8 + (n - 232) * 10
        return val, val, val


def _contrast_fg(n: int) -> int:
    """Return ANSI color 0 (black) or 15 (white), whichever contrasts better against n."""
    r, g, b = _ansi_256_to_rgb(n)
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return 0 if luminance > 128 else 15


def print_color_palette(show_block: bool = False, background: bool = False) -> None:
    """Print all 256 ANSI colors in a 16×16 grid.

    Each cell shows the color index styled in that color.

    :param show_block: When True, prefix each foreground cell with a '██'
                       swatch in the same color, making the grid wider but
                       easier to read. Ignored when background=True, since
                       the fill already acts as the swatch.
    :param background: When True, render each color as a background fill
                       instead of foreground text. The number is drawn in
                       black or white, whichever contrasts better.

    Cell anatomy (visible chars):
      foreground, no block : ' NNN '   (5 chars)
      foreground, block    : '██ NNN ' (8 chars)
      background           : ' NNN '   (5 chars, highlighted)
    """
    for i in range(256):
        num = f" {i:>3} "          # always ' NNN ' — consistent 5-char number field
        block = "██ "              # 3-char swatch prefix (foreground mode only)

        if background:
            bg  = f"\033[48;5;{i}m"
            fg  = f"\033[38;5;{_contrast_fg(i)}m"
            cell = f"{bg}{fg}{num}{RESET}"
        else:
            fg = f"\033[38;5;{i}m"
            if show_block:
                cell = f"{fg}{block}{num}{RESET}"
            else:
                cell = f"{fg}{num}{RESET}"

        print(cell, end="")
        if (i + 1) % 16 == 0:
            print()


# ---------------------------------------------------------------------------
# Print functions (side-effect only; no return value)
# ---------------------------------------------------------------------------
def string_printer(code: int) -> Callable[[str], str]:
    """Return a function that prints a message in the specified color code."""
    def printer(msg: str):
        return f"{c(code, msg)}"
    return printer


def prompt_string(msg: str) -> str:
    """Return a colorized prompt string for use with getpass.getpass(prompt=...)."""
    return string_printer(75)(msg)


def action_string(msg: str) -> str:
    return string_printer(75)(msg)


def success_string(msg: str) -> str:
    return string_printer(120)(msg)


def warning_string(msg: str) -> str:
    return string_printer(221)(msg)


def error_string(msg: str) -> str:
    return string_printer(210)(msg)


def standard_string(msg: str) -> str:
    return f"{RESET}{msg}"


def blank_string() -> str:
    return ""


# ---------------------------------------------------------------------------
# Smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":  # pragma: no cover
    print(section_header_string("Section Header Example"))
    print(section_footer_string())
    print(step_header_string("Step Header Example"))
    print(step_footer_string())
    print(action_string("This is an action message"))
    print(success_string(f"This is a success message {success}"))
    print(warning_string(f"This is a warning message {warning}"))
    print(error_string(f"This is an error message {failed}"))
    print(standard_string("This is a standard message"))
    blank_string()

    print(section_header_string("Foreground — numbers only"))
    print_color_palette()
    blank_string()
    print(section_header_string("Background"))
    print_color_palette(background=True)