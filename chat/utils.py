from django.db.models import TextChoices
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.transaction import atomic
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import ValidationError
import jwt
from uuid import UUID
from .models import Chamber
from time import time
from random import randint
from base64 import b64decode
import json
from asgiref.sync import sync_to_async


User = get_user_model()


class MessageType(TextChoices):
    TEXT = "TXT", "Text"
    IMAGE = "IMG", "Image"
    AUDIO = "AUD", "Audio"
    VIDEO = "VID", "Video"


def validate_uuid(uuid_string):
    try:
        UUID(uuid_string)
    except:
        raise ValidationError({"UUID": "Invalid uuid format detected."})


class ChamberDetail:
    def __init__(self, chamber_id):
        self.chamber_id = chamber_id

    @sync_to_async
    def retrieve_chamber_obj(self):
        return Chamber.objects.filter(id=self.chamber_id).first()

    @sync_to_async
    def retrieve_chamber_name(self):
        return Chamber.objects.filter(id=self.chamber_id).first().chambername


@sync_to_async
def confirm_authorization(headers):
    jwt_token = None
    if headers.get("Authorization"):
        jwt_token = headers["Authorization"].split(" ")[1]
    elif headers.get(b"authorization"):
        jwt_token = headers[b"authorization"].decode("utf-8").split(" ")[1]
    if jwt_token:
        payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        return User.objects.filter(id=user_id).first()


@sync_to_async
def check_user_in_chamber(user_id, chamber_id):
    chamber = Chamber.objects.prefetch_related("users").filter(id=chamber_id).first()
    return chamber.users.filter(id=user_id).exists()


@sync_to_async
def retrieve_user_name(user_id):
    return User.objects.filter(id=user_id).first().username


@sync_to_async
def set_user_status(user, status="online"):
    if status == "online":
        user.is_online = True
    elif status == "offline":
        user.is_online = False

    user.save()


@sync_to_async
def create_new_message(content, user, chamber):
    from .models import Message

    new_message = Message.objects.create(
        text_content=content, sender=user, chamber=chamber
    )
    return new_message.id, new_message.created


@sync_to_async
def get_replied_message(message_id, chamber):
    """
    Retrieves the message that was replied to.
    """
    from .models import Message
    from .serializers import MessageSerializer

    message = Message.objects.filter(id=message_id, chamber=chamber).first()
    return MessageSerializer(message).data


@sync_to_async
def create_new_reply(
    user,
    previous_sender,
    previous_content,
    previous_message_id,
    chamber,
    content=None,
    media_type="text",
):
    """
    Create a new 'reply' message.
    """
    from .models import Message

    validate_uuid(previous_message_id)
    new_reply = Message.objects.create(
        sender=user,
        previous_sender=previous_sender,
        previous_message_content=previous_content,
        previous_message_id=previous_message_id,
        chamber=chamber,
        is_reply=True,
    )
    if media_type == "text":
        new_reply.message_type = Message.MessageType.TEXT
        new_reply.text_content = content
    elif media_type == "image":
        new_reply.message_type = Message.MessageType.IMAGE
    elif media_type == "audio":
        new_reply.message_type = Message.MessageType.AUDIO
    elif media_type == "video":
        new_reply.message_type = Message.MessageType.VIDEO

    new_reply.save()
    return new_reply.id, new_reply.created


@sync_to_async
def generate_random_filename(media_type):
    timestamp = int(time() * 1000)  # Get the current timestamp in milliseconds
    random_num = randint(0, 999999)  # Generate a random number between 0 and 999999
    if media_type == "image":
        extension = "png"
    elif media_type == "audio":
        extension = "wav"
    elif media_type == "video":
        extension = "mp4"
    return f"media_{timestamp}_{random_num}.{extension}"


@sync_to_async
def create_new_media_message(media_type, user, chamber):
    from .models import Message

    new_message = Message.objects.create(sender=user, chamber=chamber)
    if media_type == "image":
        new_message.message_type = Message.MessageType.IMAGE
    elif media_type == "audio":
        new_message.message_type = Message.MessageType.AUDIO
    elif media_type == "video":
        new_message.message_type = Message.MessageType.VIDEO

    new_message.save(update_fields=["message_type"])
    return new_message.id, new_message.created


@sync_to_async
def update_media_message(media_id, content, filename, media_type):
    """
    Saves the decoded audio data to temporary storage, and uploads from there to cloudinary.
    The audio object is then updated with the cloud details and temporary file is removed at the end.
    """
    from .models import Message

    media_data = b64decode(content)
    file_data = SimpleUploadedFile(
        name=filename,
        content=media_data,
    )
    media_message = Message.objects.filter(id=media_id).first()
    with atomic():
        if media_type == "image":
            file_data.content_type = "image/png"
            media_message.message_type = Message.MessageType.IMAGE
            media_message.image_content = file_data
        elif media_type == "audio":
            file_data.content_type = "audio/wav"
            media_message.message_type = Message.MessageType.AUDIO
            media_message.audio_content = file_data
        elif media_type == "video":
            file_data.content_type = "video/mp4"
            media_message.message_type = Message.MessageType.VIDEO
            media_message.video_content = file_data

        media_message.save()


async def send_text_message(communicator):
    message_data = {
        "message_type": "message",
        "message": "Hello. You.",
    }
    await communicator.send_to(json.dumps(message_data))


async def send_reply_text_message(communicator, previous_message_id):
    message_data = {
        "message_type": "reply",
        "message": "Hello. You.",
        "previous_message_id": previous_message_id,
    }
    await communicator.send_to(json.dumps(message_data))


async def send_image_message(communicator):
    message_data = {"message_type": "image", "media_type": "image"}
    message_json = json.dumps(message_data).encode()
    delimiter = "<delimiter>".encode()

    image_file = settings.BASE_DIR / "test-image/whisper.png"
    with open(image_file, "rb") as file:
        image_data = file.read()

    combined_data = message_json + delimiter + image_data
    await communicator.send_to(bytes_data=combined_data)


async def send_audio_message(communicator):
    message_data = {"message_type": "audio", "media_type": "audio"}
    message_json = json.dumps(message_data).encode()
    delimiter = "<delimiter>".encode()

    audio_file = settings.BASE_DIR / "test-audio/audio.wav"
    with open(audio_file, "rb") as file:
        audio_data = file.read()

    combined_data = message_json + delimiter + audio_data
    await communicator.send_to(bytes_data=combined_data)


async def send_reply_image_message(communicator, previous_message_id):
    message_data = {
        "message_type": "reply",
        "previous_message_id": previous_message_id,
        "media_type": "image",
    }
    message_json = json.dumps(message_data).encode()
    delimiter = "<delimiter>".encode()

    image_file = settings.BASE_DIR / "test-image/whisper.png"
    with open(image_file, "rb") as file:
        image_data = file.read()

    combined_data = message_json + delimiter + image_data
    await communicator.send_to(bytes_data=combined_data)


async def send_reply_audio_message(communicator, previous_message_id):
    message_data = {
        "message_type": "reply",
        "previous_message_id": previous_message_id,
        "media_type": "audio",
    }
    message_json = json.dumps(message_data).encode()
    delimiter = "<delimiter>".encode()

    audio_file = settings.BASE_DIR / "test-audio/audio.wav"
    with open(audio_file, "rb") as file:
        audio_data = file.read()

    combined_data = message_json + delimiter + audio_data
    await communicator.send_to(bytes_data=combined_data)


@sync_to_async
def get_active_users_count(chamber_id):
    chamber = Chamber.objects.prefetch_related("users").filter(id=chamber_id).first()
    return chamber.users.filter(is_online=True).count()
