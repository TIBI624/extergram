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
        # The initial text is now also safely escaped to prevent errors.
        self.text = escape_markdown_v2(str(text))

    def bold(self, text: str) -> 'Markdown':
        """Appends bold text, automatically escaping special characters in the content."""
        self.text += f"*{escape_markdown_v2(str(text))}*"
        return self

    def italic(self, text: str) -> 'Markdown':
        """Appends italic text, automatically escaping special characters in the content."""
        self.text += f"_{escape_markdown_v2(str(text))}_"
        return self
    
    def __str__(self):
        return self.text