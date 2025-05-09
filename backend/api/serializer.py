from rest_framework import serializers
from .models import Medics, Sessions, Client, Hospital, Pharmacy, ChatGroup, Message

from rest_framework import serializers
from .models import Medics


class MedicsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medics
        fields = ('id', 'medic_name', 'speciality', 'medic_image', 'price', 'hospital', 'favorites')


class SessionsSerializer(serializers.ModelSerializer):
    medics = MedicsSerializer()

    class Meta:
        model = Sessions
        fields = ('id', 'appointment', 'medics', 'client', 'fid')


class SessionsSerializer3(serializers.ModelSerializer):

    class Meta:
        model = Sessions
        fields = ('appointment',)


class SessionsSerializer2(serializers.ModelSerializer):
    class Meta:
        model = Sessions
        fields = ('id', 'appointment', 'medics', 'client', 'fid')


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ('id', 'client_name')


class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ('id', 'name', 'street_address', "city", "bed_count", "image_url", "rating", "favorites")


class PharmacySerializer(serializers.ModelSerializer):
    class Meta:
        model = Pharmacy
        fields = ('id', 'name', 'address', 'image_url', 'rating', 'phone_number', 'email')



class MedicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medics
        fields = ['id', 'medic_name', 'doctor_firebase_id', 'speciality', 'medic_image']


class ChatGroupSerializer(serializers.ModelSerializer):
    doctor = MedicSerializer()

    class Meta:
        model = ChatGroup
        fields = ['id', 'doctor', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['group', 'sender_id', 'content', 'timestamp']