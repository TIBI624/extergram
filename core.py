# extergram/core.py

import httpx
import json
import asyncio
import inspect
import os
from time import time
from collections import deque
from .ui import ButtonsDesign
from .api_types import Update, Message, CallbackQuery, BotCommand, ChatPermissions
from .ext.base import BaseHandler
from . import errors
from .fsm import MemoryFSMStorage, FSMContext

class Bot:
    """
    The main class for creating a Telegram bot and interacting with the API.
    """
    def __init__(self, token: str, default_parse_mode: str = None):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{self.token}/"
        self.handlers = []
        self._offset = None
        self._client = httpx.AsyncClient()
        self.default_parse_mode = default_parse_mode
        # --- Anti-flood system ---
        self._request_timestamps = deque()
        self._min_delay = 0.1
        self._max_delay = 0.5
        # --- FSM storage ---
        self.fsm_storage = MemoryFSMStorage()

    async def _apply_anti_flood(self):
        """Dynamic delay to avoid hitting API limits."""
        current_time = time()
        while self._request_timestamps and self._request_timestamps[0] <= current_time - 2:
            self._request_timestamps.popleft()

        recent_requests = len(self._request_timestamps)
        delay = 0
        if recent_requests > 25:
            delay = self._max_delay
        elif recent_requests > 15:
            delay = (self._min_delay + self._max_delay) / 2
        elif recent_requests > 5:
            delay = self._min_delay

        if delay > 0 and self._request_timestamps:
            time_since_last_call = current_time - self._request_timestamps[-1]
            if time_since_last_call < delay:
                await asyncio.sleep(delay - time_since_last_call)

        self._request_timestamps.append(time())

    async def _make_request(self, method: str, params: dict = None, files: dict = None):
        await self._apply_anti_flood()
        try:
            response = await self._client.post(self.api_url + method, json=params, files=files, timeout=40)
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    description = error_data.get('description', 'Unknown API error')
                    error_code = error_data.get('error_code', response.status_code)
                except json.JSONDecodeError:
                    description = "Failed to parse error response"
                    error_code = response.status_code

                if "user has insufficient rights" in description.lower() or "not enough rights" in description.lower():
                    raise errors.TelegramAdminError(description, error_code)

                error_map = {
                    400: errors.BadRequestError, 401: errors.UnauthorizedError,
                    403: errors.ForbiddenError, 404: errors.NotFoundError,
                    409: errors.ConflictError, 413: errors.EntityTooLargeError,
                    502: errors.BadGatewayError
                }
                error_class = error_map.get(response.status_code, errors.APIError)
                raise error_class(description, error_code)

            data = response.json()
            if not data.get('ok'):
                raise errors.APIError(data.get('description', 'Unknown error'), data.get('error_code', -1))
            return data
        except httpx.RequestError as e:
            raise errors.NetworkError(f"Network error: {e}", -1)
        except json.JSONDecodeError:
            raise errors.APIError("Failed to decode JSON response", -1)

    def add_handler(self, handler: BaseHandler):
        """Registers a new event handler."""
        if not isinstance(handler, BaseHandler):
            raise TypeError("handler must be an instance of BaseHandler")
        # Give the handler a chance to store a reference to this bot
        if hasattr(handler, 'set_bot'):
            handler.set_bot(self)
        self.handlers.append(handler)

    async def _process_update(self, update: Update):
        """Asynchronously processes a single update with backward compatibility."""
        event = update.message or update.callback_query or update.edited_message
        if not event:
            return

        tasks = []
        for handler in self.handlers:
            # Check if the update matches this handler (async or sync)
            matches = False
            if hasattr(handler, 'async_check_update') and callable(handler.async_check_update):
                matches = await handler.async_check_update(update, self)
            else:
                matches = handler.check_update(update)

            if not matches:
                continue

            callback = handler.callback
            sig = inspect.signature(callback)
            params_count = len(sig.parameters)

            if params_count == 2:
                # Old style: callback(bot, event)
                args = (self, event)
            else:
                # New style: callback(context)
                context = ContextTypes(self, update)
                args = (context,)

            if inspect.iscoroutinefunction(callback):
                tasks.append(asyncio.create_task(callback(*args)))
            else:
                loop = asyncio.get_running_loop()
                tasks.append(loop.run_in_executor(None, callback, *args))

        if tasks:
            await asyncio.gather(*tasks)

    async def _polling_loop(self, timeout: int = 30):
        """The main asynchronous polling loop with auto-restart logic."""
        while True:
            try:
                updates_data = await self.get_updates(offset=self._offset, timeout=timeout)
                updates = updates_data.get('result', [])
                if updates:
                    for raw_update in updates:
                        self._offset = raw_update['update_id'] + 1
                        update_obj = Update(raw_update)
                        asyncio.create_task(self._process_update(update_obj))

            except errors.NetworkError as e:
                print(f"[!] Network Connection Error: {e}. Retrying in 5s...")
                await asyncio.sleep(5)
                continue
            except (errors.UnauthorizedError, errors.NotFoundError) as e:
                print(f"[CRITICAL] Invalid Token or URL: {e}")
                print(">>> Please check your BOT_TOKEN. Retrying in 10s...")
                await asyncio.sleep(10)
            except errors.ConflictError:
                print("[!] Conflict: Another bot instance is running. Waiting 10s...")
                await asyncio.sleep(10)
            except errors.BadGatewayError:
                print("[!] Telegram servers are down (502 Bad Gateway). Waiting 5s...")
                await asyncio.sleep(5)
            except errors.APIError as e:
                print(f"[!] API Error: {e}. Attempting to continue in 5s...")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"[!!!] Unexpected System Error: {e}")
                await asyncio.sleep(10)

    async def polling(self, timeout: int = 30):
        """Starts the bot in long-polling mode. This is a coroutine."""
        print("Bot started polling...")
        try:
            await self._polling_loop(timeout)
        except (KeyboardInterrupt, asyncio.CancelledError):
            print("Bot stopped.")
        finally:
            await self._client.aclose()

    # --- API Methods (unchanged) ---
    async def get_updates(self, offset: int = None, timeout: int = 30):
        params = {'timeout': timeout, 'offset': offset}
        return await self._make_request('getUpdates', params)

    async def send_message(self, chat_id: int, text: str, parse_mode: str = None, reply_markup=None):
        params = {'chat_id': chat_id, 'text': text}
        params['parse_mode'] = parse_mode or self.default_parse_mode
        if isinstance(reply_markup, ButtonsDesign):
            params['reply_markup'] = reply_markup.to_dict()
        elif reply_markup:
            params['reply_markup'] = reply_markup
        return await self._make_request('sendMessage', params)

    async def edit_message_text(self, chat_id: int, message_id: int, text: str, parse_mode: str = None, reply_markup=None):
        params = {'chat_id': chat_id, 'message_id': message_id, 'text': text}
        params['parse_mode'] = parse_mode or self.default_parse_mode
        if isinstance(reply_markup, ButtonsDesign):
            params['reply_markup'] = reply_markup.to_dict()
        elif reply_markup:
            params['reply_markup'] = reply_markup
        return await self._make_request('editMessageText', params)

    async def answer_callback_query(self, callback_query_id: str, text: str = None, show_alert: bool = False):
        params = {'callback_query_id': callback_query_id}
        if text:
            params['text'] = text
        params['show_alert'] = show_alert
        return await self._make_request('answerCallbackQuery', params)

    async def delete_message(self, chat_id: int, message_id: int):
        params = {'chat_id': chat_id, 'message_id': message_id}
        return await self._make_request('deleteMessage', params)

    async def send_photo(self, chat_id: int, photo: str, caption: str = None, parse_mode: str = None, reply_markup=None):
        params = {'chat_id': chat_id}
        files = None
        if caption:
            params['caption'] = caption
        params['parse_mode'] = parse_mode or self.default_parse_mode
        if isinstance(reply_markup, ButtonsDesign):
            params['reply_markup'] = reply_markup.to_dict()
        elif reply_markup:
            params['reply_markup'] = reply_markup

        if photo.startswith('http') or not os.path.exists(photo):
            params['photo'] = photo
        else:
            files = {'photo': open(photo, 'rb')}
        return await self._make_request('sendPhoto', params, files=files)

    async def send_document(self, chat_id: int, document: str, caption: str = None, parse_mode: str = None, reply_markup=None):
        params = {'chat_id': chat_id}
        files = None
        if caption:
            params['caption'] = caption
        params['parse_mode'] = parse_mode or self.default_parse_mode
        if isinstance(reply_markup, ButtonsDesign):
            params['reply_markup'] = reply_markup.to_dict()
        elif reply_markup:
            params['reply_markup'] = reply_markup

        if document.startswith('http') or not os.path.exists(document):
            params['document'] = document
        else:
            files = {'document': open(document, 'rb')}
        return await self._make_request('sendDocument', params, files=files)

    async def send_video(self, chat_id: int, video: str, caption: str = None, parse_mode: str = None, reply_markup=None):
        params = {'chat_id': chat_id}
        files = None
        if caption:
            params['caption'] = caption
        params['parse_mode'] = parse_mode or self.default_parse_mode
        if isinstance(reply_markup, ButtonsDesign):
            params['reply_markup'] = reply_markup.to_dict()
        elif reply_markup:
            params['reply_markup'] = reply_markup

        if video.startswith('http') or not os.path.exists(video):
            params['video'] = video
        else:
            files = {'video': open(video, 'rb')}
        return await self._make_request('sendVideo', params, files=files)

    async def send_voice(self, chat_id: int, voice: str, caption: str = None, parse_mode: str = None, reply_markup=None):
        params = {'chat_id': chat_id}
        files = None
        if caption:
            params['caption'] = caption
        params['parse_mode'] = parse_mode or self.default_parse_mode
        if isinstance(reply_markup, ButtonsDesign):
            params['reply_markup'] = reply_markup.to_dict()

        if voice.startswith('http') or not os.path.exists(voice):
            params['voice'] = voice
        else:
            files = {'voice': open(voice, 'rb')}
        return await self._make_request('sendVoice', params, files=files)

    async def send_video_note(self, chat_id: int, video_note: str, reply_markup=None):
        params = {'chat_id': chat_id}
        files = None
        if isinstance(reply_markup, ButtonsDesign):
            params['reply_markup'] = reply_markup.to_dict()

        if video_note.startswith('http') or not os.path.exists(video_note):
            params['video_note'] = video_note
        else:
            files = {'video_note': open(video_note, 'rb')}
        return await self._make_request('sendVideoNote', params, files=files)

    async def send_animation(self, chat_id: int, animation: str, caption: str = None, parse_mode: str = None, reply_markup=None):
        params = {'chat_id': chat_id}
        files = None
        if caption:
            params['caption'] = caption
        params['parse_mode'] = parse_mode or self.default_parse_mode
        if isinstance(reply_markup, ButtonsDesign):
            params['reply_markup'] = reply_markup.to_dict()
        elif reply_markup:
            params['reply_markup'] = reply_markup

        if animation.startswith('http') or not os.path.exists(animation):
            params['animation'] = animation
        else:
            files = {'animation': open(animation, 'rb')}
        return await self._make_request('sendAnimation', params, files=files)

    async def edit_message_reply_markup(self, chat_id: int, message_id: int, reply_markup=None):
        params = {'chat_id': chat_id, 'message_id': message_id}
        if isinstance(reply_markup, ButtonsDesign):
            params['reply_markup'] = reply_markup.to_dict()
        elif reply_markup:
            params['reply_markup'] = reply_markup
        return await self._make_request('editMessageReplyMarkup', params)

    async def set_my_commands(self, commands: list[BotCommand]):
        params = {'commands': [cmd.to_dict() for cmd in commands]}
        return await self._make_request('setMyCommands', params)

    # --- Administration Methods ---
    async def ban_chat_member(self, chat_id: int, user_id: int, until_date: int = None, revoke_messages: bool = None):
        params = {'chat_id': chat_id, 'user_id': user_id}
        if until_date:
            params['until_date'] = until_date
        if revoke_messages is not None:
            params['revoke_messages'] = revoke_messages
        return await self._make_request('banChatMember', params)

    async def unban_chat_member(self, chat_id: int, user_id: int, only_if_banned: bool = None):
        params = {'chat_id': chat_id, 'user_id': user_id}
        if only_if_banned is not None:
            params['only_if_banned'] = only_if_banned
        return await self._make_request('unbanChatMember', params)

    async def restrict_chat_member(self, chat_id: int, user_id: int, permissions: ChatPermissions, until_date: int = None):
        params = {'chat_id': chat_id, 'user_id': user_id, 'permissions': permissions.to_dict()}
        if until_date:
            params['until_date'] = until_date
        return await self._make_request('restrictChatMember', params)

    async def promote_chat_member(self, chat_id: int, user_id: int, **permissions):
        params = {'chat_id': chat_id, 'user_id': user_id}
        params.update(permissions)
        return await self._make_request('promoteChatMember', params)

    async def approve_chat_join_request(self, chat_id: int, user_id: int):
        params = {'chat_id': chat_id, 'user_id': user_id}
        return await self._make_request('approveChatJoinRequest', params)

    async def decline_chat_join_request(self, chat_id: int, user_id: int):
        params = {'chat_id': chat_id, 'user_id': user_id}
        return await self._make_request('declineChatJoinRequest', params)


class ContextTypes:
    """A context class that provides bot and update information to handlers."""
    def __init__(self, bot: Bot, update: Update):
        self.bot = bot
        self.update = update

    @property
    def message(self) -> Message:
        return self.update.message or self.update.edited_message

    @property
    def callback_query(self) -> CallbackQuery:
        return self.update.callback_query

    @property
    def state(self) -> FSMContext:
        """
        Returns an FSMContext object for the current user/chat.
        The key is (chat_id, user_id). In private chats both are the same.
        """
        # Determine chat_id and user_id from the update
        if self.message:
            chat_id = self.message.chat.id
            user_id = self.message.from_user.id if self.message.from_user else None
        elif self.callback_query:
            chat_id = self.callback_query.message.chat.id if self.callback_query.message else None
            user_id = self.callback_query.from_user.id if self.callback_query.from_user else None
        else:
            chat_id = user_id = None

        if chat_id is None or user_id is None:
            raise RuntimeError("Cannot determine user/chat for FSM context")

        key = (chat_id, user_id)
        return FSMContext(self.bot.fsm_storage, key)