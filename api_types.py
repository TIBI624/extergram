# extergram/api_types.py

class User:
    """This object represents a Telegram user or bot."""
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.is_bot = data.get('is_bot', False)
        self.first_name = data.get('first_name')
        self.last_name = data.get('last_name')
        self.username = data.get('username')


class Chat:
    """This object represents a chat."""
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.type = data.get('type')
        self.title = data.get('title')
        self.username = data.get('username')


class Message:
    """This object represents a message."""
    def __init__(self, data: dict):
        self.message_id = data.get('message_id')
        self.from_user = User(data['from']) if 'from' in data and data['from'] else None
        self.chat = Chat(data['chat']) if 'chat' in data and data['chat'] else None
        self.date = data.get('date')
        self.text = data.get('text')
        self.caption = data.get('caption')
        # Other fields like photo, document, etc., can be added here.


class CallbackQuery:
    """This object represents an incoming callback query from a callback button in an inline keyboard."""
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.from_user = User(data['from']) if 'from' in data and data['from'] else None
        self.message = Message(data['message']) if 'message' in data and data['message'] else None
        self.data = data.get('data')


class Update:
    """
    This object represents an incoming update.
    At most one of the optional parameters can be present in any given update.
    """
    def __init__(self, data: dict):
        self.update_id = data.get('update_id')
        self.message = Message(data['message']) if 'message' in data else None
        self.edited_message = Message(data['edited_message']) if 'edited_message' in data else None
        self.callback_query = CallbackQuery(data['callback_query']) if 'callback_query' in data else None


class BotCommand:
    """This object represents a bot command."""
    def __init__(self, command: str, description: str):
        self.command = command
        self.description = description

    def to_dict(self):
        return {"command": self.command, "description": self.description}


class ChatPermissions:
    """
    Describes actions that a non-administrator user is allowed to take in a chat.
    Pass 'False' to explicitly restrict an action, or 'None'/'True' to allow it or leave it unchanged.
    """
    def __init__(
        self,
        can_send_messages: bool = None,
        can_send_audios: bool = None,
        can_send_documents: bool = None,
        can_send_photos: bool = None,
        can_send_videos: bool = None,
        can_send_video_notes: bool = None,
        can_send_voice_notes: bool = None,
        can_send_polls: bool = None,
        can_send_other_messages: bool = None,
        can_add_web_page_previews: bool = None,
        can_change_info: bool = None,
        can_invite_users: bool = None,
        can_pin_messages: bool = None,
        can_manage_topics: bool = None,
    ):
        self.can_send_messages = can_send_messages
        self.can_send_audios = can_send_audios
        self.can_send_documents = can_send_documents
        self.can_send_photos = can_send_photos
        self.can_send_videos = can_send_videos
        self.can_send_video_notes = can_send_video_notes
        self.can_send_voice_notes = can_send_voice_notes
        self.can_send_polls = can_send_polls
        self.can_send_other_messages = can_send_other_messages
        self.can_add_web_page_previews = can_add_web_page_previews
        self.can_change_info = can_change_info
        self.can_invite_users = can_invite_users
        self.can_pin_messages = can_pin_messages
        self.can_manage_topics = can_manage_topics

    def to_dict(self):
        """
        Converts the object to a dictionary, omitting any permissions that were not set (are None).
        This is important for the Telegram API, as omitting a key means "do not change".
        """
        return {key: value for key, value in self.__dict__.items() if value is not None}