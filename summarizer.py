import ollama
import sys
import threading
import time
import itertools


# ---------------------------------------------------------------------------
# Simple ANSI color helpers (no extra dependencies needed)
# ---------------------------------------------------------------------------
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"
    BLUE = "\033[34m"


def color(text, *codes):
    return f"{''.join(codes)}{text}{C.RESET}"


def print_banner():
    width = 56
    title = "AI TEXT SUMMARIZER"
    subtitle = "Tools used:Ollama + Python"
    print(color("╔" + "═" * (width - 2) + "╗", C.CYAN, C.BOLD))
    print(color("║", C.CYAN, C.BOLD) + title.center(width - 2) + color("║", C.CYAN, C.BOLD))
    print(color("║", C.CYAN, C.BOLD) + color(subtitle.center(width - 2), C.DIM) + color("║", C.CYAN, C.BOLD))
    print(color("╚" + "═" * (width - 2) + "╝", C.CYAN, C.BOLD))


def print_section(title):
    print()
    print(color(f"── {title} ", C.MAGENTA, C.BOLD) + color("─" * (50 - len(title)), C.DIM))


def print_boxed(label, content, border_color=C.GREEN):
    width = 60
    print(color("┌" + "─" * (width - 2) + "┐", border_color))
    print(color("│ ", border_color) + color(label, C.BOLD) + " " * (width - 4 - len(label)) + color(" │", border_color))
    print(color("├" + "─" * (width - 2) + "┤", border_color))
    for line in wrap_text(content, width - 4):
        pad = width - 4 - len(line)
        print(color("│ ", border_color) + line + " " * pad + color(" │", border_color))
    print(color("└" + "─" * (width - 2) + "┘", border_color))


def wrap_text(text, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        if len(current) + len(word) + 1 <= max_width:
            current = f"{current} {word}".strip()
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


class Spinner:
    """Simple terminal spinner to show while Ollama is generating."""

    def __init__(self, message="Generating summary"):
        self.message = message
        self._stop_event = threading.Event()
        self._thread = None

    def _spin(self):
        frames = itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])
        while not self._stop_event.is_set():
            frame = next(frames)
            sys.stdout.write(f"\r{color(frame, C.YELLOW, C.BOLD)} {color(self.message + '...', C.DIM)}")
            sys.stdout.flush()
            time.sleep(0.08)
        sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")
        sys.stdout.flush()

    def __enter__(self):
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop_event.set()
        if self._thread:
            self._thread.join()


# ---------------------------------------------------------------------------
# Core summarization logic
# ---------------------------------------------------------------------------
def summarize_text(long_text):
    """
    Summarize the given text using Ollama with improved prompt design
    """
    if not long_text or len(long_text.strip()) == 0:
        return "Error: No text provided."

    system_instruction = (
        "You are a summarization tool. Summarize text in a short, clear, and concise way. "
        "Keep the summary strictly under 3 bullet points or maximum 2-3 sentences. "
        "Do not include unnecessary intros or introductory text like 'Here is a summary:'."
    )

    try:
        with Spinner("Generating concise summary"):
            response = ollama.chat(
                model="llama3.1",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": long_text.strip()},
                ],
                options={
                    "temperature": 0.3,   # Lower temperature for focused output
                    "num_predict": 150,   # Limit output length
                },
            )

        summary = response["message"]["content"].strip()

        intro_phrases = ["here is a summary:", "summary:", "in summary:", "to summarize:"]
        for phrase in intro_phrases:
            if summary.lower().startswith(phrase):
                summary = summary[len(phrase):].strip()

        return summary

    except ollama.ResponseError as e:
        return f"Error: Ollama response error - {e}"
    except Exception as e:
        return f"Error: Ensure Ollama service is running. Details: {e}"


# ---------------------------------------------------------------------------
# Script logic (runs directly, no main() wrapper)
# ---------------------------------------------------------------------------
print_banner()

print_section("INPUT")
print(color("Paste your long text below.", C.DIM))
print(color("Press Enter, then Ctrl+D (Mac/Linux) or Ctrl+Z + Enter (Windows) to submit:\n", C.DIM))

lines = []
try:
    while True:
        line = input()
        lines.append(line)
except EOFError:
    pass

user_input = "\n".join(lines).strip()

if user_input:
    print_section("RESULT")
    summary = summarize_text(user_input)

    if summary.startswith("Error:"):
        print(color(f"✗ {summary}", C.RED, C.BOLD))
    else:
        print_boxed("CONCISE SUMMARY", summary, border_color=C.GREEN)

    print()
    orig_len = len(user_input)
    summ_len = len(summary)
    reduction = 100 - (summ_len / orig_len * 100) if orig_len else 0

    print(color("Stats:", C.BOLD))
    print(f"  {color('•', C.CYAN)} Original length : {orig_len} characters")
    print(f"  {color('•', C.CYAN)} Summary length  : {summ_len} characters")
    print(f"  {color('•', C.CYAN)} Reduction       : {color(f'{reduction:.1f}%', C.GREEN, C.BOLD)}")
    print()
    print(color("═" * 56, C.CYAN))
else:
    print(color("\n✗ No text provided!", C.RED, C.BOLD))