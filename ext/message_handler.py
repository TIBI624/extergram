# extergram/ext/message_handler.py

import re
from .base import BaseHandler
from ..api_types import Update

class MessageHandler(BaseHandler):
    """
    Handler for incoming text messages.
    Only triggers for messages that contain text.
    Optionally filters by exact text match or regex patterns.
    """
    def __init__(self, callback, filters=None):
        """
        :param callback: coroutine or function to call
        :param filters: optional filter – can be a string (exact match),
                        a list of strings, a compiled regex, or a list of regex/string.
                        If None, any text message matches.
        """
        super().__init__(callback)
        self.filters = filters
        # нормализуем в список для удобства
        if filters is None:
            self._filter_list = None
        else:
            if isinstance(filters, (str, re.Pattern)):
                self._filter_list = [filters]
            elif isinstance(filters, list):
                self._filter_list = filters
            else:
                raise TypeError("filters must be str, re.Pattern, or list of them")

    def check_update(self, update: Update) -> bool:
        # сначала проверка на наличие текста
        if update.message is None or update.message.text is None:
            return False

        if self._filter_list is None:
            return True

        text = update.message.text
        for f in self._filter_list:
            if isinstance(f, re.Pattern):
                if f.search(text):
                    return True
            elif isinstance(f, str):
                if text == f:
                    return True
        return False