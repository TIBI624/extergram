# extergram/ext/base.py

from ..api_types import Update
from typing import Callable, Awaitable

class BaseHandler:
    """Base class for all handlers."""
    def __init__(self, callback):
        self.callback = callback

    def set_bot(self, bot):
        """Called when handler is added to a bot."""
        pass

    def check_update(self, update: Update) -> bool:
        """Checks if the update is suitable for this handler."""
        raise NotImplementedError


class BaseMiddleware:
    """Base class for middleware."""
    async def process(self, context, call_next: Callable[[], Awaitable[None]]):
        """
        Process the update. Call await call_next() to continue the chain.
        """
        await call_next()