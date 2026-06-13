# Extergram — Asynchronous Telegram Bot Framework

*Disclaimer: This project is an independent open-source library and is not affiliated with, associated with, authorized by, endorsed by, or in any way officially connected with Telegram FZ-LLC or any of its subsidiaries or its affiliates.*

**Extergram** is a modern, fully asynchronous Python framework for building Telegram bots. It provides a clean API, built‑in FSM (Finite State Machine) with multiple storage backends, middleware support, webhooks, anti‑flood protection, and a wide range of Telegram Bot API methods (version 7.2+).

**Current Version:** 1.0.0

---

## Installation

Requires **Python 3.8+**.

```bash
pip install extergram
```

Optional dependencies for persistent FSM storage:

- **Redis**: `pip install redis`
- **JSON** and **SQLite** storages work out of the box.

---

## Quick Start

A minimal echo bot:

```python
import asyncio
from extergram import Bot, ContextTypes
from extergram.ext import CommandHandler, MessageHandler

async def start(context: ContextTypes):
    await context.bot.send_message(
        chat_id=context.message.chat.id,
        text="Hello! I am an Extergram bot."
    )

async def echo(context: ContextTypes):
    await context.bot.send_message(
        chat_id=context.message.chat.id,
        text=f"You said: {context.message.text}"
    )

async def main():
    bot = Bot(token="YOUR_BOT_TOKEN")
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(MessageHandler(echo))
    await bot.polling()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Key Features

- **100% Asynchronous** – all methods are async/await; no blocking.
- **Middleware** – global pre‑/post‑processing of updates.
- **Webhooks** – can be used instead of polling.
- **FSM (Finite State Machine)** – built‑in with memory, JSON, SQLite, and Redis backends.
- **Anti‑flood** – automatic retries with dynamic delays.
- **Rich Keyboard Support** – inline and reply keyboards.
- **Full API Coverage** – messages, media, polls, admin actions, chat management, and more.

---

## API Reference

### Bot Class

#### Constructor

```python
Bot(token: str, default_parse_mode: str = None, fsm_storage: FSMStorage = None)
```

- `token` – bot token from BotFather. If empty, `EmptyTokenError` is raised.
- `default_parse_mode` – global parse mode (`"HTML"`, `"MarkdownV2"`, or `"Markdown"`). If `None`, formatting is disabled by default (no `parse_mode` field sent).
- `fsm_storage` – optional storage for FSM (default: `MemoryFSMStorage`).

#### Polling

```python
await bot.polling(timeout=30)
await bot.run_polling(timeout=30)   # alias
```

#### Webhooks

```python
await bot.set_webhook(url, certificate=None, max_connections=None, allowed_updates=None, drop_pending_updates=None, secret_token=None)
await bot.delete_webhook(drop_pending_updates=None)
info = await bot.get_webhook_info()
await bot.process_webhook(update_dict)   # call from your web framework
```

#### Middleware

```python
from extergram.ext import BaseMiddleware

class MyMiddleware(BaseMiddleware):
    async def process(self, context, call_next):
        print("Before handler")
        await call_next()
        print("After handler")

bot.add_middleware(MyMiddleware())
```

#### Handlers

- `add_handler(handler: BaseHandler)` – registers a handler.
- Handlers are checked in order; the first matching one executes.

Available handlers:

- `MessageHandler(callback, filters=None)` – triggers on text messages. Filters can be a string (exact match), a compiled regex, or a list of them.
- `CommandHandler(command, callback)` – triggers on `/command`. Accepts a string or list of strings.
- `CallbackQueryHandler(callback)` – triggers on inline button presses.
- `StateHandler(state, handler)` – wraps any handler and only triggers if the user is in the given FSM state.

#### Sending Messages

```python
await bot.send_message(chat_id, text, parse_mode=None, disable_web_page_preview=None, disable_notification=None, reply_to_message_id=None, reply_markup=None, message_thread_id=None, business_connection_id=None)
```

- `parse_mode`: if `None`, the bot's `default_parse_mode` is used. Pass `""` to send plain text.
- `reply_markup`: can be a `ButtonsDesign`, `ReplyKeyboard`, or a raw dict.

#### Media

All media methods accept a local file path or an HTTP/HTTPS URL. Local files are uploaded automatically.

```python
await bot.send_photo(chat_id, photo, caption=None, parse_mode=None, reply_markup=None)
await bot.send_document(chat_id, document, caption=None, parse_mode=None, reply_markup=None)
await bot.send_video(chat_id, video, caption=None, parse_mode=None, reply_markup=None)
await bot.send_animation(chat_id, animation, caption=None, parse_mode=None, reply_markup=None)
await bot.send_voice(chat_id, voice, caption=None, parse_mode=None, reply_markup=None)
await bot.send_video_note(chat_id, video_note, reply_markup=None)
await bot.send_sticker(chat_id, sticker, reply_markup=None, disable_notification=None, message_thread_id=None)
await bot.send_media_group(chat_id, media, disable_notification=None, message_thread_id=None)
```

#### Other Send Methods

```python
await bot.send_location(chat_id, latitude, longitude, live_period=None, disable_notification=None, message_thread_id=None, reply_markup=None)
await bot.send_venue(chat_id, latitude, longitude, title, address, foursquare_id=None, disable_notification=None, message_thread_id=None, reply_markup=None)
await bot.send_contact(chat_id, phone_number, first_name, last_name=None, disable_notification=None, message_thread_id=None, reply_markup=None)
await bot.send_poll(chat_id, question, options, is_anonymous=True, type='regular', allows_multiple_answers=False, correct_option_id=None, explanation=None, open_period=None, close_date=None, is_closed=False, disable_notification=None, message_thread_id=None, reply_markup=None)
await bot.send_dice(chat_id, emoji='🎲', disable_notification=None, message_thread_id=None, reply_markup=None)
```

#### Message Editing & Deletion

```python
await bot.edit_message_text(chat_id, message_id, text, parse_mode=None, reply_markup=None)
await bot.edit_message_caption(chat_id, message_id, caption, parse_mode=None, reply_markup=None, show_caption_above_media=None)
await bot.edit_message_media(chat_id, message_id, media, reply_markup=None, business_connection_id=None)
await bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
await bot.delete_message(chat_id, message_id)
await bot.delete_messages(chat_id, message_ids)
```

#### Forwarding & Copying

```python
await bot.forward_message(chat_id, from_chat_id, message_id, disable_notification=None, message_thread_id=None)
await bot.copy_message(chat_id, from_chat_id, message_id, caption=None, parse_mode=None, disable_notification=None, message_thread_id=None, reply_markup=None)
```

#### Callback Queries

```python
await bot.answer_callback_query(callback_query_id, text=None, show_alert=False, url=None, cache_time=None)
```

#### Polls

```python
await bot.stop_poll(chat_id, message_id, reply_markup=None)
```

#### Bot Commands

```python
from extergram import BotCommand
await bot.set_my_commands([BotCommand("start", "Start the bot"), BotCommand("help", "Show help")])
await bot.get_my_commands(scope=None, language_code=None)
await bot.delete_my_commands(scope=None, language_code=None)
```

#### Chat & Administration

```python
await bot.get_chat(chat_id)
await bot.get_chat_member(chat_id, user_id)
await bot.get_chat_administrators(chat_id)
await bot.leave_chat(chat_id)
await bot.set_chat_title(chat_id, title)
await bot.set_chat_description(chat_id, description)
await bot.set_chat_photo(chat_id, photo_path)
await bot.delete_chat_photo(chat_id)
await bot.pin_chat_message(chat_id, message_id, disable_notification=None)
await bot.unpin_chat_message(chat_id, message_id)
await bot.unpin_all_chat_messages(chat_id)
await bot.send_chat_action(chat_id, action, message_thread_id=None)
await bot.get_file(file_id)
await bot.ban_chat_member(chat_id, user_id, until_date=None, revoke_messages=None)
await bot.unban_chat_member(chat_id, user_id, only_if_banned=None)
await bot.restrict_chat_member(chat_id, user_id, permissions: ChatPermissions, until_date=None)
await bot.promote_chat_member(chat_id, user_id, **permissions)   # e.g. can_pin_messages=True
await bot.ban_chat_sender_chat(chat_id, sender_chat_id)
await bot.unban_chat_sender_chat(chat_id, sender_chat_id)
await bot.set_chat_permissions(chat_id, permissions: ChatPermissions)
await bot.approve_chat_join_request(chat_id, user_id)
await bot.decline_chat_join_request(chat_id, user_id)
await bot.export_chat_invite_link(chat_id)
await bot.create_chat_invite_link(chat_id, name=None, expire_date=None, member_limit=None, creates_join_request=None)
await bot.edit_chat_invite_link(chat_id, invite_link, name=None, expire_date=None, member_limit=None, creates_join_request=None)
await bot.revoke_chat_invite_link(chat_id, invite_link)
```

#### Bot Info & Lifecycle

```python
await bot.set_my_description(description, language_code=None)
await bot.set_my_short_description(short_description, language_code=None)
await bot.log_out()
await bot.close()
```

#### Inline Queries (new in 1.0.0)

```python
await bot.answer_inline_query(inline_query_id, results: list, cache_time=None, is_personal=None, next_offset=None, switch_pm_text=None, switch_pm_parameter=None)
```

---

### ContextTypes

Passed to handlers that accept a single argument (`context`). Provides:

- `context.bot` – the Bot instance.
- `context.update` – the raw Update object.
- `context.message` – the Message (if any).
- `context.callback_query` – the CallbackQuery (if any).
- `context.effective_user` – the user who triggered the update.
- `context.effective_chat` – the chat where the update occurred.
- `context.state` – an `FSMContext` instance (requires chat & user ID).

---

### Data Classes

The library provides type‑safe wrappers for Telegram objects:

- `User`, `Chat`, `Message`, `CallbackQuery`, `Update`, `BotCommand`, `ChatPermissions`, `InlineKeyboardMarkup`, `PhotoSize`, `Document`, `Animation`, `Audio`, `Voice`, `Video`, `VideoNote`, `Sticker`, `Contact`, `Dice`, `Location`, `Venue`, `Poll`, `PollOption`, `MessageEntity`

They are automatically created from API responses.

---

### Keyboards

#### Inline Keyboard (`ButtonsDesign`)

```python
from extergram import ButtonsDesign

kb = ButtonsDesign()
kb.add_row(
    ButtonsDesign.create_button("Button 1", "callback_data_1"),
    ButtonsDesign.create_url_button("GitHub", "https://github.com")
)
await bot.send_message(chat_id, "Choose:", reply_markup=kb)
```

#### Reply Keyboard (`ReplyKeyboard` + `KeyboardButton`)

```python
from extergram import ReplyKeyboard, KeyboardButton

kb = ReplyKeyboard(resize_keyboard=True, input_field_placeholder="Send contact")
kb.add_row(
    KeyboardButton("Send phone", request_contact=True),
    KeyboardButton("Send location", request_location=True)
)
await bot.send_message(chat_id, "Press a button:", reply_markup=kb)
```

---

### FSM (Finite State Machine)

Storages:

- `MemoryFSMStorage()` – in‑memory (default).
- `JSONFSMStorage(file_path="fsm_data.json")`
- `SQLiteFSMStorage(db_path="fsm_storage.db")`
- `RedisFSMStorage(redis_url="redis://localhost:6379/0")`

Usage inside a handler (`context.state`):

```python
# set state
await context.state.set_state("waiting_for_name")
# store data
await context.state.update_data(name="John")
# retrieve
data = await context.state.get_data()
# clear
await context.state.clear()
```

Wrap a handler with `StateHandler`:

```python
from extergram.ext import StateHandler, MessageHandler

bot.add_handler(StateHandler("waiting_for_name", MessageHandler(process_name)))
```

---

### Utilities

#### Markdown Helper (safe escaping)

```python
from extergram import Markdown

text = str(Markdown("Hello ").bold("World").text("!"))
# result: Hello *World*!
await bot.send_message(chat_id, text, parse_mode="MarkdownV2")
```

#### Low‑level escaping

```python
from extergram import escape_markdown_v2
safe = escape_markdown_v2("Special chars: _ * [ ] ( )")
```

---

### Exceptions

All exceptions are in `extergram.errors`.

- `EmptyTokenError` – token is empty or only whitespace.
- `UnauthorizedError` – invalid token.
- `FloodControlError` – rate limit hit; contains `retry_after` attribute.
- `TelegramAdminError` – bot lacks admin rights.
- `NetworkError`, `BadRequestError`, `ForbiddenError`, `NotFoundError`, `ConflictError`, `EntityTooLargeError`, `InternalServerError`, `BadGatewayError`, `APIError` (base).

---

## Examples

### Example 1: Command with Inline Keyboard

```python
import asyncio
from extergram import Bot, ContextTypes, ButtonsDesign
from extergram.ext import CommandHandler, CallbackQueryHandler

async def start(context: ContextTypes):
    kb = ButtonsDesign().add_row(
        ButtonsDesign.create_button("Click me", "btn_click")
    )
    await context.bot.send_message(context.message.chat.id, "Press the button:", reply_markup=kb)

async def on_click(context: ContextTypes):
    await context.bot.answer_callback_query(context.callback_query.id, "Button clicked!")
    await context.bot.edit_message_text(
        context.callback_query.message.chat.id,
        context.callback_query.message.message_id,
        "You clicked!"
    )

async def main():
    bot = Bot("YOUR_TOKEN")
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CallbackQueryHandler(on_click))
    await bot.polling()

asyncio.run(main())
```

### Example 2: FSM with SQLite storage

```python
import asyncio
from extergram import Bot, ContextTypes, SQLiteFSMStorage
from extergram.ext import CommandHandler, MessageHandler, StateHandler

async def start(context: ContextTypes):
    await context.state.set_state("ask_age")
    await context.bot.send_message(context.message.chat.id, "How old are you?")

async def age_received(context: ContextTypes):
    age = context.message.text
    await context.state.update_data(age=age)
    await context.state.set_state(None)
    await context.bot.send_message(context.message.chat.id, f"Thanks! Your age is {age}.")

async def main():
    storage = SQLiteFSMStorage("my_bot.db")
    bot = Bot("YOUR_TOKEN", fsm_storage=storage)
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(StateHandler("ask_age", MessageHandler(age_received)))
    await bot.polling()

asyncio.run(main())
```

### Example 3: Webhook with aiohttp

```python
from aiohttp import web
import asyncio
from extergram import Bot

bot = Bot("YOUR_TOKEN")

async def webhook(request):
    update = await request.json()
    await bot.process_webhook(update)
    return web.Response(status=200)

async def set_webhook():
    await bot.set_webhook("https://your-domain.com/webhook")

async def main():
    await set_webhook()
    app = web.Application()
    app.router.add_post("/webhook", webhook)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    await asyncio.Event().wait()

asyncio.run(main())
```

### Example 4: Middleware for logging

```python
import asyncio
from extergram import Bot, ContextTypes
from extergram.ext import BaseMiddleware, CommandHandler

class LogMiddleware(BaseMiddleware):
    async def process(self, context, call_next):
        print(f"Update from user {context.effective_user.id}")
        await call_next()
        print("Handler finished")

async def start(context: ContextTypes):
    await context.bot.send_message(context.message.chat.id, "Hello!")

async def main():
    bot = Bot("YOUR_TOKEN")
    bot.add_middleware(LogMiddleware())
    bot.add_handler(CommandHandler("start", start))
    await bot.polling()

asyncio.run(main())
```

---

## License

MIT License. See [LICENSE](LICENSE) file.

---

## Links

- **GitHub**: [https://github.com/TIBI624/extergram](https://github.com/TIBI624/extergram)
- **PyPI**: [https://pypi.org/project/extergram/](https://pypi.org/project/extergram/)
- **Issues**: [https://github.com/TIBI624/extergram/issues](https://github.com/TIBI624/extergram/issues)