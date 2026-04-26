# Extergram — Asynchronous Telegram Bot Framework

*Disclaimer: This project is an independent open-source library and is not affiliated with, associated with, authorized by, endorsed by, or in any way officially connected with Telegram FZ-LLC or any of its subsidiaries or its affiliates.*

**Extergram** is a modern, simple, and fully asynchronous library for creating Telegram bots in Python using `httpx`. It provides a clean API, built-in FSM (Finite State Machine) with multiple storage backends, anti-flood protection, support for both inline and reply keyboards, and a wide range of Telegram Bot API methods.

**Current Version:** 0.9.0

---

## Installation

Extergram requires **Python 3.8+**.

```bash
pip install extergram
```

Optional dependencies for persistent FSM storage:

- **Redis**: `pip install redis`
- **JSON** and **SQLite** storages work out of the box (no extra packages required).

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

**Note:** Starting from version 0.9.0, the default `parse_mode` is `"MarkdownV2"`. To send messages without formatting, pass `parse_mode=""` explicitly.

---

## API Reference

### Core Concepts

- **Bot** – the main class that interacts with Telegram API.
- **ContextTypes** – passed to handlers, provides access to bot, update, and FSM.
- **Handlers** – define how to process updates (messages, commands, callbacks). Handlers are checked sequentially; the first matching handler is executed.
- **FSM** – built-in finite state machine for multi-step dialogs, with optional persistent storage (Memory, JSON, SQLite, Redis).

---

### 1. Bot Class

#### Constructor

```python
Bot(token: str, default_parse_mode: str = None, fsm_storage: FSMStorage = None)
```

- `token` – your bot token from BotFather.
- `default_parse_mode` – default parse mode for messages (`"HTML"`, `"MarkdownV2"`, or `"Markdown"`). If not set, `"MarkdownV2"` is used. Pass `""` to disable formatting.
- `fsm_storage` – an instance of `FSMStorage` (e.g., `MemoryFSMStorage`, `RedisFSMStorage`). Defaults to `MemoryFSMStorage` if not provided.

#### Methods

##### Polling

```python
async polling(timeout: int = 30)
```
Starts long polling. This coroutine runs forever until interrupted.

##### Handler Registration

```python
add_handler(handler: BaseHandler)
```
Registers a handler. Must be an instance of `BaseHandler`.

##### Getting Updates

```python
async get_updates(offset: int = None, timeout: int = 30) -> List[dict]
```
Fetches raw updates from Telegram. Normally you don't need to call this directly.

---

##### Sending Messages

```python
async send_message(
    chat_id: int,
    text: str,
    parse_mode: str = None,
    disable_web_page_preview: bool = None,
    disable_notification: bool = None,
    reply_to_message_id: int = None,
    reply_markup = None,
    message_thread_id: int = None,
    business_connection_id: str = None
) -> dict
```

- `parse_mode`: If `None`, the bot's `default_parse_mode` is used. Pass `""` to send plain text.
- `reply_markup`: Can be a `ButtonsDesign` instance (inline keyboard), a `ReplyKeyboard` instance (reply keyboard), or a raw dict.

##### Sending Media

```python
async send_photo(chat_id: int, photo: str, caption: str = None, parse_mode: str = None, reply_markup=None) -> dict
async send_document(chat_id: int, document: str, caption: str = None, parse_mode: str = None, reply_markup=None) -> dict
async send_video(chat_id: int, video: str, caption: str = None, parse_mode: str = None, reply_markup=None) -> dict
async send_animation(chat_id: int, animation: str, caption: str = None, parse_mode: str = None, reply_markup=None) -> dict
async send_voice(chat_id: int, voice: str, caption: str = None, parse_mode: str = None, reply_markup=None) -> dict
async send_video_note(chat_id: int, video_note: str, reply_markup=None) -> dict
async send_sticker(chat_id: int, sticker: str, reply_markup=None, disable_notification: bool = None, message_thread_id: int = None) -> dict
```
All media methods accept a local file path or an HTTP URL. Local files are uploaded as multipart/form-data.

##### Sending Other Content

```python
async send_location(
    chat_id: int,
    latitude: float,
    longitude: float,
    live_period: int = None,
    disable_notification: bool = None,
    message_thread_id: int = None,
    reply_markup = None
) -> dict

async send_venue(
    chat_id: int,
    latitude: float,
    longitude: float,
    title: str,
    address: str,
    foursquare_id: str = None,
    disable_notification: bool = None,
    message_thread_id: int = None,
    reply_markup = None
) -> dict

async send_contact(
    chat_id: int,
    phone_number: str,
    first_name: str,
    last_name: str = None,
    disable_notification: bool = None,
    message_thread_id: int = None,
    reply_markup = None
) -> dict

async send_poll(
    chat_id: int,
    question: str,
    options: list,
    is_anonymous: bool = True,
    type: str = 'regular',
    allows_multiple_answers: bool = False,
    correct_option_id: int = None,
    explanation: str = None,
    open_period: int = None,
    close_date: int = None,
    is_closed: bool = False,
    disable_notification: bool = None,
    message_thread_id: int = None,
    reply_markup = None
) -> dict

async send_dice(
    chat_id: int,
    emoji: str = '🎲',
    disable_notification: bool = None,
    message_thread_id: int = None,
    reply_markup = None
) -> dict
```

##### Message Draft (Forum Topics)

```python
async send_message_draft(
    chat_id: int,
    draft_id: int,
    text: str,
    parse_mode: str = None,
    entities: list = None,
    message_thread_id: int = None
) -> dict
```
Streams a partial message to a chat (for bots with forum topic mode enabled). The `draft_id` must be a non-zero unique identifier.

##### Media Groups

```python
async send_media_group(
    chat_id: int,
    media: list,
    disable_notification: bool = None,
    message_thread_id: int = None
) -> dict
```
- `media` is a list of dictionaries representing InputMedia objects (e.g., `{"type": "photo", "media": "file_id_or_url"}`).

##### Forwarding and Copying Messages

```python
async forward_message(
    chat_id: int,
    from_chat_id: int,
    message_id: int,
    disable_notification: bool = None,
    message_thread_id: int = None
) -> dict

async copy_message(
    chat_id: int,
    from_chat_id: int,
    message_id: int,
    caption: str = None,
    parse_mode: str = None,
    disable_notification: bool = None,
    message_thread_id: int = None,
    reply_markup = None
) -> dict
```

##### Editing Messages

```python
async edit_message_text(
    chat_id: int,
    message_id: int,
    text: str,
    parse_mode: str = None,
    reply_markup = None
) -> dict

async edit_message_caption(
    chat_id: int,
    message_id: int,
    caption: str,
    parse_mode: str = None,
    reply_markup = None,
    show_caption_above_media: bool = None
) -> dict

async edit_message_media(
    chat_id: int,
    message_id: int,
    media: dict,
    reply_markup = None,
    business_connection_id: str = None
) -> dict

async edit_message_reply_markup(
    chat_id: int,
    message_id: int,
    reply_markup = None
) -> dict
```

##### Deleting Messages

```python
async delete_message(chat_id: int, message_id: int) -> dict
async delete_messages(chat_id: int, message_ids: list) -> dict
```

##### Callback Queries

```python
async answer_callback_query(
    callback_query_id: str,
    text: str = None,
    show_alert: bool = False,
    url: str = None,
    cache_time: int = None
) -> dict
```

##### Polls

```python
async stop_poll(chat_id: int, message_id: int, reply_markup=None) -> dict
```

##### Bot Commands

```python
async set_my_commands(commands: List[BotCommand]) -> dict
```

##### Administration

```python
async ban_chat_member(
    chat_id: int,
    user_id: int,
    until_date: int = None,
    revoke_messages: bool = None
) -> dict

async unban_chat_member(
    chat_id: int,
    user_id: int,
    only_if_banned: bool = None
) -> dict

async restrict_chat_member(
    chat_id: int,
    user_id: int,
    permissions: ChatPermissions,
    until_date: int = None
) -> dict

async promote_chat_member(
    chat_id: int,
    user_id: int,
    **permissions
) -> dict

async approve_chat_join_request(chat_id: int, user_id: int) -> dict
async decline_chat_join_request(chat_id: int, user_id: int) -> dict
```

---

### 2. ContextTypes

Passed to handlers (callback receives either `(bot, event)` or `(context,)`). Provides:

- `bot` – the Bot instance.
- `update` – the raw Update object.
- `message` – the Message object (if present).
- `callback_query` – the CallbackQuery object (if present).
- `effective_user` – the user who triggered the update.
- `effective_chat` – the chat where the update occurred.
- `state` – an `FSMContext` instance for the current user/chat.

---

### 3. Data Classes

These classes mirror Telegram API objects. They are created automatically from incoming updates.

- **User**: `id`, `is_bot`, `first_name`, `last_name`, `username`
- **Chat**: `id`, `type`, `title`, `username`
- **Message**: `message_id`, `from_user`, `chat`, `date`, `text`, `caption`
- **CallbackQuery**: `id`, `from_user`, `message`, `data`
- **Update**: `update_id`, `message`, `edited_message`, `callback_query`
- **BotCommand**: simple container for commands.
- **ChatPermissions**: used with `restrict_chat_member`. All permissions default to `None` (meaning "don't change"). Use `True` to allow, `False` to disallow.

Example:
```python
perms = ChatPermissions(can_send_messages=False, can_send_photos=False)
```

---

### 4. UI: Keyboards

Extergram supports both inline and reply keyboards.

#### Inline Keyboard (ButtonsDesign)

```python
from extergram import ButtonsDesign

kb = ButtonsDesign()
kb.add_row(
    ButtonsDesign.create_button("Click me", "callback_data"),
    ButtonsDesign.create_url_button("GitHub", "https://github.com")
)
```

- `create_button(text, callback_data)`
- `create_url_button(text, url)`
- `add_row(*buttons)` – adds a row of buttons.
- `to_dict()` – returns the keyboard as a dict for the API.

#### Reply Keyboard (ReplyKeyboard & KeyboardButton)

```python
from extergram import ReplyKeyboard, KeyboardButton

kb = ReplyKeyboard(resize_keyboard=True, input_field_placeholder="Choose an option")
kb.add_row(
    KeyboardButton("Send my phone", request_contact=True),
    KeyboardButton("Share location", request_location=True)
)
```

- `ReplyKeyboard(resize_keyboard=False, one_time_keyboard=False, selective=False, input_field_placeholder=None)`
- `add_row(*buttons)` – adds a row. Buttons can be plain strings, `KeyboardButton` objects, or dicts.
- `KeyboardButton(text, request_contact=False, request_location=False, web_app=None, request_users=None, request_chat=None, request_poll=None)` – only one optional field can be active at a time.

---

### 5. Utilities

#### Markdown Helper

Safely builds MarkdownV2 strings with automatic escaping.

```python
from extergram import Markdown

text = str(
    Markdown("Hello ")
    .bold("World")
    .text(" this is ")
    .italic("escaped")
)
await bot.send_message(chat_id, text)  # parse_mode is already "MarkdownV2" by default
```

Methods:
- `text(text)` – appends plain text (escaped).
- `bold(text)` – appends bold text.
- `italic(text)` – appends italic text.
- `__str__()` – returns the final string.

#### escape_markdown_v2(text)
Low-level function to escape MarkdownV2 special characters.

---

### 6. Documentation Access

```python
from extergram import Docs
print(Docs.get_docs())   # returns a link to GitHub README
Docs.print_docs()        # prints the link
```

---

### 7. Handlers (extergram.ext)

All handlers inherit from `BaseHandler` and must implement `check_update`. They are registered via `bot.add_handler()`.

- **BaseHandler** – abstract base class.
- **MessageHandler** – triggers on any text message.
- **CommandHandler(command, callback)** – triggers on a command (e.g., `/start`). Accepts a single command string or a list of strings.
- **CallbackQueryHandler** – triggers on any callback query.
- **StateHandler(state, handler)** – wraps another handler and only triggers if the user is in a specific FSM state. Must be used with FSM storage.

Example:
```python
from extergram.ext import StateHandler, MessageHandler

bot.add_handler(StateHandler("waiting_for_name", MessageHandler(process_name)))
```

---

### 8. FSM (Finite State Machine)

Extergram provides a flexible FSM with swappable storage backends.

#### Storage Backends

- **MemoryFSMStorage** – in-memory, volatile. State is lost on restart.
- **JSONFSMStorage** – persists state and data to a JSON file. Constructor: `JSONFSMStorage(file_path="fsm_data.json")`.
- **SQLiteFSMStorage** – persists state to a SQLite database. Constructor: `SQLiteFSMStorage(db_path="fsm_storage.db")`.
- **RedisFSMStorage** – persists state to a Redis server (requires `pip install redis`). Constructor: `RedisFSMStorage(redis_url="redis://localhost:6379/0", **kwargs)`.

You can pass your chosen storage to the bot:
```python
from extergram import Bot, RedisFSMStorage

bot = Bot(token="TOKEN", fsm_storage=RedisFSMStorage("redis://localhost:6379"))
```

If no storage is specified, `MemoryFSMStorage` is used by default.

#### FSMContext

Obtained via `context.state`. Methods:

- `async get_state() -> Optional[str]`
- `async set_state(state: Optional[str])` – pass `None` to reset state.
- `async get_data() -> dict`
- `async set_data(data: dict)`
- `async update_data(**kwargs)`
- `async clear()` – clears both state and data.

---

### 9. Exceptions

All exceptions inherit from `extergram.errors.ExtergramError`.

- `APIError` – base for API errors. Contains `description`, `error_code`, and optional `parameters` (e.g., `retry_after`).
- `NetworkError` – network-related issues.
- `BadRequestError` (400)
- `UnauthorizedError` (401)
- `ForbiddenError` (403)
- `NotFoundError` (404)
- `ConflictError` (409) – another bot instance is running.
- `EntityTooLargeError` (413)
- `FloodControlError` (429) – too many requests. The library automatically retries after `retry_after` seconds (up to 5 times). If all retries fail, this exception is raised.
- `InternalServerError` (500)
- `BadGatewayError` (502)
- `TelegramAdminError` – insufficient rights for admin actions (subclass of `ForbiddenError`).

---

## Anti-Flood System

Extergram automatically tracks request frequency and introduces dynamic delays when approaching Telegram's rate limits. When a `429` response is received, the library waits for the duration specified in `retry_after` and retries the request up to 5 times. This ensures smooth operation under high load.

---

## Examples

### Example 1: Echo Bot with Commands

```python
import asyncio
from extergram import Bot, ContextTypes
from extergram.ext import CommandHandler, MessageHandler

async def start(context: ContextTypes):
    await context.bot.send_message(
        context.message.chat.id,
        "Welcome! Send me any text and I'll echo it."
    )

async def echo(context: ContextTypes):
    await context.bot.send_message(
        context.message.chat.id,
        f"Echo: {context.message.text}"
    )

async def main():
    bot = Bot(token="YOUR_TOKEN")
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(MessageHandler(echo))
    await bot.polling()

asyncio.run(main())
```

### Example 2: Inline Keyboard with Callback

```python
import asyncio
from extergram import Bot, ContextTypes, ButtonsDesign
from extergram.ext import CommandHandler, CallbackQueryHandler

async def start(context: ContextTypes):
    kb = ButtonsDesign().add_row(
        ButtonsDesign.create_button("Green", "color_green"),
        ButtonsDesign.create_button("Red", "color_red")
    )
    await context.bot.send_message(
        context.message.chat.id,
        "Choose a color:",
        reply_markup=kb
    )

async def button_handler(context: ContextTypes):
    query = context.callback_query
    color = query.data.split('_')[1]
    await context.bot.answer_callback_query(query.id, text=f"You chose {color}")
    await context.bot.send_message(
        query.message.chat.id,
        f"Your favorite color is {color}!"
    )

async def main():
    bot = Bot(token="YOUR_TOKEN")
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CallbackQueryHandler(button_handler))
    await bot.polling()

asyncio.run(main())
```

### Example 3: FSM – Collecting User Info (with JSON Storage)

```python
import asyncio
from extergram import Bot, ContextTypes, JSONFSMStorage
from extergram.ext import CommandHandler, MessageHandler, StateHandler

async def start(context: ContextTypes):
    await context.state.set_state("waiting_for_name")
    await context.bot.send_message(context.message.chat.id, "What's your name?")

async def process_name(context: ContextTypes):
    name = context.message.text
    await context.state.update_data(name=name)
    await context.state.set_state("waiting_for_age")
    await context.bot.send_message(context.message.chat.id, f"Nice to meet you, {name}! How old are you?")

async def process_age(context: ContextTypes):
    try:
        age = int(context.message.text)
    except ValueError:
        await context.bot.send_message(context.message.chat.id, "Please enter a number.")
        return
    data = await context.state.get_data()
    name = data.get("name")
    await context.state.clear()
    await context.bot.send_message(context.message.chat.id, f"Thank you! You are {name}, {age} years old.")

async def main():
    # State will be saved to fsm_data.json
    bot = Bot(token="YOUR_TOKEN", fsm_storage=JSONFSMStorage("fsm_data.json"))
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(StateHandler("waiting_for_name", MessageHandler(process_name)))
    bot.add_handler(StateHandler("waiting_for_age", MessageHandler(process_age)))
    await bot.polling()

asyncio.run(main())
```

### Example 4: Sending Photo and Document

```python
import asyncio
from extergram import Bot, ContextTypes
from extergram.ext import CommandHandler

async def photo(context: ContextTypes):
    await context.bot.send_photo(
        context.message.chat.id,
        photo="https://picsum.photos/400/300",
        caption="Random photo"
    )

async def doc(context: ContextTypes):
    await context.bot.send_document(
        context.message.chat.id,
        document="/path/to/file.pdf",
        caption="My document"
    )

async def main():
    bot = Bot(token="YOUR_TOKEN")
    bot.add_handler(CommandHandler("photo", photo))
    bot.add_handler(CommandHandler("doc", doc))
    await bot.polling()

asyncio.run(main())
```

### Example 5: Admin Command with Error Handling

```python
import asyncio
from extergram import Bot, ContextTypes, errors
from extergram.ext import CommandHandler

async def kick(context: ContextTypes):
    if not context.message.reply_to_message:
        await context.bot.send_message(context.message.chat.id, "Reply to a user's message to kick them.")
        return
    user_id = context.message.reply_to_message.from_user.id
    try:
        await context.bot.ban_chat_member(context.message.chat.id, user_id)
        await context.bot.send_message(context.message.chat.id, f"User {user_id} has been kicked.")
    except errors.TelegramAdminError as e:
        await context.bot.send_message(context.message.chat.id, f"Failed: {e}")

async def main():
    bot = Bot(token="YOUR_TOKEN")
    bot.add_handler(CommandHandler("kick", kick))
    await bot.polling()

asyncio.run(main())
```

### Example 6: Reply Keyboard with Location and Contact

```python
import asyncio
from extergram import Bot, ContextTypes, ReplyKeyboard, KeyboardButton
from extergram.ext import CommandHandler, MessageHandler

async def start(context: ContextTypes):
    kb = ReplyKeyboard(resize_keyboard=True, input_field_placeholder="Select an option")
    kb.add_row(
        KeyboardButton("Send my phone", request_contact=True),
        KeyboardButton("Share location", request_location=True)
    )
    await context.bot.send_message(context.message.chat.id, "Use the buttons below:", reply_markup=kb)

async def handle_message(context: ContextTypes):
    if context.message.contact:
        await context.bot.send_message(context.message.chat.id, f"Got your phone: {context.message.contact.phone_number}")
    elif context.message.location:
        await context.bot.send_message(context.message.chat.id, "Location received!")
    else:
        await context.bot.send_message(context.message.chat.id, "Please use the keyboard buttons.")

async def main():
    bot = Bot(token="YOUR_TOKEN")
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(MessageHandler(handle_message))
    await bot.polling()

asyncio.run(main())
```

### Example 7: Dice and Poll

```python
import asyncio
from extergram import Bot, ContextTypes
from extergram.ext import CommandHandler

async def dice(context: ContextTypes):
    await context.bot.send_dice(context.message.chat.id, emoji="🎲")

async def poll(context: ContextTypes):
    await context.bot.send_poll(
        context.message.chat.id,
        question="What's your favorite language?",
        options=["Python", "JavaScript", "Go"],
        is_anonymous=False
    )

async def main():
    bot = Bot(token="YOUR_TOKEN")
    bot.add_handler(CommandHandler("dice", dice))
    bot.add_handler(CommandHandler("poll", poll))
    await bot.polling()

asyncio.run(main())
```

### Example 8: Media Group

```python
import asyncio
from extergram import Bot, ContextTypes
from extergram.ext import CommandHandler

async def album(context: ContextTypes):
    media = [
        {"type": "photo", "media": "https://picsum.photos/id/1/400/300"},
        {"type": "photo", "media": "https://picsum.photos/id/2/400/300"}
    ]
    await context.bot.send_media_group(context.message.chat.id, media)

async def main():
    bot = Bot(token="YOUR_TOKEN")
    bot.add_handler(CommandHandler("album", album))
    await bot.polling()

asyncio.run(main())
```

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Links

- **GitHub**: [https://github.com/TIBI624/extergram](https://github.com/TIBI624/extergram)
- **Issue Tracker**: [https://github.com/TIBI624/extergram/issues](https://github.com/TIBI624/extergram/issues)
- **PyPI**: [https://pypi.org/project/extergram/](https://pypi.org/project/extergram/)