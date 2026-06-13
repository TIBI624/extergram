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
from typing import List, Optional, Callable, Awaitable, Dict, Any
from .ui import ButtonsDesign, ReplyKeyboard
from .api_types import Update, Message, CallbackQuery, BotCommand, ChatPermissions
from .ext.base import BaseHandler, BaseMiddleware
from . import errors
from .fsm import MemoryFSMStorage, FSMContext, FSMStorage


class Bot:
    def __init__(self, token: str, default_parse_mode: str = None, fsm_storage: FSMStorage = None):
        if not token or not token.strip():
            raise errors.EmptyTokenError("Bot token cannot be empty")
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{self.token}/"
        self.handlers = []
        self._middlewares = []
        self._offset = None
        self._client = httpx.AsyncClient()
        # По умолчанию форматирование отключено (None)
        self.default_parse_mode = default_parse_mode
        # Anti-flood
        self._request_timestamps = deque()
        self._min_delay = 0.1
        self._max_delay = 0.5
        self.fsm_storage = fsm_storage if fsm_storage is not None else MemoryFSMStorage()

    @staticmethod
    def _resolve_parse_mode(parse_mode, default_parse_mode):
        # Если явно передан parse_mode (даже пустая строка), используем его (пустая = без форматирования)
        if parse_mode is not None:
            return parse_mode if parse_mode != '' else None
        # Если нет явного, используем default_parse_mode (может быть None)
        return default_parse_mode

    async def _apply_anti_flood(self):
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

    async def _make_request(self, method: str, params: dict = None, files: dict = None, retries: int = 5):
        for attempt in range(retries):
            await self._apply_anti_flood()
            try:
                response = await self._client.post(
                    self.api_url + method,
                    json=params,
                    files=files,
                    timeout=40
                )
            except httpx.RequestError as e:
                raise errors.NetworkError(f"Network error: {e}", -1)
            if response.status_code == 200:
                data = response.json()
                if not data.get('ok'):
                    raise errors.APIError(
                        data.get('description', 'Unknown error'),
                        data.get('error_code', -1),
                        data.get('parameters')
                    )
                return data.get('result')
            try:
                error_data = response.json()
                description = error_data.get('description', 'Unknown API error')
                error_code = error_data.get('error_code', response.status_code)
                parameters = error_data.get('parameters')
            except json.JSONDecodeError:
                description = "Failed to parse error response"
                error_code = response.status_code
                parameters = None
            if response.status_code == 429:
                retry_after = (parameters or {}).get('retry_after', 5)
                if attempt < retries - 1:
                    await asyncio.sleep(retry_after)
                    continue
                raise errors.FloodControlError(description, error_code, retry_after)
            if "user has insufficient rights" in description.lower() or "not enough rights" in description.lower():
                raise errors.TelegramAdminError(description, error_code, parameters)
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
            raise error_class(description, error_code, parameters)
        raise errors.APIError("Request failed after retries", -1)

    def add_middleware(self, middleware: BaseMiddleware):
        """Добавляет middleware для обработки всех апдейтов."""
        if not isinstance(middleware, BaseMiddleware):
            raise TypeError("Middleware must be an instance of BaseMiddleware")
        self._middlewares.append(middleware)

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

        # Создаём контекст (будет передан в middleware и хендлеры)
        context = ContextTypes(self, update)

        # Определяем цепочку вызова
        async def call_handler():
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
                    args = (context,)
                try:
                    if inspect.iscoroutinefunction(callback):
                        await callback(*args)
                    else:
                        loop = asyncio.get_running_loop()
                        await loop.run_in_executor(None, callback, *args)
                except Exception as e:
                    print(f"Error in handler {callback.__name__}: {e}")
                break  # после первого подходящего хендлера останавливаемся

        # Применяем middleware в обратном порядке (последний добавленный — первый)
        async def run_middlewares(idx=0):
            if idx < len(self._middlewares):
                await self._middlewares[idx].process(context, lambda: run_middlewares(idx+1))
            else:
                await call_handler()

        await run_middlewares()

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
            except errors.FloodControlError as e:
                retry_after = getattr(e, 'retry_after', 5)
                print(f"[!] Flood control. Waiting {retry_after}s...")
                await asyncio.sleep(retry_after)
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

    async def run_polling(self, timeout: int = 30):
        """Алиас для polling (для совместимости)."""
        await self.polling(timeout)

    # ---- Webhook methods ----
    async def set_webhook(self, url: str, certificate=None, max_connections=None,
                          allowed_updates=None, drop_pending_updates=None,
                          secret_token=None):
        params = {'url': url}
        if certificate:
            params['certificate'] = certificate
        if max_connections:
            params['max_connections'] = max_connections
        if allowed_updates:
            params['allowed_updates'] = allowed_updates
        if drop_pending_updates is not None:
            params['drop_pending_updates'] = drop_pending_updates
        if secret_token:
            params['secret_token'] = secret_token
        return await self._make_request('setWebhook', params)

    async def delete_webhook(self, drop_pending_updates=None):
        params = {}
        if drop_pending_updates is not None:
            params['drop_pending_updates'] = drop_pending_updates
        return await self._make_request('deleteWebhook', params)

    async def get_webhook_info(self):
        return await self._make_request('getWebhookInfo')

    async def process_webhook(self, update_dict: dict):
        """Обрабатывает апдейт, полученный через вебхук. Вызывается из вашего веб-фреймворка."""
        update = Update(update_dict)
        await self._process_update(update)

    # ---- API Methods ----
    async def get_updates(self, offset: int = None, timeout: int = 30):
        params = {'timeout': timeout}
        if offset is not None:
            params['offset'] = offset
        return await self._make_request('getUpdates', params)

    def _prepare_reply_markup(self, reply_markup):
        if isinstance(reply_markup, (ButtonsDesign, ReplyKeyboard)):
            return reply_markup.to_dict()
        return reply_markup

    async def send_message(self, chat_id: int, text: str, parse_mode: str = None,
                           disable_web_page_preview: bool = None, disable_notification: bool = None,
                           reply_to_message_id: int = None, reply_markup=None,
                           message_thread_id: int = None, business_connection_id: str = None):
        if not chat_id:
            raise errors.BadRequestError("chat_id is required", 400)
        params = {'chat_id': chat_id, 'text': text}
        pm = self._resolve_parse_mode(parse_mode, self.default_parse_mode)
        if pm is not None:
            params['parse_mode'] = pm
        if disable_web_page_preview is not None:
            params['disable_web_page_preview'] = disable_web_page_preview
        if disable_notification is not None:
            params['disable_notification'] = disable_notification
        if reply_to_message_id is not None:
            params['reply_to_message_id'] = reply_to_message_id
        if message_thread_id is not None:
            params['message_thread_id'] = message_thread_id
        if business_connection_id is not None:
            params['business_connection_id'] = business_connection_id
        if reply_markup:
            params['reply_markup'] = self._prepare_reply_markup(reply_markup)
        return await self._make_request('sendMessage', params)

    async def edit_message_text(self, chat_id: int, message_id: int, text: str,
                                parse_mode: str = None, reply_markup=None):
        params = {'chat_id': chat_id, 'message_id': message_id, 'text': text}
        pm = self._resolve_parse_mode(parse_mode, self.default_parse_mode)
        if pm is not None:
            params['parse_mode'] = pm
        if reply_markup:
            params['reply_markup'] = self._prepare_reply_markup(reply_markup)
        return await self._make_request('editMessageText', params)

    async def edit_message_caption(self, chat_id: int, message_id: int, caption: str,
                                   parse_mode: str = None, reply_markup=None,
                                   show_caption_above_media: bool = None):
        params = {'chat_id': chat_id, 'message_id': message_id}
        if caption is not None:
            params['caption'] = caption
        pm = self._resolve_parse_mode(parse_mode, self.default_parse_mode)
        if pm is not None:
            params['parse_mode'] = pm
        if show_caption_above_media is not None:
            params['show_caption_above_media'] = show_caption_above_media
        if reply_markup:
            params['reply_markup'] = self._prepare_reply_markup(reply_markup)
        return await self._make_request('editMessageCaption', params)

    async def edit_message_media(self, chat_id: int, message_id: int, media: dict,
                                 reply_markup=None, business_connection_id: str = None):
        params = {'chat_id': chat_id, 'message_id': message_id, 'media': json.dumps(media)}
        if business_connection_id:
            params['business_connection_id'] = business_connection_id
        if reply_markup:
            params['reply_markup'] = self._prepare_reply_markup(reply_markup)
        return await self._make_request('editMessageMedia', params)

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

    async def delete_messages(self, chat_id: int, message_ids: list):
        params = {'chat_id': chat_id, 'message_ids': message_ids}
        return await self._make_request('deleteMessages', params)

    async def forward_message(self, chat_id: int, from_chat_id: int, message_id: int,
                              disable_notification: bool = None, message_thread_id: int = None):
        params = {'chat_id': chat_id, 'from_chat_id': from_chat_id, 'message_id': message_id}
        if disable_notification is not None:
            params['disable_notification'] = disable_notification
        if message_thread_id is not None:
            params['message_thread_id'] = message_thread_id
        return await self._make_request('forwardMessage', params)

    async def copy_message(self, chat_id: int, from_chat_id: int, message_id: int,
                           caption: str = None, parse_mode: str = None,
                           disable_notification: bool = None, message_thread_id: int = None,
                           reply_markup=None):
        params = {'chat_id': chat_id, 'from_chat_id': from_chat_id, 'message_id': message_id}
        if caption is not None:
            params['caption'] = caption
        pm = self._resolve_parse_mode(parse_mode, self.default_parse_mode)
        if pm is not None:
            params['parse_mode'] = pm
        if disable_notification is not None:
            params['disable_notification'] = disable_notification
        if message_thread_id is not None:
            params['message_thread_id'] = message_thread_id
        if reply_markup:
            params['reply_markup'] = self._prepare_reply_markup(reply_markup)
        return await self._make_request('copyMessage', params)

    async def _send_media(self, method: str, chat_id: int, media_path: str,
                          caption: str = None, parse_mode: str = None,
                          reply_markup=None, **extra_params):
        params = {'chat_id': chat_id, **extra_params}
        files = None
        if caption is not None:
            params['caption'] = caption
        pm = self._resolve_parse_mode(parse_mode, self.default_parse_mode)
        if pm is not None:
            params['parse_mode'] = pm
        if reply_markup:
            params['reply_markup'] = self._prepare_reply_markup(reply_markup)
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
            files = {method[4:].lower(): (path.name, file_bytes, mime_type)}
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
    async def send_animation(self, chat_id: int, animation: str, caption: str = None,
                             parse_mode: str = None, reply_markup=None):
        return await self._send_media('sendAnimation', chat_id, animation, caption,
                                      parse_mode, reply_markup)
    async def send_voice(self, chat_id: int, voice: str, caption: str = None,
                         parse_mode: str = None, reply_markup=None):
        return await self._send_media('sendVoice', chat_id, voice, caption,
                                      parse_mode, reply_markup)
    async def send_video_note(self, chat_id: int, video_note: str, reply_markup=None):
        return await self._send_media('sendVideoNote', chat_id, video_note,
                                      reply_markup=reply_markup)
    async def send_sticker(self, chat_id: int, sticker: str, reply_markup=None,
                           disable_notification: bool = None, message_thread_id: int = None):
        params = {}
        if disable_notification is not None:
            params['disable_notification'] = disable_notification
        if message_thread_id is not None:
            params['message_thread_id'] = message_thread_id
        return await self._send_media('sendSticker', chat_id, sticker,
                                      reply_markup=reply_markup, **params)

    async def send_media_group(self, chat_id: int, media: list,
                               disable_notification: bool = None, message_thread_id: int = None):
        params = {'chat_id': chat_id, 'media': json.dumps(media)}
        if disable_notification is not None:
            params['disable_notification'] = disable_notification
        if message_thread_id is not None:
            params['message_thread_id'] = message_thread_id
        return await self._make_request('sendMediaGroup', params)

    async def send_location(self, chat_id: int, latitude: float, longitude: float,
                            live_period: int = None, disable_notification: bool = None,
                            message_thread_id: int = None, reply_markup=None):
        params = {'chat_id': chat_id, 'latitude': latitude, 'longitude': longitude}
        if live_period is not None:
            params['live_period'] = live_period
        if disable_notification is not None:
            params['disable_notification'] = disable_notification
        if message_thread_id is not None:
            params['message_thread_id'] = message_thread_id
        if reply_markup:
            params['reply_markup'] = self._prepare_reply_markup(reply_markup)
        return await self._make_request('sendLocation', params)

    async def send_venue(self, chat_id: int, latitude: float, longitude: float,
                         title: str, address: str, foursquare_id: str = None,
                         disable_notification: bool = None, message_thread_id: int = None,
                         reply_markup=None):
        params = {'chat_id': chat_id, 'latitude': latitude, 'longitude': longitude,
                  'title': title, 'address': address}
        if foursquare_id:
            params['foursquare_id'] = foursquare_id
        if disable_notification is not None:
            params['disable_notification'] = disable_notification
        if message_thread_id is not None:
            params['message_thread_id'] = message_thread_id
        if reply_markup:
            params['reply_markup'] = self._prepare_reply_markup(reply_markup)
        return await self._make_request('sendVenue', params)

    async def send_contact(self, chat_id: int, phone_number: str, first_name: str,
                           last_name: str = None, disable_notification: bool = None,
                           message_thread_id: int = None, reply_markup=None):
        params = {'chat_id': chat_id, 'phone_number': phone_number, 'first_name': first_name}
        if last_name is not None:
            params['last_name'] = last_name
        if disable_notification is not None:
            params['disable_notification'] = disable_notification
        if message_thread_id is not None:
            params['message_thread_id'] = message_thread_id
        if reply_markup:
            params['reply_markup'] = self._prepare_reply_markup(reply_markup)
        return await self._make_request('sendContact', params)

    async def send_poll(self, chat_id: int, question: str, options: list,
                        is_anonymous: bool = True, type: str = 'regular',
                        allows_multiple_answers: bool = False, correct_option_id: int = None,
                        explanation: str = None, open_period: int = None,
                        close_date: int = None, is_closed: bool = False,
                        disable_notification: bool = None, message_thread_id: int = None,
                        reply_markup=None):
        params = {'chat_id': chat_id, 'question': question,
                  'options': [{'text': opt} for opt in options],
                  'is_anonymous': is_anonymous, 'type': type,
                  'allows_multiple_answers': allows_multiple_answers, 'is_closed': is_closed}
        if correct_option_id is not None:
            params['correct_option_id'] = correct_option_id
        if explanation is not None:
            params['explanation'] = explanation
        if open_period is not None:
            params['open_period'] = open_period
        if close_date is not None:
            params['close_date'] = close_date
        if disable_notification is not None:
            params['disable_notification'] = disable_notification
        if message_thread_id is not None:
            params['message_thread_id'] = message_thread_id
        if reply_markup:
            params['reply_markup'] = self._prepare_reply_markup(reply_markup)
        return await self._make_request('sendPoll', params)

    async def send_dice(self, chat_id: int, emoji: str = '🎲',
                        disable_notification: bool = None, message_thread_id: int = None,
                        reply_markup=None):
        params = {'chat_id': chat_id, 'emoji': emoji}
        if disable_notification is not None:
            params['disable_notification'] = disable_notification
        if message_thread_id is not None:
            params['message_thread_id'] = message_thread_id
        if reply_markup:
            params['reply_markup'] = self._prepare_reply_markup(reply_markup)
        return await self._make_request('sendDice', params)

    async def stop_poll(self, chat_id: int, message_id: int, reply_markup=None):
        params = {'chat_id': chat_id, 'message_id': message_id}
        if reply_markup:
            params['reply_markup'] = self._prepare_reply_markup(reply_markup)
        return await self._make_request('stopPoll', params)

    async def edit_message_reply_markup(self, chat_id: int, message_id: int, reply_markup=None):
        params = {'chat_id': chat_id, 'message_id': message_id}
        if reply_markup:
            params['reply_markup'] = self._prepare_reply_markup(reply_markup)
        return await self._make_request('editMessageReplyMarkup', params)

    async def set_my_commands(self, commands: List[BotCommand]):
        params = {'commands': [cmd.to_dict() for cmd in commands]}
        return await self._make_request('setMyCommands', params)

    # ---- Administration methods ----
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
        params = {'chat_id': chat_id, 'user_id': user_id, 'permissions': permissions.to_dict()}
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

    # ---- New API methods (1.0.0) ----
    async def get_chat(self, chat_id: int):
        return await self._make_request('getChat', {'chat_id': chat_id})

    async def get_chat_member(self, chat_id: int, user_id: int):
        return await self._make_request('getChatMember', {'chat_id': chat_id, 'user_id': user_id})

    async def get_chat_administrators(self, chat_id: int):
        return await self._make_request('getChatAdministrators', {'chat_id': chat_id})

    async def leave_chat(self, chat_id: int):
        return await self._make_request('leaveChat', {'chat_id': chat_id})

    async def set_chat_title(self, chat_id: int, title: str):
        return await self._make_request('setChatTitle', {'chat_id': chat_id, 'title': title})

    async def set_chat_description(self, chat_id: int, description: str):
        return await self._make_request('setChatDescription', {'chat_id': chat_id, 'description': description})

    async def set_chat_photo(self, chat_id: int, photo_path: str):
        # photo must be uploaded as file
        return await self._send_media('setChatPhoto', chat_id, photo_path)

    async def delete_chat_photo(self, chat_id: int):
        return await self._make_request('deleteChatPhoto', {'chat_id': chat_id})

    async def pin_chat_message(self, chat_id: int, message_id: int, disable_notification: bool = None):
        params = {'chat_id': chat_id, 'message_id': message_id}
        if disable_notification is not None:
            params['disable_notification'] = disable_notification
        return await self._make_request('pinChatMessage', params)

    async def unpin_chat_message(self, chat_id: int, message_id: int):
        return await self._make_request('unpinChatMessage', {'chat_id': chat_id, 'message_id': message_id})

    async def unpin_all_chat_messages(self, chat_id: int):
        return await self._make_request('unpinAllChatMessages', {'chat_id': chat_id})

    async def send_chat_action(self, chat_id: int, action: str, message_thread_id: int = None):
        params = {'chat_id': chat_id, 'action': action}
        if message_thread_id is not None:
            params['message_thread_id'] = message_thread_id
        return await self._make_request('sendChatAction', params)

    async def get_file(self, file_id: str):
        return await self._make_request('getFile', {'file_id': file_id})

    async def ban_chat_sender_chat(self, chat_id: int, sender_chat_id: int):
        return await self._make_request('banChatSenderChat', {'chat_id': chat_id, 'sender_chat_id': sender_chat_id})

    async def unban_chat_sender_chat(self, chat_id: int, sender_chat_id: int):
        return await self._make_request('unbanChatSenderChat', {'chat_id': chat_id, 'sender_chat_id': sender_chat_id})

    async def set_chat_permissions(self, chat_id: int, permissions: ChatPermissions):
        return await self._make_request('setChatPermissions', {'chat_id': chat_id, 'permissions': permissions.to_dict()})

    async def export_chat_invite_link(self, chat_id: int):
        return await self._make_request('exportChatInviteLink', {'chat_id': chat_id})

    async def create_chat_invite_link(self, chat_id: int, name: str = None, expire_date: int = None,
                                      member_limit: int = None, creates_join_request: bool = None):
        params = {'chat_id': chat_id}
        if name: params['name'] = name
        if expire_date: params['expire_date'] = expire_date
        if member_limit: params['member_limit'] = member_limit
        if creates_join_request is not None: params['creates_join_request'] = creates_join_request
        return await self._make_request('createChatInviteLink', params)

    async def edit_chat_invite_link(self, chat_id: int, invite_link: str, name: str = None,
                                    expire_date: int = None, member_limit: int = None,
                                    creates_join_request: bool = None):
        params = {'chat_id': chat_id, 'invite_link': invite_link}
        if name: params['name'] = name
        if expire_date: params['expire_date'] = expire_date
        if member_limit: params['member_limit'] = member_limit
        if creates_join_request is not None: params['creates_join_request'] = creates_join_request
        return await self._make_request('editChatInviteLink', params)

    async def revoke_chat_invite_link(self, chat_id: int, invite_link: str):
        return await self._make_request('revokeChatInviteLink', {'chat_id': chat_id, 'invite_link': invite_link})

    async def set_my_description(self, description: str, language_code: str = None):
        params = {'description': description}
        if language_code: params['language_code'] = language_code
        return await self._make_request('setMyDescription', params)

    async def set_my_short_description(self, short_description: str, language_code: str = None):
        params = {'short_description': short_description}
        if language_code: params['language_code'] = language_code
        return await self._make_request('setMyShortDescription', params)

    async def get_my_commands(self, scope: dict = None, language_code: str = None):
        params = {}
        if scope: params['scope'] = scope
        if language_code: params['language_code'] = language_code
        return await self._make_request('getMyCommands', params)

    async def delete_my_commands(self, scope: dict = None, language_code: str = None):
        params = {}
        if scope: params['scope'] = scope
        if language_code: params['language_code'] = language_code
        return await self._make_request('deleteMyCommands', params)

    async def log_out(self):
        return await self._make_request('logOut')

    async def close(self):
        return await self._make_request('close')

    async def answer_inline_query(self, inline_query_id: str, results: List[dict], cache_time: int = None,
                                  is_personal: bool = None, next_offset: str = None,
                                  switch_pm_text: str = None, switch_pm_parameter: str = None):
        params = {'inline_query_id': inline_query_id, 'results': json.dumps(results)}
        if cache_time: params['cache_time'] = cache_time
        if is_personal is not None: params['is_personal'] = is_personal
        if next_offset: params['next_offset'] = next_offset
        if switch_pm_text: params['switch_pm_text'] = switch_pm_text
        if switch_pm_parameter: params['switch_pm_parameter'] = switch_pm_parameter
        return await self._make_request('answerInlineQuery', params)


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
        return FSMContext(self.bot.fsm_storage, (chat_id, user_id))