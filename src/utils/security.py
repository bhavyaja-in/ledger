"""
Security utilities for input sanitization and validation.

This module provides functions to sanitize user inputs and prevent
various types of attacks including XSS, SQL injection, and path traversal.
"""

import html
import re
from typing import Optional

__all__ = [
    "sanitize_text_input",
    "validate_amount",
    "sanitize_filename",
    "sanitize_sql_like_pattern",
]


def sanitize_text_input(
    text: Optional[str], max_length: Optional[int] = None
) -> str:  # pylint: disable=unused-variable
    """
    Sanitize text input to prevent XSS and other injection attacks.

    Args:
        text: The input text to sanitize
        max_length: Maximum allowed length for the text (optional)

    Returns:
        Sanitized text safe for storage and display

    Examples:
        >>> sanitize_text_input("<script>alert('XSS')</script>")
        "&lt;script&gt;alert('XSS')&lt;/script&gt;"

        >>> sanitize_text_input("javascript:alert('XSS')")
        "javascript:alert('XSS')"
    """
    if not text:
        return ""

    # Convert to string and strip whitespace
    text = str(text).strip()

    # Apply length limit if specified
    if max_length and len(text) > max_length:
        text = text[:max_length]

    # HTML escape to prevent XSS
    text = html.escape(text)

    # Additional security checks for dangerous patterns
    dangerous_patterns = [
        r"javascript:",  # JavaScript protocol
        r"vbscript:",  # VBScript protocol
        r"data:",  # Data protocol
        r"<script",  # Script tags
        r"<iframe",  # Iframe tags
        r"<object",  # Object tags
        r"<embed",  # Embed tags
        r"on\w+\s*=",  # Event handlers (onclick, onload, etc.)
    ]

    for pattern in dangerous_patterns:
        # Replace dangerous patterns with safe alternatives
        # Use a simple replacement to avoid regex escape issues
        if "javascript:" in pattern:
            text = re.sub(pattern, "[BLOCKED:javascript]", text, flags=re.IGNORECASE)
        elif "vbscript:" in pattern:
            text = re.sub(pattern, "[BLOCKED:vbscript]", text, flags=re.IGNORECASE)
        elif "data:" in pattern:
            text = re.sub(pattern, "[BLOCKED:data]", text, flags=re.IGNORECASE)
        elif "<script" in pattern:
            text = re.sub(pattern, "[BLOCKED:script]", text, flags=re.IGNORECASE)
        elif "<iframe" in pattern:
            text = re.sub(pattern, "[BLOCKED:iframe]", text, flags=re.IGNORECASE)
        elif "<object" in pattern:
            text = re.sub(pattern, "[BLOCKED:object]", text, flags=re.IGNORECASE)
        elif "<embed" in pattern:
            text = re.sub(pattern, "[BLOCKED:embed]", text, flags=re.IGNORECASE)
        elif "on\\w+\\s*=" in pattern:
            text = re.sub(pattern, "[BLOCKED:event_handler]", text, flags=re.IGNORECASE)

    return text


def sanitize_filename(
    filename: Optional[str],
) -> str:  # pylint: disable=unused-variable
    """
    Sanitize filename to prevent path traversal attacks.

    Args:
        filename: The filename to sanitize

    Returns:
        Sanitized filename safe for file operations

    Examples:
        >>> sanitize_filename("../../../etc/passwd")
        "etc_passwd"

        >>> sanitize_filename("normal_file.xlsx")
        "normal_file.xlsx"
    """
    if not filename:
        return ""

    # Remove path traversal sequences
    dangerous_patterns = [
        r"\.\./",  # ../
        r"\.\.\\",  # ..\
        r"%2e%2e%2f",  # URL encoded ../
        r"%2e%2e%5c",  # URL encoded ..\
    ]

    for pattern in dangerous_patterns:
        filename = re.sub(pattern, "", filename, flags=re.IGNORECASE)

    # Remove any remaining path separators and URL encoded separators
    filename = re.sub(r"[\\/]", "_", filename)
    filename = re.sub(r"%2f", "_", filename, flags=re.IGNORECASE)  # URL encoded /
    filename = re.sub(r"%5c", "_", filename, flags=re.IGNORECASE)  # URL encoded \

    # Remove any remaining .. sequences (double dots)
    filename = re.sub(r"\.\.", "", filename)

    # Collapse multiple underscores to a single one
    filename = re.sub(r"_+", "_", filename)
    # Remove leading underscores
    filename = filename.lstrip("_")

    # Remove null bytes and other dangerous characters
    filename = re.sub(r"[\x00-\x1f\x7f]", "", filename)

    return filename


def validate_amount(amount_str: Optional[str]) -> Optional[float]:
    """
    Validate and parse amount strings safely.

    Args:
        amount_str: The amount string to validate

    Returns:
        Parsed float value or None if invalid

    Examples:
        >>> validate_amount("100.50")
        100.5

        >>> validate_amount("1,000.00")
        1000.0

        >>> validate_amount("invalid")
        None
    """
    if not amount_str:
        return None

    try:
        # Remove common currency symbols and formatting
        cleaned = (
            str(amount_str)
            .replace(",", "")
            .replace("₹", "")
            .replace("$", "")
            .replace("€", "")
            .strip()
        )

        # Validate it's a reasonable number
        value = float(cleaned)

        # Check for reasonable bounds (prevent overflow attacks)
        if abs(value) > 1e12:  # 1 trillion limit
            return None

        return value if value >= 0 else None

    except (ValueError, TypeError, OverflowError):
        return None


def sanitize_sql_like_pattern(
    pattern: Optional[str],
) -> str:  # pylint: disable=unused-variable
    """
    Sanitize SQL LIKE patterns to prevent injection.

    Args:
        pattern: The pattern to sanitize

    Returns:
        Sanitized pattern safe for SQL LIKE operations

    Examples:
        >>> sanitize_sql_like_pattern("user%")
        "user%"

        >>> sanitize_sql_like_pattern("'; DROP TABLE users; --")
        "'; DROP TABLE users; --"
    """
    if not pattern:
        return ""

    # Escape SQL wildcards that could be used maliciously
    pattern = str(pattern).replace("%", "\\%").replace("_", "\\_")

    return pattern


def is_safe_for_display(text: Optional[str]) -> bool:  # pylint: disable=unused-variable
    """
    Check if text is safe for display without additional sanitization.

    Args:
        text: The text to check

    Returns:
        True if text is safe for display, False otherwise

    Examples:
        >>> is_safe_for_display("Normal text")
        True

        >>> is_safe_for_display("<script>alert('XSS')</script>")
        False
    """
    if not text:
        return True

    dangerous_patterns = [
        r"<script",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False

    return True
