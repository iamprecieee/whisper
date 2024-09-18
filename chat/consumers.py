from channels.generic.websocket import AsyncWebsocketConsumer
from .utils import (
    confirm_authorization,
    check_user_in_chamber,
    ChamberDetail,
    set_user_status,
    create_new_message,
    get_replied_message,
    create_new_reply,
    generate_random_filename,
    create_new_media_message,
    update_media_message,
    get_active_users_count,
)
import json
from django.utils.dateformat import format
from base64 import b64encode


class ChamberConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.chamber = None
        self.chamber_id = None
        self.chamber_group_name = None
        self.user = None
        self.username = None

    async def connect(self):
        """
        Initiates handshake to connect consumer to websocket client and join the chat group.
        Includes extra authorization check for 'request.user' to ensure current user is part of chat.
        """
        # Retrieve 'chamber_id' value from scope and use it to set group name
        self.chamber_id = self.scope["url_route"]["kwargs"]["chamber_id"]
        self.chamber = await ChamberDetail(self.chamber_id).retrieve_chamber_obj()
        self.chamber_group_name = self.chamber_id

        headers = dict(self.scope["headers"])
        user = await confirm_authorization(headers)
        self.user = user
        self.username = user.username
        user_in_chamber = await check_user_in_chamber(self.user.id, self.chamber_id)
        if not user_in_chamber:
            await self.close(code=4001)

        # Join chamber group and confirm websocket connection
        await self.channel_layer.group_add(self.chamber_group_name, self.channel_name)
        await self.accept()

        await set_user_status(self.user, status="online")
        active_count = await get_active_users_count(self.chamber_id)
        await self.channel_layer.group_send(
            self.chamber_group_name, {"type": "chat.active", "content": active_count}
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.chamber_group_name, self.channel_name
        )
        await set_user_status(self.user, status="offline")
        active_count = await get_active_users_count(self.chamber_id)
        await self.channel_layer.group_send(
            self.chamber_group_name, {"type": "chat.active", "content": active_count}
        )

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            text_data_json = json.loads(text_data)
            message = text_data_json.get("message")
            message_type = text_data_json.get("message_type")

            # Send message to chamber group
            if message_type == "message":
                if message:
                    message_id, created = await create_new_message(
                        message, self.user, self.chamber
                    )
                    await self.channel_layer.group_send(
                        self.chamber_group_name,
                        {
                            "type": "chat.message",
                            "id": str(message_id),
                            "content": message,
                            "sender": self.username,
                            "created": format(created, "M. d, Y"),
                            "time": format(created, "P"),
                        },
                    )
            elif message_type == "reply":
                previous_message_id = text_data_json.get("previous_message_id")
                if message:
                    replied_message = await get_replied_message(
                        previous_message_id, self.chamber
                    )
                    if replied_message["message_type"] == "IMG":
                        previous_message_content = "IMAGE"
                    elif replied_message["message_type"] == "AUD":
                        previous_message_content = "AUDIO"
                    elif replied_message["message_type"] == "VID":
                        previous_message_content = "VIDEO"
                    else:
                        previous_message_content = replied_message["text_content"]

                    reply_id, created = await create_new_reply(
                        self.user,
                        replied_message["sender"],
                        previous_message_content,
                        previous_message_id,
                        self.chamber,
                        message,
                    )
                    await self.channel_layer.group_send(
                        self.chamber_group_name,
                        {
                            "type": "chat.reply",
                            "reply_format": "text",
                            "id": str(reply_id),
                            "content": message,
                            "previous_sender": replied_message["sender"],
                            "previous_message_content": previous_message_content,
                            "previous_message_id": previous_message_id,
                            "sender": self.username,
                            "created": format(created, "M. d, Y"),
                            "time": format(created, "P"),
                        },
                    )
            elif message_type == "typing":
                print("hiiiiii")
                await self.channel_layer.group_send(
                    self.chamber_group_name,
                    {
                        "type": "chat.typing",
                        "username": self.username,
                        "content": (
                            f"{self.user} is typing..." if message == "typing" else None
                        ),
                    },
                )
        elif bytes_data:
            """
            Seperates the bytes data into its audio and json components using the delimiter(plain text).
            Audio data is base64-encoded, while Json data is decoded and loaded into a metadata variable.
            The message is then processed and sent as normal audio, or as an audio reply.
            """
            # Define the delimiter
            delimiter = b"<delimiter>"

            # Separate the JSON metadata from the audio data using the delimiter
            if delimiter in bytes_data:
                json_data, media_data = bytes_data.split(delimiter, 1)

                # Decode the JSON metadata
                metadata = json.loads(json_data.decode("utf-8"))
                message_type = metadata.get("message_type")
                media_type = metadata.get("media_type")

                # Handle binary data (audio message)
                filename = await generate_random_filename(media_type)
                message = b64encode(media_data).decode(
                    "utf-8"
                )  # Encode to base64 for sending as text

                if message_type != "reply":
                    media_message_id, created = await create_new_media_message(
                        media_type, self.user, self.chamber
                    )

                    await self.channel_layer.group_send(
                        self.chamber_group_name,
                        {
                            "type": "chat.media",
                            "id": str(media_message_id),
                            "content": message,
                            "filename": filename,
                            "sender": self.username,
                            "created": format(created, "M. d, Y"),
                            "time": format(created, "P"),
                        },
                    )
                    await update_media_message(
                        media_message_id, message, filename, media_type
                    )
                else:
                    """
                    For 'reply' messages.
                    """
                    previous_message_content = None
                    previous_message_id = metadata.get("previous_message_id")
                    replied_message = await get_replied_message(
                        previous_message_id, self.chamber
                    )
                    if replied_message["message_type"] == "IMG":
                        previous_message_content = "IMAGE"
                    elif replied_message["message_type"] == "AUD":
                        previous_message_content = "AUDIO"
                    elif replied_message["message_type"] == "VID":
                        previous_message_content = "VIDEO"
                    else:
                        previous_message_content = replied_message["text_content"]

                    reply_id, created = await create_new_reply(
                        self.user,
                        replied_message["sender"],
                        previous_message_content,
                        previous_message_id,
                        self.chamber,
                        media_type=media_type,
                    )
                    await self.channel_layer.group_send(
                        self.chamber_group_name,
                        {
                            "type": "chat.reply",
                            "reply_format": "media",
                            "id": str(reply_id),
                            "content": message,
                            "filename": filename,
                            "previous_sender": replied_message["sender"],
                            "previous_message_content": previous_message_content,
                            "previous_message_id": previous_message_id,
                            "time": format(created, "P"),
                            "created": format(created, "M. d, Y"),
                            "sender": self.username,
                        },
                    )
                    await update_media_message(reply_id, message, filename, media_type)

    # Receive message from chamber group
    async def chat_notification(self, event):
        text_data = json.dumps(event)
        await self.send(text_data)

    async def chat_active(self, event):
        text_data = json.dumps(event)
        await self.send(text_data)

    async def chat_message(self, event):  # Handler for chat.message
        text_data = json.dumps(event)
        await self.send(text_data)

    async def chat_reply(self, event):  # Handler for chat.reply
        text_data = json.dumps(event)
        await self.send(text_data)

    async def chat_typing(self, event):  # Handler for chat.typing
        text_data = json.dumps(event)
        await self.send(text_data)

    async def chat_media(self, event):  # Handler for chat.audio
        text_data = json.dumps(event)
        await self.send(text_data)
