"""Unused module"""

import sys


def print_progress_bar(current, total, bar_length=50):
    progress = current / total
    percent = progress * 100
    blocks = int(round(bar_length * progress))
    bar = "█" * blocks + "-" * (bar_length - blocks)

    # Use sys.stdout.write to overwrite the same line
    sys.stdout.write(f"\r|{bar}| {percent:.2f}% Complete")
    sys.stdout.flush()  # Force the system to write immediately
