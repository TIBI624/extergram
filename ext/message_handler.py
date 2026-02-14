# extergram/ext/message_handler.py

from .base import BaseHandler
from ..api_types import Update

class MessageHandler(BaseHandler):
    """Handler for incoming text messages."""
    def check_update(self, update: Update) -> bool:
        # This will now trigger for any message, even commands.
        # For an "echo" bot, it's better to register it last.
        return update.message is not None