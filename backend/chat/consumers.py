# chat/consumers.py
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone
from api.models import ChatGroup, Message, Notification, Medics
import re
from asgiref.sync import sync_to_async


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope["url_route"]["kwargs"]["group_id"]
        try:
            group = await database_sync_to_async(ChatGroup.objects.get)(token_group=self.group_id)
        except ChatGroup.DoesNotExist:
            return await self.close(code=4004)

        # Авторизация: пользователь должен быть участником
        ok = False
        if hasattr(self.scope["user"], "medic_profile"):
            ok = (group.doctor_id == self.scope["user"].medic_profile.id)
        elif "firebase_user" in self.scope:
            ok = group.firebase_user_id == self.scope["firebase_user"].uid
        if not ok:
            return await self.close(code=4003)

        self.room_name = f"chat_{self.group_id}"
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_name"):
            await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        text = content.get("message", "").strip()
        if not text:
            return
        from asgiref.sync import sync_to_async

        if "firebase_user" in self.scope:
            sender_id = self.scope["firebase_user"].uid

            # Получаем doctor_firebase_id до первого "_"
            match = re.match(r"([^_]+)", self.group_id)
            if match:
                doctor_firebase_id = match.group(1)

                # Получаем Medics и создаём уведомление — всё через async
                try:
                    doctor = await database_sync_to_async(Medics.objects.get)(doctor_firebase_id=doctor_firebase_id)
                    await database_sync_to_async(Notification.objects.create)(
                        doctor=doctor,
                        title="New Message",
                        message=f"New message in chat from {sender_id}"
                    )
                except Medics.DoesNotExist:
                    pass

        else:
            if hasattr(self.scope["user"], "medic_profile") and self.scope["user"].medic_profile:
                sender_id = str(self.scope["user"].medic_profile.doctor_firebase_id)
            else:
                return await self.close(code=4003)  # Ошибка, если у пользователя нет medic_profile

        try:
            group = await database_sync_to_async(ChatGroup.objects.get)(token_group=self.group_id)
            message = await database_sync_to_async(Message.objects.create)(
                group_id=group.id, sender_id=sender_id, content=text
            )
            # Рассылаем всем участникам
            await self.channel_layer.group_send(
                self.room_name,
                {
                    "type": "chat.message",
                    "id": str(message.id),
                    "sender_id": sender_id,
                    "content": text,
                    "timestamp": timezone.now().timestamp(),
                },
            )
        except ChatGroup.DoesNotExist:
            return await self.close(code=4004)

    async def chat_message(self, event):
        await self.send_json(event)


def create_notification_for_doctor(doctor, title, message):
    Notification.objects.create(doctor=doctor, title=title, message=message)
