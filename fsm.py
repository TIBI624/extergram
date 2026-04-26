# extergram/fsm.py

from __future__ import annotations

import json
import os
import sqlite3
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

from .api_types import Update


class FSMStorage(ABC):
    """Abstract base class for FSM storage."""

    @abstractmethod
    async def get_state(self, key: Tuple[int, int]) -> Optional[str]:
        pass

    @abstractmethod
    async def set_state(self, key: Tuple[int, int], state: Optional[str]):
        pass

    @abstractmethod
    async def get_data(self, key: Tuple[int, int]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def set_data(self, key: Tuple[int, int], data: Dict[str, Any]):
        pass

    @abstractmethod
    async def update_data(self, key: Tuple[int, int], **kwargs):
        pass

    @abstractmethod
    async def clear(self, key: Tuple[int, int]):
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


class JSONFSMStorage(FSMStorage):
    """FSM storage that saves state and data to a JSON file."""

    def __init__(self, file_path: str = "fsm_data.json"):
        self.file_path = file_path
        self._states: Dict[str, Optional[str]] = {}  # key serialized as "chat_id:user_id"
        self._data: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _key_to_str(self, key: Tuple[int, int]) -> str:
        return f"{key[0]}:{key[1]}"

    def _str_to_key(self, key_str: str) -> Tuple[int, int]:
        a, b = key_str.split(":")
        return (int(a), int(b))

    def _load(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                try:
                    dump = json.load(f)
                except json.JSONDecodeError:
                    dump = {}
            self._states = dump.get("states", {})
            self._data = dump.get("data", {})
        else:
            self._states = {}
            self._data = {}

    def _save(self):
        dump = {
            "states": self._states,
            "data": self._data,
        }
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(dump, f, ensure_ascii=False, indent=2)

    async def get_state(self, key: Tuple[int, int]) -> Optional[str]:
        return self._states.get(self._key_to_str(key))

    async def set_state(self, key: Tuple[int, int], state: Optional[str]):
        k = self._key_to_str(key)
        if state is None:
            self._states.pop(k, None)
        else:
            self._states[k] = state
        self._save()

    async def get_data(self, key: Tuple[int, int]) -> Dict[str, Any]:
        return self._data.get(self._key_to_str(key), {}).copy()

    async def set_data(self, key: Tuple[int, int], data: Dict[str, Any]):
        self._data[self._key_to_str(key)] = data.copy()
        self._save()

    async def update_data(self, key: Tuple[int, int], **kwargs):
        k = self._key_to_str(key)
        if k not in self._data:
            self._data[k] = {}
        self._data[k].update(kwargs)
        self._save()

    async def clear(self, key: Tuple[int, int]):
        k = self._key_to_str(key)
        self._states.pop(k, None)
        self._data.pop(k, None)
        self._save()


class SQLiteFSMStorage(FSMStorage):
    """FSM storage using SQLite database."""

    def __init__(self, db_path: str = "fsm_storage.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS fsm_states (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                state TEXT,
                PRIMARY KEY (chat_id, user_id)
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS fsm_data (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                data TEXT,
                PRIMARY KEY (chat_id, user_id)
            )
        """)
        self._conn.commit()

    async def get_state(self, key: Tuple[int, int]) -> Optional[str]:
        chat_id, user_id = key
        cur = self._conn.cursor()
        cur.execute("SELECT state FROM fsm_states WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        row = cur.fetchone()
        return row[0] if row else None

    async def set_state(self, key: Tuple[int, int], state: Optional[str]):
        chat_id, user_id = key
        if state is None:
            self._conn.execute("DELETE FROM fsm_states WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        else:
            self._conn.execute(
                "INSERT OR REPLACE INTO fsm_states (chat_id, user_id, state) VALUES (?,?,?)",
                (chat_id, user_id, state)
            )
        self._conn.commit()

    async def get_data(self, key: Tuple[int, int]) -> Dict[str, Any]:
        chat_id, user_id = key
        cur = self._conn.cursor()
        cur.execute("SELECT data FROM fsm_data WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        row = cur.fetchone()
        if row and row[0]:
            return json.loads(row[0])
        return {}

    async def set_data(self, key: Tuple[int, int], data: Dict[str, Any]):
        chat_id, user_id = key
        json_data = json.dumps(data, ensure_ascii=False)
        self._conn.execute(
            "INSERT OR REPLACE INTO fsm_data (chat_id, user_id, data) VALUES (?,?,?)",
            (chat_id, user_id, json_data)
        )
        self._conn.commit()

    async def update_data(self, key: Tuple[int, int], **kwargs):
        current = await self.get_data(key)
        current.update(kwargs)
        await self.set_data(key, current)

    async def clear(self, key: Tuple[int, int]):
        chat_id, user_id = key
        self._conn.execute("DELETE FROM fsm_states WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        self._conn.execute("DELETE FROM fsm_data WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        self._conn.commit()


class RedisFSMStorage(FSMStorage):
    """FSM storage using Redis."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0", **kwargs):
        try:
            import redis.asyncio as aioredis
        except ImportError:
            raise ImportError(
                "redis-py is required for RedisFSMStorage. Install it with: pip install redis"
            )
        self._redis = aioredis.from_url(redis_url, **kwargs)

    def _key_state(self, key: Tuple[int, int]) -> str:
        return f"fsm_state:{key[0]}:{key[1]}"

    def _key_data(self, key: Tuple[int, int]) -> str:
        return f"fsm_data:{key[0]}:{key[1]}"

    async def get_state(self, key: Tuple[int, int]) -> Optional[str]:
        state = await self._redis.get(self._key_state(key))
        return state.decode() if state else None

    async def set_state(self, key: Tuple[int, int], state: Optional[str]):
        if state is None:
            await self._redis.delete(self._key_state(key))
        else:
            await self._redis.set(self._key_state(key), state)

    async def get_data(self, key: Tuple[int, int]) -> Dict[str, Any]:
        data = await self._redis.get(self._key_data(key))
        if data:
            return json.loads(data.decode())
        return {}

    async def set_data(self, key: Tuple[int, int], data: Dict[str, Any]):
        await self._redis.set(self._key_data(key), json.dumps(data, ensure_ascii=False))

    async def update_data(self, key: Tuple[int, int], **kwargs):
        current = await self.get_data(key)
        current.update(kwargs)
        await self.set_data(key, current)

    async def clear(self, key: Tuple[int, int]):
        await self._redis.delete(self._key_state(key), self._key_data(key))


class FSMContext:
    """Context object for working with FSM state and data."""

    def __init__(self, storage: FSMStorage, key: Tuple[int, int]):
        self._storage = storage
        self._key = key

    async def get_state(self) -> Optional[str]:
        return await self._storage.get_state(self._key)

    async def set_state(self, state: Optional[str]):
        await self._storage.set_state(self._key, state)

    async def get_data(self) -> Dict[str, Any]:
        return await self._storage.get_data(self._key)

    async def set_data(self, data: Dict[str, Any]):
        await self._storage.set_data(self._key, data)

    async def update_data(self, **kwargs):
        await self._storage.update_data(self._key, **kwargs)

    async def clear(self):
        await self._storage.clear(self._key)


# Import here to avoid circular imports
from .ext.base import BaseHandler


class StateHandler(BaseHandler):
    """
    Handler that triggers only when the user is in a specific state.
    Wraps another handler and checks state asynchronously before delegating.
    """

    def __init__(self, state: str, handler: BaseHandler):
        self.inner_handler = handler
        super().__init__(callback=handler.callback)
        self.state = state
        self.bot = None

    def set_bot(self, bot: 'Bot'):
        self.bot = bot
        if hasattr(self.inner_handler, 'set_bot'):
            self.inner_handler.set_bot(bot)

    async def async_check_update(self, update: Update, bot: 'Bot') -> bool:
        inner_matches = False
        if hasattr(self.inner_handler, 'async_check_update') and callable(self.inner_handler.async_check_update):
            inner_matches = await self.inner_handler.async_check_update(update, bot)
        elif hasattr(self.inner_handler, 'check_update') and callable(self.inner_handler.check_update):
            inner_matches = self.inner_handler.check_update(update)

        if not inner_matches:
            return False

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
        raise NotImplementedError("StateHandler requires async_check_update")