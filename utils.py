# extergram/utils.py

import re

def escape_markdown_v2(text: str) -> str:
    """
    Escapes special characters for MarkdownV2.
    This should be used when you are inserting user-generated text
    into a MarkdownV2 formatted message.
    """
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

class Markdown:
    """
    A helper class for building Markdown formatted text.
    This version provides automatic escaping for safety.
    """
    def __init__(self, text=""):
        self._parts = [escape_markdown_v2(str(text))]

    def text(self, text: str) -> 'Markdown':
        """Appends plain text, automatically escaping special characters."""
        self._parts.append(escape_markdown_v2(str(text)))
        return self

    def bold(self, text: str) -> 'Markdown':
        """Appends bold text, automatically escaping special characters in the content."""
        self._parts.append(f"*{escape_markdown_v2(str(text))}*")
        return self

    def italic(self, text: str) -> 'Markdown':
        """Appends italic text, automatically escaping special characters in the content."""
        self._parts.append(f"_{escape_markdown_v2(str(text))}_")
        return self
    
    def __str__(self):
        return ''.join(self._parts)