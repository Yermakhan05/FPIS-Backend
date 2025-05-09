from django.shortcuts import render
from rest_framework.views import APIView
from websockets import Response

from api.models import ChatGroup


class ChatGroupView(APIView):
    def post(self, request):
        firebase_uid = request.data["firebase_uid"]
        doctor_id = request.data["doctor_id"]
        group, _ = ChatGroup.objects.get_or_create(
            firebase_user_id=firebase_uid, doctor_id=doctor_id
        )
        return Response({"group_id": group.id})

