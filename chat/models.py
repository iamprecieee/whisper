from django.contrib.auth import get_user_model
from django.db.models import (
    Model,
    UUIDField,
    CharField,
    ManyToManyField,
    ForeignKey,
    CASCADE,
    DateTimeField,
    TextField,
    ImageField,
    FileField,
    BooleanField,
)
from uuid import uuid4
from user.utils import GenerateUUID


User = get_user_model()


class Chamber(Model):
    id = UUIDField(primary_key=True, editable=False, default=uuid4)
    chambername = CharField(max_length=200, blank=False, unique=True, db_index=True)
    users = ManyToManyField(User)
    creator = ForeignKey(User, related_name="created_chambers", on_delete=CASCADE)
    created = DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.chambername

    def save(self, *args, **kwargs) -> None:
        if not self.chambername:
            self.chambername = GenerateUUID().random_chambertag()
        return super().save(*args, **kwargs)


class Message(Model):
    from .utils import MessageType

    id = UUIDField(primary_key=True, editable=False, default=uuid4)
    message_type = CharField(
        max_length=4, choices=MessageType.choices, default=MessageType.TEXT
    )
    text_content = TextField(blank=True)
    image_content = ImageField(upload_to="images/", blank=True)
    audio_content = FileField(upload_to="audios/", blank=True)
    video_content = FileField(upload_to="videos/", blank=True)
    is_reply = BooleanField(default=False)
    previous_message_content = TextField(blank=True, null=True)
    previous_message_id = UUIDField(blank=True, null=True)
    previous_sender = CharField(max_length=50, blank=True, null=True)
    sender = ForeignKey(User, related_name="sent_messages", on_delete=CASCADE)
    chamber = ForeignKey(Chamber, related_name="messages", on_delete=CASCADE)
    created = DateTimeField(auto_now_add=True, db_index=True)
    updated = DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.get_message_type_display()} message from {self.sender}"
