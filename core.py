# extergram/core.py

import httpx
import json
import asyncio
import inspect
import os
import mimetypes
from time import time
from collections import deque
from pathlib import Path
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
        # Anti-flood system
        self._request_timestamps = deque()
        self._min_delay = 0.1
        self._max_delay = 0.5
        # FSM storage
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
        
        # Properly handle file objects to ensure they are closed
        files_to_close = []
        if files:
            for key, file_obj in files.items():
                if hasattr(file_obj, 'close') and not file_obj.closed:
                    files_to_close.append(file_obj)
        
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
                    400: errors.BadRequestError,
                    401: errors.UnauthorizedError,
                    403: errors.ForbiddenError,
                    404: errors.NotFoundError,
                    409: errors.ConflictError,
                    413: errors.EntityTooLargeError,
                    500: errors.InternalServerError,
                    502: errors.BadGatewayError
                }
                error_class = error_map.get(response.status_code, errors.APIError)
                raise error_class(description, error_code)

            data = response.json()
            if not data.get('ok'):
                raise errors.APIError(data.get('description', 'Unknown error'), data.get('error_code', -1))
            return data.get('result')
        except httpx.RequestError as e:
            raise errors.NetworkError(f"Network error: {e}", -1)
        except json.JSONDecodeError:
            raise errors.APIError("Failed to decode JSON response", -1)
        finally:
            for f in files_to_close:
                try:
                    f.close()
                except Exception:
                    pass

    def add_handler(self, handler: BaseHandler):
        if not isinstance(handler, BaseHandler):
            raise TypeError("handler must be an instance of BaseHandler")
        if hasattr(handler, 'set_bot'):
            handler.set_bot(self)
        self.handlers.append(handler)

    async def _process_update(self, update: Update):
        event = update.message or update.callback_query or update.edited_message
        if not event:
            return

        for handler in self.handlers:
            matches = False
            if hasattr(handler, 'async_check_update') and callable(handler.async_check_update):
                matches = await handler.async_check_update(update, self)
            elif hasattr(handler, 'check_update') and callable(handler.check_update):
                matches = handler.check_update(update)

            if not matches:
                continue

            callback = handler.callback
            sig = inspect.signature(callback)
            params_count = len(sig.parameters)

            if params_count not in (1, 2):
                raise errors.ExtergramError(
                    f"Handler callback must accept 1 (context) or 2 (bot, event) parameters, "
                    f"but {callback.__name__} accepts {params_count}"
                )

            if params_count == 2:
                args = (self, event)
            else:
                context = ContextTypes(self, update)
                args = (context,)

            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(*args)
                else:
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, callback, *args)
                break
            except Exception as e:
                print(f"Error in handler {callback.__name__}: {e}")

    async def _polling_loop(self, timeout: int = 30):
        while True:
            try:
                updates = await self.get_updates(offset=self._offset, timeout=timeout)
                if updates:
                    for raw_update in updates:
                        self._offset = raw_update['update_id'] + 1
                        update_obj = Update(raw_update)
                        asyncio.create_task(self._process_update(update_obj))
            except errors.NetworkError as e:
                print(f"[!] Network Connection Error: {e}. Retrying in 5s...")
                await asyncio.sleep(5)
            except (errors.UnauthorizedError, errors.NotFoundError) as e:
                print(f"[CRITICAL] Invalid Token or URL: {e}. Retrying in 10s...")
                await asyncio.sleep(10)
            except errors.ConflictError:
                print("[!] Conflict: Another bot instance is running. Waiting 10s...")
                await asyncio.sleep(10)
            except errors.BadGatewayError:
                print("[!] Telegram servers are down (502). Waiting 5s...")
                await asyncio.sleep(5)
            except errors.APIError as e:
                print(f"[!] API Error: {e}. Retrying in 5s...")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"[!!!] Unexpected System Error: {e}")
                await asyncio.sleep(10)

    async def polling(self, timeout: int = 30):
        print("Bot started polling...")
        try:
            await self._polling_loop(timeout)
        except (KeyboardInterrupt, asyncio.CancelledError):
            print("Bot stopped.")
        finally:
            await self._client.aclose()

    # --- API Methods ---
    async def get_updates(self, offset: int = None, timeout: int = 30):
        params = {'timeout': timeout}
        if offset is not None:
            params['offset'] = offset
        return await self._make_request('getUpdates', params)

    async def send_message(self, chat_id: int, text: str, parse_mode: str = None,
                          disable_web_page_preview: bool = None, disable_notification: bool = None,
                          reply_to_message_id: int = None, reply_markup=None):
        params = {'chat_id': chat_id, 'text': text}
        # Parse mode: use provided or default, but only if not None
        pm = parse_mode or self.default_parse_mode
        if pm is not None:
            params['parse_mode'] = pm
        if disable_web_page_preview is not None:
            params['disable_web_page_preview'] = disable_web_page_preview
        if disable_notification is not None:
            params['disable_notification'] = disable_notification
        if reply_to_message_id is not None:
            params['reply_to_message_id'] = reply_to_message_id
        if isinstance(reply_markup, ButtonsDesign):
            params['reply_markup'] = reply_markup.to_dict()
        elif reply_markup:
            params['reply_markup'] = reply_markup
        return await self._make_request('sendMessage', params)

    async def edit_message_text(self, chat_id: int, message_id: int, text: str,
                               parse_mode: str = None, reply_markup=None):
        params = {'chat_id': chat_id, 'message_id': message_id, 'text': text}
        pm = parse_mode or self.default_parse_mode
        if pm is not None:
            params['parse_mode'] = pm
        if isinstance(reply_markup, ButtonsDesign):
            params['reply_markup'] = reply_markup.to_dict()
        elif reply_markup:
            params['reply_markup'] = reply_markup
        return await self._make_request('editMessageText', params)

    async def answer_callback_query(self, callback_query_id: str, text: str = None,
                                   show_alert: bool = False, url: str = None,
                                   cache_time: int = None):
        params = {'callback_query_id': callback_query_id}
        if text is not None:
            params['text'] = text
        params['show_alert'] = show_alert
        if url is not None:
            params['url'] = url
        if cache_time is not None:
            params['cache_time'] = cache_time
        return await self._make_request('answerCallbackQuery', params)

    async def delete_message(self, chat_id: int, message_id: int):
        params = {'chat_id': chat_id, 'message_id': message_id}
        return await self._make_request('deleteMessage', params)

    async def _send_media(self, method: str, chat_id: int, media_path: str,
                         caption: str = None, parse_mode: str = None,
                         reply_markup=None, **extra_params):
        params = {'chat_id': chat_id, **extra_params}
        files = None

        if caption is not None:
            params['caption'] = caption
        pm = parse_mode or self.default_parse_mode
        if pm is not None:
            params['parse_mode'] = pm
        if isinstance(reply_markup, ButtonsDesign):
            params['reply_markup'] = reply_markup.to_dict()
        elif reply_markup:
            params['reply_markup'] = reply_markup

        if media_path.startswith(('http://', 'https://')):
            params[method[4:].lower()] = media_path
        else:
            path = Path(media_path)
            if not path.exists():
                raise FileNotFoundError(f"Media file not found: {media_path}")
            mime_type, _ = mimetypes.guess_type(str(path))
            if not mime_type:
                mime_type = 'application/octet-stream'
            with open(path, 'rb') as f:
                file_bytes = f.read()
            files = {
                method[4:].lower(): (path.name, file_bytes, mime_type)
            }
        return await self._make_request(method, params, files)

    async def send_photo(self, chat_id: int, photo: str, caption: str = None,
                        parse_mode: str = None, reply_markup=None):
        return await self._send_media('sendPhoto', chat_id, photo, caption,
                                     parse_mode, reply_markup)

    async def send_document(self, chat_id: int, document: str, caption: str = None,
                           parse_mode: str = None, reply_markup=None):
        return await self._send_media('sendDocument', chat_id, document, caption,
                                     parse_mode, reply_markup)

    async def send_video(self, chat_id: int, video: str, caption: str = None,
                        parse_mode: str = None, reply_markup=None):
        return await self._send_media('sendVideo', chat_id, video, caption,
                                     parse_mode, reply_markup)

    async def send_voice(self, chat_id: int, voice: str, caption: str = None,
                        parse_mode: str = None, reply_markup=None):
        return await self._send_media('sendVoice', chat_id, voice, caption,
                                     parse_mode, reply_markup)

    async def send_video_note(self, chat_id: int, video_note: str, reply_markup=None):
        return await self._send_media('sendVideoNote', chat_id, video_note,
                                     reply_markup=reply_markup)

    async def send_animation(self, chat_id: int, animation: str, caption: str = None,
                            parse_mode: str = None, reply_markup=None):
        return await self._send_media('sendAnimation', chat_id, animation, caption,
                                     parse_mode, reply_markup)

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
    async def ban_chat_member(self, chat_id: int, user_id: int, until_date: int = None,
                             revoke_messages: bool = None):
        params = {'chat_id': chat_id, 'user_id': user_id}
        if until_date is not None:
            params['until_date'] = until_date
        if revoke_messages is not None:
            params['revoke_messages'] = revoke_messages
        return await self._make_request('banChatMember', params)

    async def unban_chat_member(self, chat_id: int, user_id: int, only_if_banned: bool = None):
        params = {'chat_id': chat_id, 'user_id': user_id}
        if only_if_banned is not None:
            params['only_if_banned'] = only_if_banned
        return await self._make_request('unbanChatMember', params)

    async def restrict_chat_member(self, chat_id: int, user_id: int, permissions: ChatPermissions,
                                  until_date: int = None):
        params = {
            'chat_id': chat_id,
            'user_id': user_id,
            'permissions': permissions.to_dict()
        }
        if until_date is not None:
            params['until_date'] = until_date
        return await self._make_request('restrictChatMember', params)

    async def promote_chat_member(self, chat_id: int, user_id: int, **permissions):
        params = {'chat_id': chat_id, 'user_id': user_id}
        params.update({k: v for k, v in permissions.items() if v is not None})
        return await self._make_request('promoteChatMember', params)

    async def approve_chat_join_request(self, chat_id: int, user_id: int):
        params = {'chat_id': chat_id, 'user_id': user_id}
        return await self._make_request('approveChatJoinRequest', params)

    async def decline_chat_join_request(self, chat_id: int, user_id: int):
        params = {'chat_id': chat_id, 'user_id': user_id}
        return await self._make_request('declineChatJoinRequest', params)


class ContextTypes:
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
    def effective_user(self):
        if self.message and self.message.from_user:
            return self.message.from_user
        if self.callback_query and self.callback_query.from_user:
            return self.callback_query.from_user
        return None

    @property
    def effective_chat(self):
        if self.message and self.message.chat:
            return self.message.chat
        if self.callback_query and self.callback_query.message:
            return self.callback_query.message.chat
        return None

    @property
    def state(self) -> FSMContext:
        if self.message:
            chat_id = self.message.chat.id
            user_id = self.message.from_user.id if self.message.from_user else None
        elif self.callback_query:
            chat_id = self.callback_query.message.chat.id if self.callback_query.message else None
            user_id = self.callback_query.from_user.id if self.callback_query.from_user else None
        else:
            chat_id = user_id = None

        if chat_id is None or user_id is None:
            raise RuntimeError(
                "Cannot determine user/chat for FSM context. "
                "This may happen with channel posts or other non-user updates."
            )
        key = (chat_id, user_id)
        return FSMContext(self.bot.fsm_storage, key)