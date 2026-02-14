
# extergram/fsm.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

from .api_types import Update


class FSMStorage(ABC):
    """Abstract base class for FSM storage."""

    @abstractmethod
    async def get_state(self, key: Tuple[int, int]) -> Optional[str]:
        """Get the state for a given key (chat_id, user_id)."""
        pass

    @abstractmethod
    async def set_state(self, key: Tuple[int, int], state: Optional[str]):
        """Set the state for a given key."""
        pass

    @abstractmethod
    async def get_data(self, key: Tuple[int, int]) -> Dict[str, Any]:
        """Get the data for a given key."""
        pass

    @abstractmethod
    async def set_data(self, key: Tuple[int, int], data: Dict[str, Any]):
        """Set the data for a given key."""
        pass

    @abstractmethod
    async def update_data(self, key: Tuple[int, int], **kwargs):
        """Update the data for a given key."""
        pass

    @abstractmethod
    async def clear(self, key: Tuple[int, int]):
        """Clear state and data for a given key."""
        pass


class MemoryFSMStorage(FSMStorage):
    """In-memory storage for FSM."""

    def __init__(self):
        self._states: Dict[Tuple[int, int], Optional[str]] = {}
        self._data: Dict[Tuple[int, int], Dict[str, Any]] = {}

    async def get_state(self, key: Tuple[int, int]) -> Optional[str]:
        return self._states.get(key)

    async def set_state(self, key: Tuple[int, int], state: Optional[str]):
        if state is None:
            self._states.pop(key, None)
        else:
            self._states[key] = state

    async def get_data(self, key: Tuple[int, int]) -> Dict[str, Any]:
        return self._data.get(key, {}).copy()

    async def set_data(self, key: Tuple[int, int], data: Dict[str, Any]):
        self._data[key] = data.copy()

    async def update_data(self, key: Tuple[int, int], **kwargs):
        if key not in self._data:
            self._data[key] = {}
        self._data[key].update(kwargs)

    async def clear(self, key: Tuple[int, int]):
        self._states.pop(key, None)
        self._data.pop(key, None)


class FSMContext:
    """Context object for working with FSM state and data."""

    def __init__(self, storage: FSMStorage, key: Tuple[int, int]):
        self._storage = storage
        self._key = key

    async def get_state(self) -> Optional[str]:
        """Get current state."""
        return await self._storage.get_state(self._key)

    async def set_state(self, state: Optional[str]):
        """Set current state. Pass None to reset state."""
        await self._storage.set_state(self._key, state)

    async def get_data(self) -> Dict[str, Any]:
        """Get current data dictionary."""
        return await self._storage.get_data(self._key)

    async def set_data(self, data: Dict[str, Any]):
        """Replace current data."""
        await self._storage.set_data(self._key, data)

    async def update_data(self, **kwargs):
        """Update data with keyword arguments."""
        await self._storage.update_data(self._key, **kwargs)

    async def clear(self):
        """Clear state and data."""
        await self._storage.clear(self._key)


# Импортируем BaseHandler здесь – после определения классов, чтобы избежать циклов
from .ext.base import BaseHandler

class StateHandler(BaseHandler):
    """
    Handler that triggers only when the user is in a specific state.
    Wraps another handler and checks state asynchronously before delegating.
    """

    def __init__(self, state: str, handler: BaseHandler):
        """
        :param state: The required state (string).
        :param handler: Another handler instance (e.g., MessageHandler, CommandHandler, etc.)
        """
        # Сохраняем внутренний обработчик и используем его callback как свой собственный
        self.inner_handler = handler
        super().__init__(callback=handler.callback)
        self.state = state
        self.bot = None

    def set_bot(self, bot: 'Bot'):
        """Called by bot when handler is added."""
        self.bot = bot
        if hasattr(self.inner_handler, 'set_bot'):
            self.inner_handler.set_bot(bot)

    async def async_check_update(self, update: Update, bot: 'Bot') -> bool:
        """Async check: matches inner handler and user is in the required state."""
        # Проверяем, подходит ли внутренний обработчик
        inner_matches = False
        if hasattr(self.inner_handler, 'async_check_update') and callable(self.inner_handler.async_check_update):
            inner_matches = await self.inner_handler.async_check_update(update, bot)
        else:
            inner_matches = self.inner_handler.check_update(update)

        if not inner_matches:
            return False

        # Определяем ключ FSM для этого пользователя/чата
        if update.message:
            chat_id = update.message.chat.id
            user_id = update.message.from_user.id if update.message.from_user else None
        elif update.callback_query:
            chat_id = update.callback_query.message.chat.id if update.callback_query.message else None
            user_id = update.callback_query.from_user.id if update.callback_query.from_user else None
        else:
            return False

        if chat_id is None or user_id is None:
            return False

        key = (chat_id, user_id)
        current_state = await bot.fsm_storage.get_state(key)
        return current_state == self.state

    def check_update(self, update: Update) -> bool:
        """Fallback sync check – не используется, но требуется для абстрактного метода."""
        raise NotImplementedError("StateHandler requires async_check_update")