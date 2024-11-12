"""Convert bytes to KB, or MB or GB"""


def convert_bytes(size):
    """Convert bytes to KB, or MB or GB"""
    kb = 1024

    for x in ["bytes", "KB", "MB", "GB", "TB"]:
        if size < kb:
            return f"{size:3.1f} {x}"
        size /= 1024.0

    return size
