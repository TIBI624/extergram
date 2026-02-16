# extergram/ext/message_handler.py

from .base import BaseHandler
from ..api_types import Update

class MessageHandler(BaseHandler):
    """
    Handler for incoming text messages.
    Only triggers for messages that contain text.
    For other content types (photo, video, etc.), create specific handlers.
    """
    def check_update(self, update: Update) -> bool:
        # Check if it's a message AND it has text content
        return update.message is not None and update.message.text is not None