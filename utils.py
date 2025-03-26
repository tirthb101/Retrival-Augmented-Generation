import os
import sys


def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def clean_text(text):
    """
    Remove extra newlines from the text.
    """
    cleaned_text = '\n'.join(
        [line for line in text.splitlines() if line.strip()])
    return cleaned_text
