# extergram/ext/base.py

from ..api_types import Update

class BaseHandler:
    """Base class for all handlers."""
    def __init__(self, callback):
        self.callback = callback

    def set_bot(self, bot):
        """
        Optional method called when the handler is added to a bot.
        Can be used to store a reference to the bot (e.g., for FSM).
        """
        pass

    def check_update(self, update: Update) -> bool:
        """Checks if the update is suitable for this handler."""
        raise NotImplementedError