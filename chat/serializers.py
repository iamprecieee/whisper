from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer, SerializerMethodField, ListField
from rest_framework.exceptions import ValidationError
from .models import Chamber, Message
from uuid import UUID


User = get_user_model()


class ChamberSerializer(ModelSerializer):
    users = SerializerMethodField()
    user_ids = ListField(write_only=True)

    class Meta:
        model = Chamber
        fields = ["id", "chambername", "users", "creator", "created", "user_ids"]
        read_only_fields = ["id", "creator", "created"]

    def validate(self, data):
        from .utils import validate_uuid

        if data.get("user_ids"):
            for user_id in data["user_ids"]:
                validate_uuid(user_id)
        return data

    def create(self, validated_data):
        users_data = validated_data.pop("user_ids")
        current_user = self.context.get("user")
        validated_data["creator"] = current_user
        new_chamber = Chamber.objects.create(**validated_data)

        if users_data is not None:
            for user_id in users_data:
                user = User.objects.filter(id=user_id)
                if all(
                    [
                        user.exists(),
                        not Chamber.objects.filter(users__id=user_id).exists(),
                    ]
                ):
                    new_chamber.users.add(user.first())
        return new_chamber

    def get_users(self, obj):
        return [str(user.id) for user in obj.users.all()]


class MessageSerializer(ModelSerializer):
    sender = SerializerMethodField()
    chamber = SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "message_type",
            "text_content",
            "image_content",
            "audio_content",
            "video_content",
            "is_reply",
            "previous_message_content",
            "previous_message_id",
            "previous_sender",
            "sender",
            "chamber",
            "created",
        ]
        read_only_fields = ["id", "sender", "chamber", "created"]

    def get_sender(self, obj):
        return str(obj.sender.id)

    def get_chamber(self, obj):
        return str(obj.chamber.id)
