# extergram/ext/callback_query_handler.py

from .base import BaseHandler
from ..api_types import Update

class CallbackQueryHandler(BaseHandler):
    """Handler for inline button clicks (CallbackQuery)."""
    def check_update(self, update: Update) -> bool:
        return update.callback_query is not None