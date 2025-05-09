# tests/test_chat.py
import pytest, json
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from django.test import override_settings

from chat.consumers import ChatConsumer
from api.models import FirebaseUser, Medics, ChatGroup, Message

# In-memory channel layer конфигурация
CHANNEL_LAYER_SETTINGS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

# test_chat.py

from django.urls import re_path
from channels.routing import URLRouter
from chat.consumers import ChatConsumer

application = URLRouter([
    re_path(r"^ws/chat/(?P<group_id>\d+)/$", ChatConsumer.as_asgi()),
])


@override_settings(CHANNEL_LAYERS=CHANNEL_LAYER_SETTINGS)
@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_chat_flow():
    # ---------- фикстуры ----------
    dj_user = await sync_to_async(User.objects.create_user)(
        username="doc", password="pw"
    )
    medic = await sync_to_async(Medics.objects.create)(
        user=dj_user, medic_name="Dr. Who", speciality="Time"
    )

    patient = await sync_to_async(FirebaseUser.objects.create)(
        uid="uid-123", email="p@t.com", full_name="Patient Zero"
    )

    group = await sync_to_async(ChatGroup.objects.create)(
        firebase_user_id=patient.uid, doctor=medic
    )

    path = f"/ws/chat/{group.id}/"

    # ---------- WebSocket-каналы напрямую к ChatConsumer ----------
    app = application

    comm_patient = WebsocketCommunicator(app, path)
    comm_patient.scope["firebase_user"] = patient
    comm_patient.scope["user"] = patient       # для unified access

    comm_doctor = WebsocketCommunicator(app, path)
    comm_doctor.scope["user"] = dj_user

    # ---------- подключаемся ----------
    ok, _ = await comm_patient.connect()
    assert ok
    ok, _ = await comm_doctor.connect()
    assert ok

    # ---------- обмен ----------
    text = "Hello, doc!"
    await comm_patient.send_json_to({"message": text})

    recv_p = await comm_patient.receive_json_from()
    recv_d = await comm_doctor.receive_json_from()

    assert recv_p["content"] == text
    assert recv_d["content"] == text
    assert recv_d["sender_id"] == patient.uid

    # ---------- запись в БД ----------
    count = await sync_to_async(Message.objects.filter(group=group).count)()
    assert count == 1

    await comm_patient.disconnect()
    await comm_doctor.disconnect()
