import re


# ============================================================
# Core ANSI helpers
# ============================================================

RESET = "\033[0m"


def _wrap_with(code, light=False):
    """
    Wrap text with a basic 8-color ANSI code.

    :param code: ANSI color code (e.g. 31 for red)
    :param light: Whether to use the bold/light variant

    :return: function that takes text and returns colored ANSI string
    """
    start = f"\033[{('1;' if light else '')}{code}m"
    end = RESET

    def inner(text):
        if not isinstance(text, str):
            text = str(text)
        if "\033[" in text:
            return f"{start}{text.replace(end, end + start)}{end}"
        else:
            return f"{start}{text}{end}"

    return inner


def _wrap_with_256(n):
    """
    Wrap text with a 256-color ANSI foreground code.

    :param n: 256-color palette index (0-255)

    :return: function that takes text and returns colored ANSI string
    """
    start = f"\033[38;5;{n}m"
    end = RESET

    def inner(text):
        if not isinstance(text, str):
            text = str(text)
        if "\033[" in text:
            return f"{start}{text.replace(end, end + start)}{end}"
        else:
            return f"{start}{text}{end}"

    return inner


def c(n):
    """
    Return the raw ANSI escape sequence for 256-color foreground index *n*.
    Equivalent to the bash helper:  c() { printf '\\033[38;5;%sm' "$1"; }

    :param n: 256-color palette index (0-255)
    :return: ANSI escape string (no trailing reset)
    """
    return f"\033[38;5;{n}m"


def strip_ansi_color_codes(text):
    """
    Remove ANSI escape sequences from a string.

    :param text: The string to strip.
    :return: Plain string with all ANSI codes removed.
    """
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


# ============================================================
# Basic 8-color convenience wrappers (kept for compatibility)
# ============================================================

red = _wrap_with("31")
green = _wrap_with("32")
yellow = _wrap_with("33")
blue = _wrap_with("34")
magenta = _wrap_with("35")
cyan = _wrap_with("36")
white = _wrap_with("37")
light_red = _wrap_with("31", light=True)
light_green = _wrap_with("32", light=True)
light_yellow = _wrap_with("33", light=True)
light_blue = _wrap_with("34", light=True)
light_magenta = _wrap_with("35", light=True)
light_cyan = _wrap_with("36", light=True)
light_white = _wrap_with("37", light=True)
default = _wrap_with("39")


# ============================================================
# 256-color palette — named wrappers
# ============================================================

# Purple gradient (8 stops): dark → light
P0 = c(54)   # darkest purple
P1 = c(54)
P2 = c(91)
P3 = c(91)
P4 = c(129)
P5 = c(129)
P6 = c(171)
P7 = c(171)  # lightest purple

# Blue gradient (8 stops): navy → cyan-blue
B0 = c(17)   # darkest navy
B1 = c(17)
B2 = c(18)
B3 = c(19)
B4 = c(19)
B5 = c(20)
B6 = c(21)
B7 = c(21)   # lightest cyan-blue

# Section / step title colors
CLR_SECTION_TITLE = c(105)   # medium purple  — section header title
CLR_STEP_TITLE    = c(184)   # olive/yellow   — step header title

# Semantic colors
CLR_ACTION      = c(75)    # light blue    — action text
CLR_SUCCESS     = c(120)   # light green   — success
CLR_ACTION_VAR  = c(183)   # lavender      — variables in action strings
CLR_ERROR       = c(210)   # light red     — error text
CLR_ERROR_VAR   = c(227)   # yellow        — variables in error strings
CLR_WARN        = c(221)   # yellow        — warning text
CLR_WARN_VAR    = c(183)   # lavender      — variables in warning strings

# 256-color semantic wrappers
color_action     = _wrap_with_256(75)
color_success    = _wrap_with_256(120)
color_action_var = _wrap_with_256(183)
color_error      = _wrap_with_256(210)
color_error_var  = _wrap_with_256(227)
color_warn       = _wrap_with_256(221)
color_warn_var   = _wrap_with_256(183)
color_standard   = _wrap_with("39")


# ============================================================
# Status emoji
# ============================================================

success = "\U00002705"
failed  = "\U0000274C"
warning = "\U000026A0"


# ============================================================
# Gradient helpers
# ============================================================

def _gradient_str(text, *colors):
    """
    Build a gradient string by spreading *colors* evenly across *text*.

    Each character in *text* is colored with the closest color stop.
    A terminal reset is appended at the end.

    :param text:   The string to colorize.
    :param colors: Raw ANSI escape sequences (e.g. from :func:`c`), spread
                   evenly left-to-right across the text.
    :return: Colorized string with trailing reset.
    """
    length = len(text)
    num_colors = len(colors)
    if length == 0 or num_colors == 0:
        return text
    result = ""
    for i, char in enumerate(text):
        ci = i * (num_colors - 1) // (length - 1 if length > 1 else 1)
        result += colors[ci] + char
    return result + RESET


# ============================================================
# Gradient header / footer helpers
# ============================================================

def section_header_string(title):
    """
    Build an 80-char section header with a purple gradient on the ``=`` bars
    and the title in :data:`CLR_SECTION_TITLE`.

    ``=====`` (dark→light) `` {title} `` ``========================`` (light→dark)

    :param title: Header title text.
    :return: Formatted header string (no trailing newline).
    """
    title_with_spaces = f" {title} "
    total = 80
    prefix_eq = 5
    suffix_eq = max(0, total - prefix_eq - len(title_with_spaces))

    prefix = _gradient_str("=" * prefix_eq, P0, P1, P2, P3, P4, P5, P6, P7)
    suffix = _gradient_str("=" * suffix_eq, P7, P6, P5, P4, P3, P2, P1, P0)
    return f"{prefix}{CLR_SECTION_TITLE}{title_with_spaces}{RESET}{suffix}"


def section_footer_string():
    """
    Build an 80-char section footer with a purple gradient on the ``=`` bar.

    :return: Formatted footer string (no trailing newline).
    """
    total = 80
    prefix_eq = 5
    suffix_eq = max(0, total - prefix_eq // 2)

    prefix = _gradient_str("=" * prefix_eq, P0, P1, P2, P3, P4, P5, P6, P7)
    suffix = _gradient_str("=" * suffix_eq, P7, P6, P5, P4, P3, P2, P1, P0)
    return f"{prefix}{suffix}"


def step_header_string(title):
    """
    Build an 80-char step header with a blue gradient on the ``=`` bars
    and the title in :data:`CLR_STEP_TITLE`.

    ``=====`` (dark→light) `` {title} `` ``=========================`` (light→dark)

    :param title: Step title text.
    :return: Formatted header string (no trailing newline).
    """
    title_with_spaces = f" {title} "
    total = 80
    prefix_eq = 5
    suffix_eq = max(0, total - prefix_eq - len(title_with_spaces))

    prefix = _gradient_str("=" * prefix_eq, B0, B1, B2, B3, B4, B5, B6, B7)
    suffix = _gradient_str("=" * suffix_eq, B7, B6, B5, B4, B3, B2, B1, B0)
    return f"{prefix}{CLR_STEP_TITLE}{title_with_spaces}{RESET}{suffix}"


def step_footer_string():
    """
    Build an 80-char step footer with a blue gradient on the ``=`` bar.

    :return: Formatted footer string (no trailing newline).
    """
    total = 80
    prefix_eq = 5
    suffix_eq = max(0, total - prefix_eq // 2)

    prefix = _gradient_str("=" * prefix_eq, B0, B1, B2, B3, B4, B5, B6, B7)
    suffix = _gradient_str("=" * suffix_eq, B7, B6, B5, B4, B3, B2, B1, B0)
    return f"{prefix}{suffix}"


# ============================================================
# Module self-test
# ============================================================

if __name__ == "__main__":  # pragma: no cover
    # Basic 8-color checks
    print(green("THIS IS GREEN"))
    print(red("THIS IS RED"))
    print(yellow("THIS IS YELLOW"))
    print(blue("THIS IS BLUE"))
    print(magenta("THIS IS MAGENTA"))
    print(cyan("THIS IS CYAN"))
    print(white("THIS IS WHITE"))
    print(light_green("THIS IS LIGHT GREEN"))
    print(light_red("THIS IS LIGHT RED"))
    print(light_yellow("THIS IS LIGHT YELLOW"))
    print(light_blue("THIS IS LIGHT BLUE"))
    print(light_magenta("THIS IS LIGHT MAGENTA"))
    print(light_cyan("THIS IS LIGHT CYAN"))
    print(light_white("THIS IS LIGHT WHITE"))
    print(default("THIS IS DEFAULT"))
    print()

    # 256-color semantic checks
    print(color_action(f"Action text {success}"))
    print(color_success(f"Success text {success}"))
    print(color_warn(f"Warning text {warning}"))
    print(color_error(f"Error text {failed}"))
    print()

    # Gradient header/footer helpers
    print(section_header_string("My Section Title"))
    print(color_standard("  Some section content goes here."))
    print(section_footer_string())
    print()
    print(step_header_string("My Step Title"))
    print(color_standard("  Some step content goes here."))
    print(step_footer_string())
