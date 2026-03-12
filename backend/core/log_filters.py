"""Log filters for PII masking in production.

Applies to the root logger so all libraries benefit from the masking.
Controlled by LOG_MASK_PII environment variable (default: true).

Set LOG_MASK_PII=false in development to see unmasked paths and emails.
"""

import logging
import os
import re

_MASK_PII = os.getenv("LOG_MASK_PII", "true").lower() == "true"

# Match standard email addresses
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Match file system paths with at least 3 components (avoids masking short paths like /api/v1)
_PATH_RE = re.compile(r"(/[a-zA-Z0-9._-]+){3,}")


class PIIMaskingFilter(logging.Filter):
    """Mask emails and long file paths in log messages.

    Applied to the root logger so it covers all modules including
    third-party libraries that may log user-supplied data.

    Masking is skipped when LOG_MASK_PII=false (development mode).
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if _MASK_PII and isinstance(record.msg, str):
            record.msg = _EMAIL_RE.sub("[EMAIL]", record.msg)
            record.msg = _PATH_RE.sub(lambda m: _truncate_path(m.group()), record.msg)
        return True


def _truncate_path(path: str) -> str:
    """Keep first and last component of long file system paths.

    Args:
        path: Absolute file system path with 3+ components.

    Returns:
        Truncated path showing only first and last components.

    Examples:
        >>> _truncate_path("/data/VarunaPoC/Slides/3DHistech/sample.mrxs")
        "/data/.../sample.mrxs"
    """
    parts = path.strip("/").split("/")
    if len(parts) <= 2:
        return path
    return f"/{parts[0]}/.../{parts[-1]}"
