from django.dispatch import receiver
from django.db.models.signals import m2m_changed
from .models import Chamber
from .utils import retrieve_user_name
from channels.layers import get_channel_layer


channel_layer = get_channel_layer()


@receiver(m2m_changed, sender=Chamber.users.through)
async def notify_new_chamber_user_websocket(sender, instance, action, pk_set, **kwargs):
    """
    Triggered when a new user joins a chamber.
    """
    if action == "post_add":
        for user_id in pk_set:
            username = await retrieve_user_name(user_id)
            await channel_layer.group_send(
                str(instance.id),
                {
                    "type": "chat.notification",
                    "content": f"{username} was added to the chat.",
                },
            )
