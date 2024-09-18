from django.urls import path, reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APITransactionTestCase
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from .consumers import ChamberConsumer
from .models import Chamber
from user.models import User, JWTAccessToken
from time import sleep
import json
from .utils import (
    send_text_message,
    send_reply_text_message,
    send_image_message,
    send_audio_message,
    send_reply_image_message,
    send_reply_audio_message,
)
from asgiref.sync import sync_to_async


class ChamberListViewTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@gmail.com", password="Adm1!n123", is_email_verified=True
        )
        JWTAccessToken.objects.create(user=self.user)
        self.token = self.client.post(
            reverse("user:login"),
            data={"email": self.user.email, "password": "Adm1!n123"},
        ).data["access"]

        self.chamber = Chamber.objects.create(chambername="test", creator=self.user)

        self.url = reverse("chat:chamber-list")

    def test_retrieve_chamber_list_success(self):
        self.chamber.users.add(self.user)
        response = self.client.get(
            self.url, headers={"Authorization": f"Bearer {self.token}"}
        )
        self.assertEqual(type(response.data[0]), dict)
        self.assertEqual(response.status_code, 200)

    def test_create_chamber_success(self):
        response = self.client.post(
            self.url,
            headers={"Authorization": f"Bearer {self.token}"},
            data={"chambername": "test2", "user_ids": [self.user.id]},
        )
        self.assertIsNotNone(response.data["users"])

    def test_create_chamber_failure_existing_chambername(self):
        for i in range(2):
            response = self.client.post(
                self.url,
                headers={"Authorization": f"Bearer {self.token}"},
                data={"chambername": "test2", "user_ids": [self.user.id]},
            )
        self.assertEqual("Chamber with this chambername already exists.", response.data)

    def test_create_chamber_failure_invalid_uuid(self):
        response = self.client.post(
            self.url,
            headers={"Authorization": f"Bearer {self.token}"},
            data={"chambername": "test2", "user_ids": [self.user.id, "jsvgvj"]},
        )
        self.assertEqual("Invalid uuid format detected.", response.data)

    def tearDown(self) -> None:
        sleep(1)


class ChamberConsumerTestCase(APITransactionTestCase):
    async def asyncSetUp(self):
        self.user = await self.create_user(
            email="admin@gmail.com",
            username="admin",
            password="Adm1!n123",
            is_email_verified=True,
        )
        self.token = await self.get_token(self.user)

        self.user2 = await self.create_user(
            email="admin@gmail2.com",
            username="admin2",
            password="Adm1!n123",
            is_email_verified=True,
        )
        self.token2 = await self.get_token(self.user2)

        self.chamber = await self.create_chamber(chambername="test", creator=self.user)

        self.application = URLRouter(
            [
                path("testws/chamber/<str:chamber_id>/", ChamberConsumer.as_asgi()),
            ]
        )

        self.url = f"/testws/chamber/{self.chamber.id}/"

    @sync_to_async
    def create_user(self, email, username, password, is_email_verified=False):
        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            is_email_verified=is_email_verified,
        )
        JWTAccessToken.objects.create(user=user)
        return user

    @sync_to_async
    def get_token(self, user):
        return self.client.post(
            reverse("user:login"),
            data={"email": user.email, "password": "Adm1!n123"},
        ).data["access"]

    @sync_to_async
    def create_chamber(self, chambername, creator):
        return Chamber.objects.create(chambername=chambername, creator=creator)

    @sync_to_async
    def add_user_to_chamber(self, user):
        self.chamber.users.add(user)

    async def test_chamber_consumer_connect_disconnect_success(self):
        await self.asyncSetUp()
        await self.add_user_to_chamber(self.user)
        communicator = WebsocketCommunicator(
            self.application,
            self.url,
            headers={"Authorization": f"Bearer {self.token}"},
        )
        connected, subprotocol = await communicator.connect()
        self.assertEqual(connected, True)
        user = await User.objects.aget(id=self.user.id)
        self.assertEqual(user.is_online, True)

        # Test adding new user to chamber
        await self.add_user_to_chamber(self.user2)
        message = await communicator.receive_from()
        self.assertEqual(
            message,
            '{"type": "chat.active", "content": 1}',
        )
        message = await communicator.receive_from()
        self.assertEqual(
            message,
            '{"type": "chat.notification", "content": "admin2 was added to the chat."}',
        )

        # Test sending number of active users
        communicator2 = WebsocketCommunicator(
            self.application,
            self.url,
            headers={"Authorization": f"Bearer {self.token2}"},
        )
        connected, subprotocol = await communicator2.connect()
        message = await communicator.receive_from()
        self.assertEqual(
            message,
            '{"type": "chat.active", "content": 2}',
        )

        # Test sending text message
        await send_text_message(communicator)
        message = await communicator.receive_from()
        dict_message = json.loads(message)
        self.assertEqual(dict_message["type"], "chat.message")
        self.assertEqual(dict_message["sender"], "admin")

        # Test send text reply message
        await send_reply_text_message(
            communicator, previous_message_id=dict_message["id"]
        )
        message = await communicator.receive_from()
        reply_dict_message = json.loads(message)
        self.assertEqual(reply_dict_message["type"], "chat.reply")
        self.assertEqual(reply_dict_message["sender"], "admin")
        self.assertEqual(
            reply_dict_message["previous_message_content"], dict_message["content"]
        )
        self.assertEqual(reply_dict_message["previous_message_id"], dict_message["id"])

        # Test send image
        await send_image_message(communicator)
        message = await communicator.receive_from()
        image_dict_message = json.loads(message)
        self.assertEqual(image_dict_message["type"], "chat.media")
        self.assertEqual(image_dict_message["filename"].endswith("png"), True)

        # Test send audio
        await send_audio_message(communicator)
        message = await communicator.receive_from()
        audio_dict_message = json.loads(message)
        self.assertEqual(audio_dict_message["type"], "chat.media")
        self.assertEqual(audio_dict_message["filename"].endswith("wav"), True)

        # Test send image reply message
        await send_reply_image_message(
            communicator, previous_message_id=audio_dict_message["id"]
        )
        message = await communicator.receive_from()
        image_reply_dict_message = json.loads(message)
        self.assertEqual(image_reply_dict_message["type"], "chat.reply")
        self.assertEqual(image_reply_dict_message["sender"], "admin")
        self.assertEqual(image_reply_dict_message["previous_message_content"], "AUDIO")
        self.assertEqual(
            image_reply_dict_message["previous_message_id"], audio_dict_message["id"]
        )

        # Test send audio reply message
        await send_reply_audio_message(
            communicator, previous_message_id=image_reply_dict_message["id"]
        )
        message = await communicator.receive_from()
        audio_reply_dict_message = json.loads(message)
        self.assertEqual(audio_reply_dict_message["type"], "chat.reply")
        self.assertEqual(audio_reply_dict_message["sender"], "admin")
        self.assertEqual(audio_reply_dict_message["previous_message_content"], "IMAGE")
        self.assertEqual(
            audio_reply_dict_message["previous_message_id"],
            image_reply_dict_message["id"],
        )

        await communicator.disconnect()
        user = await User.objects.aget(id=self.user.id)
        self.assertEqual(user.is_online, False)

    def tearDown(self) -> None:
        sleep(1)
