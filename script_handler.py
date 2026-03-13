#!/usr/bin/env python3
"""
Terminal output and command execution utilities.
Converted from Bash color/formatting and run_cmd helpers.
Color code reference: https://misc.flogisoft.com/bash/tip_colors_and_formatting
"""
import re
import subprocess
import sys
import traceback
from typing import List, Optional, Union


# ANSI 256-color escape: \e[38;5;<n>m
def _ansi_256(n: int) -> str:
    return f"\033[38;5;{n}m"


def _semantic_color_names() -> List[str]:
    """Return a list of 256 semantic names for ANSI 256 foreground indices."""
    # Indices that keep existing constant names (RED, LIGHTRED, BLUE, etc.)
    existing = {
        1: "LIGHTRED",
        15: "WHITE",
        20: "BLUE",
        27: "LIGHTBLUE",
        34: "GREEN",
        54: "PURPLE",
        74: "CYAN",
        82: "LIGHTGREEN",
        87: "LIGHTCYAN",
        93: "LIGHTPURPLE",
        94: "BROWN",
        124: "RED",
        137: "LIGHTBROWN",
        226: "YELLOW",
        228: "LIGHTYELLOW",
        238: "DARKGRAY",
        248: "LIGHTGRAY",
    }
    names = []
    # 0-15: standard 16-color palette
    std16 = [
        "BLACK",
        "LIGHTRED",  # 1
        "DARKGREEN",
        "OLIVE",
        "NAVY",
        "DARKMAGENTA",
        "TEAL",
        "SILVER",
        "DARKGREY",
        "BRIGHTRED",
        "BRIGHTGREEN",
        "BRIGHTYELLOW",
        "ROYALBLUE",
        "FUCHSIA",
        "AQUA",
        "WHITE",  # 15
    ]
    for i in range(16):
        names.append(existing.get(i, std16[i]))
    # 16-231: 6x6x6 RGB cube -> CUBE_Rr_Gg_Bb
    for i in range(16, 232):
        if i in existing:
            names.append(existing[i])
        else:
            x = i - 16
            r, x = x // 36, x % 36
            g, b = x // 6, x % 6
            names.append(f"CUBE_R{r}_G{g}_B{b}")
    # 232-255: grayscale
    for i in range(232, 256):
        if i in existing:
            names.append(existing[i])
        else:
            names.append(f"GREY{i - 232}")
    return names


class ScriptOutput:
    """Instantiable helper for colored terminal output and command execution."""

    # Color constants (ANSI 256)
    RED = _ansi_256(124)
    LIGHTRED = _ansi_256(1)
    GREEN = _ansi_256(34)
    LIGHTGREEN = _ansi_256(82)
    BROWN = _ansi_256(94)
    LIGHTBROWN = _ansi_256(137)
    YELLOW = _ansi_256(226)
    LIGHTYELLOW = _ansi_256(228)
    BLUE = _ansi_256(20)
    LIGHTBLUE = _ansi_256(27)
    CYAN = _ansi_256(74)
    LIGHTCYAN = _ansi_256(87)
    PURPLE = _ansi_256(54)
    LIGHTPURPLE = _ansi_256(93)
    DARKGRAY = _ansi_256(238)
    LIGHTGRAY = _ansi_256(248)
    WHITE = _ansi_256(15)
    NC = "\033[0m"

    # All 256 foreground colors by semantic name (built from _semantic_color_names())
    _COLOR_BY_NAME = {
        name: _ansi_256(i) for i, name in enumerate(_semantic_color_names())
    }
    _COLOR_BY_NAME["NC"] = NC

    _ANSI_STRIP = re.compile(r"\033\[[0-9;]*m")
    MAX_HEADER_LEN = 80

    def __init__(self, stream=None, dry_run: bool = False):
        """Optional stream for print (default: sys.stdout)."""
        self._stream = stream if stream is not None else sys.stdout
        self.dry_run = dry_run

    def _print(self, text: str, end: str = "\n") -> None:
        """Write text to the configured stream."""
        print(text, end=end, file=self._stream, flush=True)

    @classmethod
    def _strip_ansi(cls, text: str) -> str:
        """Remove ANSI escape sequences for length calculation."""
        return cls._ANSI_STRIP.sub("", text)

    def colorize_string(self, color_name: str, text: str) -> str:
        """
        Wrap text in the given color. Nested ANSI resets are replaced with
        reset+color so the outer color continues after inner formatting.
        """
        color = self._COLOR_BY_NAME.get(color_name.upper(), self.NC)
        reset = self.NC
        outer_reset = reset + color
        # Replace reset codes with reset+color so outer color continues
        expanded = text.replace(reset, outer_reset)
        return f"{color}{expanded}{reset}"

    def colorize_string_print(self, color_name: str, text: str, end: str = "\n") -> None:
        """Print text via colorize_string."""
        self._print(self.colorize_string(color_name, text), end=end)

    def print_color_reference(
        self,
        columns: int = 13,
        column_width: int = 20,
        print_output: bool = False,
    ) -> str:
        """
        Return a grid string of all 256 semantic color names, each name shown
        in the color it represents. Use print(out.print_color_reference()) to
        display it in the terminal.
        """
        names = _semantic_color_names()
        lines = []
        for i in range(0, 256, columns):
            row_names = names[i : i + columns]
            cells = []
            for name in row_names:
                colored = self.colorize_string(name, name)
                visible_len = len(self._strip_ansi(colored))
                padding = max(0, column_width - visible_len)
                cells.append(colored + self.NC + " " * padding)
            lines.append("".join(cells))
        lines.append(self.NC)
        if print_output:
            print("\n".join(lines))
        return "\n".join(lines)

    def colorize_padding(self, string: str, start: int = 21, end: int = 16) -> str:
        """Color each character with a gradient from start to end (256-color indices)."""
        if not string:
            raise ValueError("colorize_padding: string may not be empty")
        n = len(string)
        parts = []
        for i in range(n):
            char = string[i]
            if n == 1:
                color_idx = start
            else:
                color_idx = (start * (n - 1) + (end - start) * i) // (n - 1)
            parts.append(f"\033[38;5;{color_idx}m{char}{self.NC}")
        return "".join(parts)

    def colorize_padding_series(
        self, string: str, series: Union[str, List[int]]
    ) -> str:
        """
        Color each character using a series of 256-color indices.
        series: space-separated string like '54 91 129 171' or list of ints.
        """
        if not string:
            raise ValueError("colorize_padding_series: string may not be empty")
        if isinstance(series, str):
            s_arr = [int(x) for x in series.split() if x.strip()]
        else:
            s_arr = list(series)
        if not s_arr:
            raise ValueError(
                "colorize_padding_series: series may not be empty (e.g. '54 91 129 171')"
            )
        n = len(string)
        k = len(s_arr)
        parts = []
        for i in range(n):
            char = string[i]
            if n == 1:
                index = 0
            else:
                b = n // k
                r = n % k
                if i < r * (b + 1):
                    index = i // (b + 1)
                else:
                    index = r + (i - r * (b + 1)) // b
            color_idx = s_arr[index]
            parts.append(f"\033[38;5;{color_idx}m{char}{self.NC}")
        return "".join(parts)

    def section_header_string(self, *parts: str) -> str:
        """Section header with gradient padding around the title (max length 80)."""
        output_text = " ".join(str(p) for p in parts)
        text_count = len(self._strip_ansi(output_text))
        left_len = 6
        right_len = max(0, self.MAX_HEADER_LEN - left_len - 1 - text_count - 1)
        left_pad = "=" * left_len
        right_pad = "=" * right_len
        left_colored = self.colorize_padding_series(left_pad, "54 91 129 171")
        right_colored = self.colorize_padding_series(right_pad, "171 129 91 54")
        return self.colorize_string(
            "LIGHTBROWN", f"{left_colored} {output_text} {right_colored}"
        )

    def section_header(self, *parts: str) -> None:
        """Print section header."""
        self._print(self.section_header_string(*parts))

    def section_footer_string(self) -> str:
        """Section footer with gradient padding (max length 80)."""
        half = self.MAX_HEADER_LEN // 2
        left = "=" * half
        right = "=" * (self.MAX_HEADER_LEN - half)
        left_colored = self.colorize_padding_series(left, "54 91 129 171")
        right_colored = self.colorize_padding_series(right, "171 129 91 54")
        return self.colorize_string("NC", left_colored + right_colored)

    def section_footer(self) -> None:
        """Print section footer."""
        self._print(self.section_footer_string())

    def step_header_string(self, *parts: str) -> str:
        """Step header with gradient padding, cyan theme (max length 80)."""
        output_text = " ".join(str(p) for p in parts)
        text_count = len(self._strip_ansi(output_text))
        left_len = 6
        right_len = max(0, self.MAX_HEADER_LEN - left_len - 1 - text_count - 1)
        left_pad = "=" * left_len
        right_pad = "=" * right_len
        left_colored = self.colorize_padding(left_pad, 17, 21)
        right_colored = self.colorize_padding(right_pad, 21, 17)
        return self.colorize_string("CYAN", f"{left_colored} {output_text} {right_colored}")

    def step_header(self, *parts: str) -> None:
        """Print step header."""
        self._print(self.step_header_string(*parts))

    def step_footer_string(self) -> str:
        """Step footer with gradient padding (max length 80)."""
        half = self.MAX_HEADER_LEN // 2
        left = "=" * half
        right = "=" * (self.MAX_HEADER_LEN - half)
        left_colored = self.colorize_padding(left, 17, 21)
        right_colored = self.colorize_padding(right, 21, 17)
        return self.colorize_string("NC", left_colored + right_colored)

    def step_footer(self) -> None:
        """Print step footer."""
        self._print(self.step_footer_string())

    def action_string(self, *parts: str) -> str:
        """Return text colored as an action (light blue)."""
        return self.colorize_string("LIGHTBLUE", " ".join(str(p) for p in parts))

    def action(self, *parts: str) -> None:
        """Print action message."""
        self._print(self.action_string(*parts))

    def error_string(self, *parts: str) -> str:
        """Return text colored as error (light red)."""
        return self.colorize_string("LIGHTRED", " ".join(str(p) for p in parts))

    def error(self, *parts: str) -> None:
        """Print error message (to stderr if stream is stdout)."""
        msg = self.error_string(*parts)
        target = self._stream if self._stream is not sys.stdout else sys.stderr
        print(msg, file=target, flush=True)

    def run_cmd(
        self,
        command: Union[str, List[str]],
        *,
        check: bool = True,
        capture: bool = True,
        shell: Optional[bool] = None,
    ) -> subprocess.CompletedProcess:
        """
        Run a command. By default captures output and exits (raises) on non-zero.

        command: string (then shell=True) or list of args (then shell=False).
        check: if True, raise CalledProcessError on non-zero exit (and print error).
        capture: if True, capture stdout/stderr; if False, inherit (live output).
        shell: None = infer from type (str->True, list->False), else use given value.

        Returns CompletedProcess. On check=True and failure, prints error and exits.
        """
        if isinstance(command, str):
            use_shell = shell if shell is not None else True
            cmd_for_display = command
        else:
            use_shell = shell if shell is not None else False
            cmd_for_display = " ".join(command) if isinstance(command, (list, tuple)) else str(command)

        try:
            if self.dry_run:
                self.action(f"Dry run: would execute command {self.LIGHTPURPLE}{cmd_for_display}{self.NC}")
                return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")
            result = subprocess.run(
                command,
                shell=use_shell,
                capture_output=capture,
                text=True,
                check=False,
            )
        except Exception as e:
            self.error(f"Error executing command {self.LIGHTPURPLE}{cmd_for_display}{self.NC}")
            self.error(str(e))
            sys.exit(1)

        if result.returncode != 0 and check:
            self.error(f"Error executing command {self.LIGHTPURPLE}{cmd_for_display}{self.NC}")
            if result.stdout:
                self.error(result.stdout)
            if result.stderr:
                self.error(result.stderr)
            sys.exit(result.returncode)
        return result

    def error_handling_execute(
        self,
        task_step_output: str,
        command: Union[str, List[str]],
        **run_kw,
    ) -> subprocess.CompletedProcess:
        """Print action message then run command (same kwargs as run_cmd)."""
        self.action(task_step_output)
        return self.run_cmd(command, **run_kw)


def _main() -> None:
    out = ScriptOutput()

    # Section and step headers/footers
    out.section_header("Demo Section")
    out.step_header("Step 1: Colored messages")
    out.action("Action message (light blue)")
    out._print(out.action_string("action_string() returns styled text"))
    out._print(out.error_string("error_string() for error-style text (no stderr)"))

    out.step_header("Step 2: run_cmd (list, no shell)")
    out.run_cmd([sys.executable, "-c", "print('Hello from subprocess')"])

    out.step_header("Step 3: run_cmd (string, shell)")
    out.run_cmd("echo Shell command OK", shell=True)

    out.step_header("Step 4: error_handling_execute - Success")
    out.error_handling_execute("Running a quick command...", [sys.executable, "-c", "print('Done')"])

    out.step_header("Step 5: error_handling_execute - Fail")
    out.error_handling_execute("Running a quick command...", [sys.executable, "-c", "print('Done')"])
    out.error_handling_execute("Running a quick command...", [sys.executable, "-c", "import sys ; print('I FAILED') ; sys.exit(1)"])
    out.step_footer()

    out.section_footer()


if __name__ == "__main__":
    try:
        _main()
    except SystemExit:
        pass
    except BaseException as e:
        tb = traceback.format_exc()
        try:
            out = ScriptOutput()
            out.error(f"{type(e).__name__}: {e}")
            print(tb, file=sys.stderr, flush=True)
        except BaseException:
            print(f"Error: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
            print(tb, file=sys.stderr, flush=True)
        sys.exit(1)
