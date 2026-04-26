# extergram/api_types.py

from typing import List, Optional, Union, Dict, Any

class User:
    """Telegram user or bot."""
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.is_bot = data.get('is_bot', False)
        self.first_name = data.get('first_name')
        self.last_name = data.get('last_name')
        self.username = data.get('username')
        self.language_code = data.get('language_code')
        self.is_premium = data.get('is_premium')
        self.added_to_attachment_menu = data.get('added_to_attachment_menu')
        self.can_join_groups = data.get('can_join_groups')
        self.can_read_all_group_messages = data.get('can_read_all_group_messages')
        self.supports_inline_queries = data.get('supports_inline_queries')
        self.can_connect_to_business = data.get('can_connect_to_business')
        self.has_main_web_app = data.get('has_main_web_app')
        self.has_topics_enabled = data.get('has_topics_enabled')
        self.allows_users_to_create_topics = data.get('allows_users_to_create_topics')

class Chat:
    """Telegram chat."""
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.type = data.get('type')
        self.title = data.get('title')
        self.username = data.get('username')
        self.first_name = data.get('first_name')
        self.last_name = data.get('last_name')
        self.is_forum = data.get('is_forum')
        self.is_direct_messages = data.get('is_direct_messages')
        # ChatFullInfo fields (only present in getChat)
        self.accent_color_id = data.get('accent_color_id')
        self.max_reaction_count = data.get('max_reaction_count')
        self.photo = ChatPhoto(data['photo']) if 'photo' in data else None
        self.bio = data.get('bio')
        self.birthdate = Birthdate(data['birthdate']) if 'birthdate' in data else None
        self.business_intro = data.get('business_intro')       # dict
        self.business_location = data.get('business_location') # dict
        self.business_opening_hours = data.get('business_opening_hours')
        self.personal_chat = Chat(data['personal_chat']) if 'personal_chat' in data else None
        self.parent_chat = Chat(data['parent_chat']) if 'parent_chat' in data else None
        self.available_reactions = data.get('available_reactions')
        self.background_custom_emoji_id = data.get('background_custom_emoji_id')
        self.profile_accent_color_id = data.get('profile_accent_color_id')
        self.profile_background_custom_emoji_id = data.get('profile_background_custom_emoji_id')
        self.emoji_status_custom_emoji_id = data.get('emoji_status_custom_emoji_id')
        self.emoji_status_expiration_date = data.get('emoji_status_expiration_date')
        self.has_private_forwards = data.get('has_private_forwards')
        self.has_restricted_voice_and_video_messages = data.get('has_restricted_voice_and_video_messages')
        self.join_to_send_messages = data.get('join_to_send_messages')
        self.join_by_request = data.get('join_by_request')
        self.description = data.get('description')
        self.invite_link = data.get('invite_link')
        self.pinned_message = Message(data['pinned_message']) if 'pinned_message' in data else None
        self.permissions = ChatPermissions(**data['permissions']) if 'permissions' in data else None
        self.accepted_gift_types = data.get('accepted_gift_types')
        self.slow_mode_delay = data.get('slow_mode_delay')
        self.unrestrict_boost_count = data.get('unrestrict_boost_count')
        self.message_auto_delete_time = data.get('message_auto_delete_time')
        self.has_aggressive_anti_spam_enabled = data.get('has_aggressive_anti_spam_enabled')
        self.has_hidden_members = data.get('has_hidden_members')
        self.has_protected_content = data.get('has_protected_content')
        self.has_visible_history = data.get('has_visible_history')
        self.sticker_set_name = data.get('sticker_set_name')
        self.can_set_sticker_set = data.get('can_set_sticker_set')
        self.custom_emoji_sticker_set_name = data.get('custom_emoji_sticker_set_name')
        self.linked_chat_id = data.get('linked_chat_id')
        self.location = Location(data['location']) if 'location' in data else None

class ChatPhoto:
    """Chat photo."""
    def __init__(self, data: dict):
        self.small_file_id = data.get('small_file_id')
        self.small_file_unique_id = data.get('small_file_unique_id')
        self.big_file_id = data.get('big_file_id')
        self.big_file_unique_id = data.get('big_file_unique_id')

class Birthdate:
    """User's birthdate."""
    def __init__(self, data: dict):
        self.day = data.get('day')
        self.month = data.get('month')
        self.year = data.get('year')

class Message:
    """Telegram message."""
    def __init__(self, data: dict):
        self.message_id = data.get('message_id')
        self.message_thread_id = data.get('message_thread_id')
        self.from_user = User(data['from']) if 'from' in data else None
        self.sender_chat = Chat(data['sender_chat']) if 'sender_chat' in data else None
        self.date = data.get('date')
        self.chat = Chat(data['chat']) if 'chat' in data else None
        self.text = data.get('text')
        self.caption = data.get('caption')
        self.entities = [MessageEntity(e) for e in data.get('entities', [])]
        self.caption_entities = [MessageEntity(e) for e in data.get('caption_entities', [])]
        self.photo = [PhotoSize(p) for p in data.get('photo', [])]
        self.document = Document(data['document']) if 'document' in data else None
        self.video = Video(data['video']) if 'video' in data else None
        self.video_note = VideoNote(data['video_note']) if 'video_note' in data else None
        self.voice = Voice(data['voice']) if 'voice' in data else None
        self.audio = Audio(data['audio']) if 'audio' in data else None
        self.animation = Animation(data['animation']) if 'animation' in data else None
        self.sticker = Sticker(data['sticker']) if 'sticker' in data else None
        self.contact = Contact(data['contact']) if 'contact' in data else None
        self.dice = Dice(data['dice']) if 'dice' in data else None
        self.poll = Poll(data['poll']) if 'poll' in data else None
        self.location = Location(data['location']) if 'location' in data else None
        self.venue = Venue(data['venue']) if 'venue' in data else None
        self.story = Story(data['story']) if 'story' in data else None
        self.new_chat_members = [User(u) for u in data.get('new_chat_members', [])]
        self.left_chat_member = User(data['left_chat_member']) if 'left_chat_member' in data else None
        self.chat_owner_left = data.get('chat_owner_left')      # dict or object
        self.chat_owner_changed = data.get('chat_owner_changed')
        self.new_chat_title = data.get('new_chat_title')
        self.new_chat_photo = [PhotoSize(p) for p in data.get('new_chat_photo', [])]
        self.delete_chat_photo = data.get('delete_chat_photo', False)
        self.group_chat_created = data.get('group_chat_created', False)
        self.supergroup_chat_created = data.get('supergroup_chat_created', False)
        self.channel_chat_created = data.get('channel_chat_created', False)
        self.message_auto_delete_timer_changed = MessageAutoDeleteTimerChanged(data['message_auto_delete_timer_changed']) if 'message_auto_delete_timer_changed' in data else None
        self.migrate_to_chat_id = data.get('migrate_to_chat_id')
        self.migrate_from_chat_id = data.get('migrate_from_chat_id')
        self.pinned_message = Message(data['pinned_message']) if 'pinned_message' in data else None
        self.invoice = Invoice(data['invoice']) if 'invoice' in data else None
        self.successful_payment = SuccessfulPayment(data['successful_payment']) if 'successful_payment' in data else None
        self.refunded_payment = RefundedPayment(data['refunded_payment']) if 'refunded_payment' in data else None
        self.users_shared = UsersShared(data['users_shared']) if 'users_shared' in data else None
        self.chat_shared = ChatShared(data['chat_shared']) if 'chat_shared' in data else None
        self.gift = GiftInfo(data['gift']) if 'gift' in data else None
        self.unique_gift = UniqueGiftInfo(data['unique_gift']) if 'unique_gift' in data else None
        self.gift_upgrade_sent = GiftInfo(data['gift_upgrade_sent']) if 'gift_upgrade_sent' in data else None
        self.connected_website = data.get('connected_website')
        self.write_access_allowed = WriteAccessAllowed(data['write_access_allowed']) if 'write_access_allowed' in data else None
        self.passport_data = PassportData(data['passport_data']) if 'passport_data' in data else None
        self.proximity_alert_triggered = ProximityAlertTriggered(data['proximity_alert_triggered']) if 'proximity_alert_triggered' in data else None
        self.boost_added = ChatBoostAdded(data['boost_added']) if 'boost_added' in data else None
        self.chat_background_set = ChatBackground(data['chat_background_set']) if 'chat_background_set' in data else None
        self.checklist_tasks_done = data.get('checklist_tasks_done')
        self.checklist_tasks_added = data.get('checklist_tasks_added')
        self.video_chat_scheduled = VideoChatScheduled(data['video_chat_scheduled']) if 'video_chat_scheduled' in data else None
        self.video_chat_started = VideoChatStarted(data['video_chat_started']) if 'video_chat_started' in data else None
        self.video_chat_ended = VideoChatEnded(data['video_chat_ended']) if 'video_chat_ended' in data else None
        self.video_chat_participants_invited = VideoChatParticipantsInvited(data['video_chat_participants_invited']) if 'video_chat_participants_invited' in data else None
        self.web_app_data = WebAppData(data['web_app_data']) if 'web_app_data' in data else None
        self.reply_to_message = Message(data['reply_to_message']) if 'reply_to_message' in data else None
        self.is_topic_message = data.get('is_topic_message', False)
        self.is_automatic_forward = data.get('is_automatic_forward', False)
        self.has_protected_content = data.get('has_protected_content', False)
        self.is_paid_post = data.get('is_paid_post', False)
        self.media_group_id = data.get('media_group_id')
        self.author_signature = data.get('author_signature')
        self.reply_markup = InlineKeyboardMarkup(data['reply_markup']) if 'reply_markup' in data else None

    def __repr__(self):
        return f"<Message {self.message_id} from {self.chat.id if self.chat else '?'}>"

class CallbackQuery:
    """Incoming callback query."""
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.from_user = User(data['from']) if 'from' in data else None
        self.message = Message(data['message']) if 'message' in data else None
        self.inline_message_id = data.get('inline_message_id')
        self.data = data.get('data')
        self.game_short_name = data.get('game_short_name')

class Update:
    """Incoming update."""
    def __init__(self, data: dict):
        self.update_id = data.get('update_id')
        self.message = Message(data['message']) if 'message' in data else None
        self.edited_message = Message(data['edited_message']) if 'edited_message' in data else None
        self.callback_query = CallbackQuery(data['callback_query']) if 'callback_query' in data else None
        # Other update types may be added

class BotCommand:
    """Bot command."""
    def __init__(self, command: str, description: str):
        self.command = command
        self.description = description

    def to_dict(self):
        return {"command": self.command, "description": self.description}

class ChatPermissions:
    """Chat member permissions."""
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
        return {key: value for key, value in self.__dict__.items() if value is not None}

# Additional classes for message fields

class Contact:
    def __init__(self, data: dict):
        self.phone_number = data.get('phone_number')
        self.first_name = data.get('first_name')
        self.last_name = data.get('last_name')
        self.user_id = data.get('user_id')
        self.vcard = data.get('vcard')

class Dice:
    def __init__(self, data: dict):
        self.emoji = data.get('emoji')
        self.value = data.get('value')

class Location:
    def __init__(self, data: dict):
        self.latitude = data.get('latitude')
        self.longitude = data.get('longitude')
        self.horizontal_accuracy = data.get('horizontal_accuracy')
        self.live_period = data.get('live_period')
        self.heading = data.get('heading')
        self.proximity_alert_radius = data.get('proximity_alert_radius')

class Venue:
    def __init__(self, data: dict):
        self.location = Location(data['location']) if 'location' in data else None
        self.title = data.get('title')
        self.address = data.get('address')
        self.foursquare_id = data.get('foursquare_id')
        self.foursquare_type = data.get('foursquare_type')
        self.google_place_id = data.get('google_place_id')
        self.google_place_type = data.get('google_place_type')

class PhotoSize:
    def __init__(self, data: dict):
        self.file_id = data.get('file_id')
        self.file_unique_id = data.get('file_unique_id')
        self.width = data.get('width')
        self.height = data.get('height')
        self.file_size = data.get('file_size')

class Document:
    def __init__(self, data: dict):
        self.file_id = data.get('file_id')
        self.file_unique_id = data.get('file_unique_id')
        self.thumbnail = PhotoSize(data['thumbnail']) if 'thumbnail' in data else None
        self.file_name = data.get('file_name')
        self.mime_type = data.get('mime_type')
        self.file_size = data.get('file_size')

class Animation:
    def __init__(self, data: dict):
        self.file_id = data.get('file_id')
        self.file_unique_id = data.get('file_unique_id')
        self.width = data.get('width')
        self.height = data.get('height')
        self.duration = data.get('duration')
        self.thumbnail = PhotoSize(data['thumbnail']) if 'thumbnail' in data else None
        self.file_name = data.get('file_name')
        self.mime_type = data.get('mime_type')
        self.file_size = data.get('file_size')

class Audio:
    def __init__(self, data: dict):
        self.file_id = data.get('file_id')
        self.file_unique_id = data.get('file_unique_id')
        self.duration = data.get('duration')
        self.performer = data.get('performer')
        self.title = data.get('title')
        self.file_name = data.get('file_name')
        self.mime_type = data.get('mime_type')
        self.file_size = data.get('file_size')
        self.thumbnail = PhotoSize(data['thumbnail']) if 'thumbnail' in data else None

class Voice:
    def __init__(self, data: dict):
        self.file_id = data.get('file_id')
        self.file_unique_id = data.get('file_unique_id')
        self.duration = data.get('duration')
        self.mime_type = data.get('mime_type')
        self.file_size = data.get('file_size')

class Video:
    def __init__(self, data: dict):
        self.file_id = data.get('file_id')
        self.file_unique_id = data.get('file_unique_id')
        self.width = data.get('width')
        self.height = data.get('height')
        self.duration = data.get('duration')
        self.thumbnail = PhotoSize(data['thumbnail']) if 'thumbnail' in data else None
        self.file_name = data.get('file_name')
        self.mime_type = data.get('mime_type')
        self.file_size = data.get('file_size')

class VideoNote:
    def __init__(self, data: dict):
        self.file_id = data.get('file_id')
        self.file_unique_id = data.get('file_unique_id')
        self.length = data.get('length')
        self.duration = data.get('duration')
        self.thumbnail = PhotoSize(data['thumbnail']) if 'thumbnail' in data else None
        self.file_size = data.get('file_size')

class Sticker:
    def __init__(self, data: dict):
        self.file_id = data.get('file_id')
        self.file_unique_id = data.get('file_unique_id')
        self.type = data.get('type')
        self.width = data.get('width')
        self.height = data.get('height')
        self.is_animated = data.get('is_animated', False)
        self.is_video = data.get('is_video', False)
        self.thumbnail = PhotoSize(data['thumbnail']) if 'thumbnail' in data else None
        self.emoji = data.get('emoji')
        self.set_name = data.get('set_name')
        self.premium_animation = File(data['premium_animation']) if 'premium_animation' in data else None
        self.mask_position = MaskPosition(data['mask_position']) if 'mask_position' in data else None
        self.custom_emoji_id = data.get('custom_emoji_id')
        self.needs_repeating = data.get('needs_repeating')
        self.file_size = data.get('file_size')

class Story:
    def __init__(self, data: dict):
        self.chat = Chat(data['chat']) if 'chat' in data else None
        self.id = data.get('id')

class File:
    def __init__(self, data: dict):
        self.file_id = data.get('file_id')
        self.file_unique_id = data.get('file_unique_id')
        self.file_size = data.get('file_size')
        self.file_path = data.get('file_path')

class MaskPosition:
    def __init__(self, data: dict):
        self.point = data.get('point')
        self.x_shift = data.get('x_shift')
        self.y_shift = data.get('y_shift')
        self.scale = data.get('scale')

class PollOption:
    def __init__(self, data: dict):
        self.text = data.get('text')
        self.voter_count = data.get('voter_count', 0)
        self.text_entities = [MessageEntity(e) for e in data.get('text_entities', [])]

class Poll:
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.question = data.get('question')
        self.question_entities = [MessageEntity(e) for e in data.get('question_entities', [])]
        self.options = [PollOption(o) for o in data.get('options', [])]
        self.total_voter_count = data.get('total_voter_count', 0)
        self.is_closed = data.get('is_closed', False)
        self.is_anonymous = data.get('is_anonymous', True)
        self.type = data.get('type')
        self.allows_multiple_answers = data.get('allows_multiple_answers', False)
        self.correct_option_id = data.get('correct_option_id')
        self.explanation = data.get('explanation')
        self.explanation_entities = [MessageEntity(e) for e in data.get('explanation_entities', [])]
        self.open_period = data.get('open_period')
        self.close_date = data.get('close_date')

class MessageEntity:
    def __init__(self, data: dict):
        self.type = data.get('type')
        self.offset = data.get('offset')
        self.length = data.get('length')
        self.url = data.get('url')
        self.user = User(data['user']) if 'user' in data else None
        self.language = data.get('language')
        self.custom_emoji_id = data.get('custom_emoji_id')

class Invoice:
    def __init__(self, data: dict):
        self.title = data.get('title')
        self.description = data.get('description')
        self.start_parameter = data.get('start_parameter')
        self.currency = data.get('currency')
        self.total_amount = data.get('total_amount')

class SuccessfulPayment:
    def __init__(self, data: dict):
        self.currency = data.get('currency')
        self.total_amount = data.get('total_amount')
        self.invoice_payload = data.get('invoice_payload')
        self.subscription_expiration_date = data.get('subscription_expiration_date')
        self.is_recurring = data.get('is_recurring', False)
        self.is_first_recurring = data.get('is_first_recurring', False)
        self.shipping_option_id = data.get('shipping_option_id')
        self.order_info = OrderInfo(data['order_info']) if 'order_info' in data else None
        self.telegram_payment_charge_id = data.get('telegram_payment_charge_id')
        self.provider_payment_charge_id = data.get('provider_payment_charge_id')

class RefundedPayment:
    def __init__(self, data: dict):
        self.currency = data.get('currency')
        self.total_amount = data.get('total_amount')
        self.invoice_payload = data.get('invoice_payload')
        self.telegram_payment_charge_id = data.get('telegram_payment_charge_id')
        self.provider_payment_charge_id = data.get('provider_payment_charge_id')

class OrderInfo:
    def __init__(self, data: dict):
        self.name = data.get('name')
        self.phone_number = data.get('phone_number')
        self.email = data.get('email')
        self.shipping_address = ShippingAddress(data['shipping_address']) if 'shipping_address' in data else None

class ShippingAddress:
    def __init__(self, data: dict):
        self.country_code = data.get('country_code')
        self.state = data.get('state')
        self.city = data.get('city')
        self.street_line1 = data.get('street_line1')
        self.street_line2 = data.get('street_line2')
        self.post_code = data.get('post_code')

class PassportData:
    def __init__(self, data: dict):
        self.data = [EncryptedPassportElement(e) for e in data.get('data', [])]
        self.credentials = EncryptedCredentials(data['credentials']) if 'credentials' in data else None

class EncryptedPassportElement:
    def __init__(self, data: dict):
        self.type = data.get('type')
        self.data = data.get('data')
        self.phone_number = data.get('phone_number')
        self.email = data.get('email')
        self.files = [PassportFile(f) for f in data.get('files', [])]
        self.front_side = PassportFile(data['front_side']) if 'front_side' in data else None
        self.reverse_side = PassportFile(data['reverse_side']) if 'reverse_side' in data else None
        self.selfie = PassportFile(data['selfie']) if 'selfie' in data else None
        self.translation = [PassportFile(f) for f in data.get('translation', [])]
        self.hash = data.get('hash')

class PassportFile:
    def __init__(self, data: dict):
        self.file_id = data.get('file_id')
        self.file_unique_id = data.get('file_unique_id')
        self.file_size = data.get('file_size')
        self.file_date = data.get('file_date')

class EncryptedCredentials:
    def __init__(self, data: dict):
        self.data = data.get('data')
        self.hash = data.get('hash')
        self.secret = data.get('secret')

class WebAppData:
    def __init__(self, data: dict):
        self.data = data.get('data')
        self.button_text = data.get('button_text')

class ProximityAlertTriggered:
    def __init__(self, data: dict):
        self.traveler = User(data['traveler']) if 'traveler' in data else None
        self.watcher = User(data['watcher']) if 'watcher' in data else None
        self.distance = data.get('distance')

class MessageAutoDeleteTimerChanged:
    def __init__(self, data: dict):
        self.message_auto_delete_time = data.get('message_auto_delete_time')

class ChatBoostAdded:
    def __init__(self, data: dict):
        self.boost_count = data.get('boost_count')

class ChatBackground:
    def __init__(self, data: dict):
        self.type = data.get('type')  # BackgroundType object

class UsersShared:
    def __init__(self, data: dict):
        self.request_id = data.get('request_id')
        self.users = [SharedUser(u) for u in data.get('users', [])]

class SharedUser:
    def __init__(self, data: dict):
        self.user_id = data.get('user_id')
        self.first_name = data.get('first_name')
        self.last_name = data.get('last_name')
        self.username = data.get('username')
        self.photo = [PhotoSize(p) for p in data.get('photo', [])]

class ChatShared:
    def __init__(self, data: dict):
        self.request_id = data.get('request_id')
        self.chat_id = data.get('chat_id')
        self.title = data.get('title')
        self.username = data.get('username')
        self.photo = [PhotoSize(p) for p in data.get('photo', [])]

class WriteAccessAllowed:
    def __init__(self, data: dict):
        self.from_request = data.get('from_request', False)
        self.web_app_name = data.get('web_app_name')
        self.from_attachment_menu = data.get('from_attachment_menu', False)

class VideoChatScheduled:
    def __init__(self, data: dict):
        self.start_date = data.get('start_date')

class VideoChatStarted:
    def __init__(self, data: dict):
        pass  # No fields

class VideoChatEnded:
    def __init__(self, data: dict):
        self.duration = data.get('duration')

class VideoChatParticipantsInvited:
    def __init__(self, data: dict):
        self.users = [User(u) for u in data.get('users', [])]

class GiftInfo:
    def __init__(self, data: dict):
        self.gift = data.get('gift')  # dict
        self.owned_gift_id = data.get('owned_gift_id')
        self.convert_star_count = data.get('convert_star_count')
        self.prepaid_upgrade_star_count = data.get('prepaid_upgrade_star_count')
        self.is_upgrade_separate = data.get('is_upgrade_separate')
        self.can_be_upgraded = data.get('can_be_upgraded')
        self.text = data.get('text')
        self.entities = [MessageEntity(e) for e in data.get('entities', [])]
        self.is_private = data.get('is_private', False)
        self.unique_gift_number = data.get('unique_gift_number')

class UniqueGiftInfo:
    def __init__(self, data: dict):
        self.gift = data.get('gift')
        self.origin = data.get('origin')
        self.last_resale_currency = data.get('last_resale_currency')
        self.last_resale_amount = data.get('last_resale_amount')
        self.owned_gift_id = data.get('owned_gift_id')
        self.transfer_star_count = data.get('transfer_star_count')
        self.next_transfer_date = data.get('next_transfer_date')

class InlineKeyboardMarkup:
    def __init__(self, data: dict):
        self.inline_keyboard = data.get('inline_keyboard', [])

# Full support for ChatMember and other types can be added later,
# but the current set is sufficient for most tasks.