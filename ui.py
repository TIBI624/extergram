# extergram/ui.py

class ButtonsDesign:
    """
    A builder for creating inline keyboards.
    """
    def __init__(self, inline_keyboard: list = None):
        self.keyboard = inline_keyboard if inline_keyboard else []

    def add_row(self, *buttons):
        """
        Adds a row of buttons to the keyboard.
        """
        self.keyboard.append(list(buttons))
        return self

    def to_dict(self):
        """
        Returns the keyboard as a dictionary for the API.
        """
        return {"inline_keyboard": self.keyboard}

    @staticmethod
    def create_button(text: str, callback_data: str):
        """
        Creates a button for an inline keyboard.
        """
        return {"text": text, "callback_data": callback_data}

    @staticmethod
    def create_url_button(text: str, url: str):
        """
        Creates a URL button.
        """
        return {"text": text, "url": url}


class ReplyKeyboard:
    """
    A builder for creating reply keyboards (custom keyboards).
    """
    def __init__(self, resize_keyboard: bool = False, one_time_keyboard: bool = False,
                 selective: bool = False, input_field_placeholder: str = None):
        self.keyboard = []
        self.resize_keyboard = resize_keyboard
        self.one_time_keyboard = one_time_keyboard
        self.selective = selective
        self.input_field_placeholder = input_field_placeholder

    def add_row(self, *buttons):
        """
        Adds a row of buttons to the keyboard.
        Buttons can be plain strings, KeyboardButton objects, or dicts.
        """
        self.keyboard.append(list(buttons))
        return self

    def to_dict(self):
        """
        Returns the keyboard as a dictionary for the API.
        """
        kb = []
        for row in self.keyboard:
            row_buttons = []
            for btn in row:
                if isinstance(btn, KeyboardButton):
                    row_buttons.append(btn.to_dict())
                elif isinstance(btn, dict):
                    row_buttons.append(btn)
                else:
                    row_buttons.append({"text": str(btn)})
            kb.append(row_buttons)
        d = {"keyboard": kb}
        if self.resize_keyboard:
            d["resize_keyboard"] = True
        if self.one_time_keyboard:
            d["one_time_keyboard"] = True
        if self.selective:
            d["selective"] = True
        if self.input_field_placeholder:
            d["input_field_placeholder"] = self.input_field_placeholder
        return d


class KeyboardButton:
    """
    Represents one button of the reply keyboard.
    At most one of the optional fields should be used.
    """
    def __init__(self, text: str, request_contact: bool = False, request_location: bool = False,
                 web_app: dict = None, request_users: dict = None, request_chat: dict = None,
                 request_poll: dict = None):
        self.text = text
        self.request_contact = request_contact
        self.request_location = request_location
        self.web_app = web_app
        self.request_users = request_users
        self.request_chat = request_chat
        self.request_poll = request_poll

        # Ensure at most one active optional field
        optional_fields = [self.request_contact, self.request_location,
                           self.web_app is not None, self.request_users is not None,
                           self.request_chat is not None, self.request_poll is not None]
        if sum(optional_fields) > 1:
            raise ValueError("Only one optional field can be specified per button.")

    def to_dict(self):
        d = {"text": self.text}
        if self.request_contact:
            d["request_contact"] = True
        if self.request_location:
            d["request_location"] = True
        if self.web_app:
            d["web_app"] = self.web_app
        if self.request_users:
            d["request_users"] = self.request_users
        if self.request_chat:
            d["request_chat"] = self.request_chat
        if self.request_poll:
            d["request_poll"] = self.request_poll
        return d