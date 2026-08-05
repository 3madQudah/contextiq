"""
Miscellaneous shared helper functions (e.g. file validation, path helpers).
"""

import os

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".csv", ".md"}


def get_file_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def is_supported_file(filename: str) -> bool:
    return get_file_extension(filename) in SUPPORTED_EXTENSIONS
