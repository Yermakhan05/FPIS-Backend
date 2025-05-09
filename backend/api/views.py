from social_core.pipeline import user

from .models import Medics, Sessions, Client, Hospital, Pharmacy, FirebaseUser, Message
from .serializer import MedicsSerializer, SessionsSerializer, ClientSerializer, HospitalSerializer, PharmacySerializer, \
    SessionsSerializer2, ChatGroupSerializer, MessageSerializer, SessionsSerializer3
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.utils.dateparse import parse_datetime
from rest_framework.views import APIView
from rest_framework import status
from django.utils.dateparse import parse_date
from django.db.models.functions import TruncTime
from django import forms
from django.contrib.auth.models import User
from .models import Medics
from django.contrib.auth import authenticate, login


from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ChatGroup

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Client, Sessions, Consultation, Message, Document

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Max, Count, Prefetch
from django.utils import timezone
from .models import ChatGroup, Message


@login_required
def chat_index(request):
    if request.user:
        # Доктор
        chats = ChatGroup.objects.filter(doctor__user=request.user).order_by('-created_at')

        chat_doctor = [{
            'user_name': FirebaseUser.objects.get(uid=a.firebase_user_id).full_name,
            'chat': a
        }
        for a in chats]

        return render(request, 'chat/chat.html', {'chats': chat_doctor})
    else:
        # Пациент (firebase_user_id)
        firebase_id = request.session.get('firebase_user_id')
        chats = ChatGroup.objects.filter(firebase_user_id=firebase_id).order_by('-created_at')

    return render(request, 'chat/chat.html', {'chats': {}})

@login_required
def chat_detail(request, chat_id):
    chat = get_object_or_404(ChatGroup, id=chat_id)
    original_messages = chat.messages.order_by('timestamp')

    messages = [{
        'sender_name': (FirebaseUser.objects.filter(uid=a.sender_id).first() or Medics.objects.filter(
            doctor_firebase_id=a.sender_id).first() or type('obj', (), {'medic_name': 'Unknown',
                                                                        'full_name': 'Unknown'})()).full_name
        if FirebaseUser.objects.filter(uid=a.sender_id).exists()
        else (Medics.objects.filter(doctor_firebase_id=a.sender_id).first() or type('obj', (), {
            'medic_name': 'Unknown'})()).medic_name,
        'chat': a
    } for a in original_messages]

    if request.method == 'POST':
        content = request.POST.get('message')


        # if content:
        #     Message.objects.create(
        #         group=chat,
        #         sender_id=Medics.objects.get(user_id=request.user.id).doctor_firebase_id,
        #         content=content,
        #         timestamp=timezone.now()
        #     )

    return render(request, 'chat/detail.html', {
        'chat': chat,
        'messages': messages,
        'user_name': FirebaseUser.objects.get(uid=chat.firebase_user_id).full_name,
        'medic_name': chat.doctor.medic_name,
    })


@login_required
def dashboard(request):
    today = timezone.now().date()

    # Get today's appointments
    appointments = Sessions.objects.all()

    # Get appointment statistics
    total_appointments = Sessions.objects.filter(appointment=today).count()
    previous_day = today - timezone.timedelta(days=1)
    previous_appointments = Sessions.objects.filter(appointment=previous_day).count()

    if previous_appointments > 0:
        appointment_change = ((total_appointments - previous_appointments) / previous_appointments) * 100
    else:
        appointment_change = 0

    # Calculate total hours of appointments
    total_hours = 1  # Placeholder, calculate actual hours based on appointment durations

    # Get surgery count
    surgery_count = 2  # Placeholder, get actual surgery count

    # Generate schedule hours
    schedule_hours = generate_schedule_hours(today)

    if request.user.is_authenticated:
        doctor = Medics.objects.filter(user=request.user.id).first()
        context = {
            'active_page': 'overview',
            'appointments': appointments,
            'total_appointments': total_appointments,
            'appointment_change': appointment_change,
            'total_hours': total_hours,
            'surgery_count': surgery_count,
            'schedule_hours': schedule_hours,
            'doctor': doctor
        }

        return render(request, 'dashboard.html', context)
    else: return redirect('dashboard')



@login_required
def appointments_view(request):
    appointments = Sessions.objects.all().select_related('client').order_by('appointment')

    context = {
        'active_page': 'appointments',
        'appointments': appointments,
    }

    return render(request, 'appointments.html', context)


@login_required
def schedule_view(request):
    today = timezone.now().date()
    schedule_hours = generate_schedule_hours(today)

    context = {
        'active_page': 'schedule',
        'schedule_hours': schedule_hours,
    }

    return render(request, 'schedule.html', context)




# Helper function to generate schedule hours
def generate_schedule_hours(date):

    schedule_hours = []

    appointments = Sessions.objects.all()

    appointments_data = [{
            'time': a.appointment,
            'title': 'Consultation-'+a.client.full_name,
            'active': False,
            'details': False,
            'has_action': False
        }
        for a in appointments]

    hours = ['6:00', '8:00', '9:00', '10:00', '11:00', '12:00']

    for hour in hours:
        hour_appointments = [a for a in appointments_data if a['time']]
        schedule_hours.append({
            'time': hour,
            'appointments': hour_appointments
        })

    return schedule_hours


from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('medic_login')

@api_view(['GET'])
def get_messages_by_group(request, group_id):
    messages = Message.objects.filter(group_id=group_id).order_by('timestamp')
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def save_message(request):
    serializer = MessageSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_or_create_group(request, firebase_user_id, doctor_id):
    try:
        doctor = Medics.objects.get(doctor_firebase_id=doctor_id)
    except Medics.DoesNotExist:
        return Response({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)

    group, created = ChatGroup.objects.get_or_create(
        firebase_user_id=firebase_user_id,
        doctor=doctor,
        token_group=doctor.doctor_firebase_id + "_" + firebase_user_id
    )
    return Response({"id": group.id}, status=status.HTTP_200_OK)


@api_view(["POST"])
def register_firebase_user(request):
    uid = request.data.get("uid")
    email = request.data.get("email")
    full_name = request.data.get("full_name")

    if not uid or not email or not full_name:
        return Response({"error": "Missing fields"}, status=400)

    user, created = FirebaseUser.objects.get_or_create(
        uid=uid,
        defaults={"email": email, "full_name": full_name}
    )

    return Response({
        "status": "ok",
        "created": created,
        "user": {
            "uid": user.uid,
            "email": user.email,
            "full_name": user.full_name
        }
    })

@api_view(["GET"])
def get_user_chats(request, firebase_user_id):
    groups = ChatGroup.objects.filter(firebase_user_id=firebase_user_id)
    serializer = ChatGroupSerializer(groups, many=True)
    return Response(serializer.data)


def medic_register(request):
    if request.method == 'POST':
        form = MedicRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('medic_login')
    else:
        form = MedicRegisterForm()
    return render(request, 'register.html', {'form': form})

def medic_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and hasattr(user, 'medic_profile'):
            login(request, user)
            return render(request, 'dashboard.html')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials or not a doctor'})
    return render(request, 'login.html')



class MedicRegisterForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    email = forms.EmailField()

    class Meta:
        model = Medics
        fields = ['medic_name', 'speciality', 'medic_image', 'price', 'city']

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            email=self.cleaned_data['email']
        )
        medic = super().save(commit=False)
        medic.user = user
        if commit:
            medic.save()
        return medic

class UnavailableTimesView(APIView):
    def get(self, request):
        medic_id = request.query_params.get('medic_id')
        date = request.query_params.get('date')

        if not medic_id or not date:
            return Response(
                {"error": "Both 'medic_id' and 'date' query parameters are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            appointment_date = parse_date(date)
            if not appointment_date:
                return Response(
                    {"error": "Invalid date format. Use 'YYYY-MM-DD'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            sessions = Sessions.objects.filter(
                medics_id=medic_id,
                appointment__date=appointment_date,
            )

            unavailable_times = sessions.annotate(
                time=TruncTime("appointment")
            ).values_list("time", flat=True)

            # Response
            return Response(
                {"unavailable_times": list(unavailable_times)},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MedicPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
def medics_all_list(request):
    if request.method == 'GET':
        medics = Medics.objects.all()
        serializer = MedicsSerializer(medics, many=True)
        return Response(serializer.data)


@api_view(['GET', 'POST'])
def medics_list(request):
    if request.method == 'GET':
        search_query = request.GET.get('search', '')
        hospital_id = request.GET.get('hospital', None)
        city = request.GET.get('city', '')

        medics = Medics.objects.all()
        medics = medics.filter(city=city)
        if search_query:
            medics = medics.filter(Q(medic_name__icontains=search_query) | Q(speciality__icontains=search_query))

        if hospital_id:
            medics = Medics.objects.all()
            medics = medics.filter(hospital_id=hospital_id)

        paginator = MedicPagination()
        paginated_medics = paginator.paginate_queryset(medics, request)
        serializer = MedicsSerializer(paginated_medics, many=True)

        return paginator.get_paginated_response(serializer.data)

    elif request.method == 'POST':
        serializer = MedicsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
def sessions_list(request):
    if request.method == 'GET':
        user = request.GET.get('user', None)
        medic = request.GET.get('medic', None)
        date = request.GET.get('date', None)
        sessions = Sessions.objects.all()

        if user:
            sessions = sessions.filter(client_id=user)
        if medic:
            sessions = sessions.filter(medics_id=medic)
        if date:
            sessions = sessions.filter(appointment__date=date)

        serializer = SessionsSerializer(sessions, many=True)

        return Response(serializer.data)

    elif request.method == 'POST':
        if 'medics_id' not in request.data:
            return Response({"error": "medics_id field is required"}, status=status.HTTP_400_BAD_REQUEST)

        client_id = request.data.get('client_id', None)
        if client_id:
            try:
                client = FirebaseUser.objects.get(uid=client_id)
            except Client.DoesNotExist:
                return Response({"error": "Client not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"error": "client_id field is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            medic = Medics.objects.get(doctor_firebase_id=request.data['medics_id'])
        except Medics.DoesNotExist:
            return Response({"error": "Medic not found"}, status=status.HTTP_404_NOT_FOUND)

        appointment = request.data.get('appointment', None)
        if appointment:
            appointment = parse_datetime(appointment)
            if not appointment:
                return Response({"error": "Invalid date format. Use ISO 8601 format (YYYY-MM-DDTHH:MM:SS)."},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "appointment field is required"}, status=status.HTTP_400_BAD_REQUEST)

        fid = request.data['fid']

        session_data = {
            'medics': medic.id,
            'client': client.id,
            'appointment': appointment,
            "fid": fid,
        }
        serializer = SessionsSerializer2(data=session_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def sessions_detail(request, pk):
    try:
        session = Sessions.objects.get(fid=pk)
    except Sessions.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = SessionsSerializer(session)
        return Response(serializer.data)
    elif request.method == 'PUT':
        appointment = request.data.get('appointment', None)
        if appointment:
            appointment = parse_datetime(appointment)
            if not appointment:
                return Response({"error": "Invalid date format. Use ISO 8601 format (YYYY-MM-DDTHH:MM:SS)."},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "appointment field is required"}, status=status.HTTP_400_BAD_REQUEST)
        session_data = {
            'appointment': appointment,
        }
        serializer = SessionsSerializer3(session, data=session_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def client_list(request):
    if request.method == 'GET':
        clients = Client.objects.all()
        serializer = ClientSerializer(clients, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = ClientSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def client_detail(request, pk):
    try:
        client = Client.objects.get(pk=pk)
    except Client.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ClientSerializer(client)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = ClientSerializer(client, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        client.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def hospital_list(request):
    search_query = request.GET.get('search', '')
    city = request.GET.get('city', '')

    hospitals = Hospital.objects.all()

    if search_query:
        hospitals = hospitals.filter(name__icontains=search_query)

    if city:
        hospitals = hospitals.filter(city__icontains=city)

    hospitals_data = []
    for hospital in hospitals:
        hospital_data = HospitalSerializer(hospital).data
        hospitals_data.append(hospital_data)

    return Response(hospitals_data)


@api_view(['GET'])
def pharmacy_list(request):
    search_query = request.GET.get('search', '')
    city = request.GET.get('city', '')

    pharmacies = Pharmacy.objects.all()

    if search_query:
        pharmacies = pharmacies.filter(name__icontains=search_query)

    if city:
        pharmacies = pharmacies.filter(address__contains=city)

    serializer = PharmacySerializer(pharmacies, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def add_favorite_medic(request):
    client_id = request.data.get('client_id')
    medic_id = request.data.get('medic_id')

    if not client_id or not medic_id:
        return Response({"error": "client_id and medic_id are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        client = Client.objects.get(id=client_id)
        medic = Medics.objects.get(id=medic_id)
    except (Client.DoesNotExist, Medics.DoesNotExist):
        return Response({"error": "Client or Medic not found."}, status=status.HTTP_404_NOT_FOUND)

    client.favorite_medics.add(medic)
    client.save()

    return Response(
        {"message": f"Medic '{medic.medic_name}' has been added to client {client.client_name}'s favorites."},
        status=status.HTTP_200_OK)


@api_view(['GET'])
def list_favorite_medics(request, client_id):
    try:
        client = Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        return Response({"error": "Client not found."}, status=status.HTTP_404_NOT_FOUND)

    favorite_medics = client.favorite_medics.all()

    serializer = MedicsSerializer(favorite_medics, many=True)

    return Response(serializer.data)


@api_view(['POST'])
def add_favorite_hospital(request):
    client_id = request.data.get('client_id')
    hospital_id = request.data.get('hospital_id')

    if not client_id or not hospital_id:
        return Response({"error": "client_id and hospital_id are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        client = Client.objects.get(id=client_id)
        hospital = Hospital.objects.get(id=hospital_id)
    except (Client.DoesNotExist, Hospital.DoesNotExist):
        return Response({"error": "Client or Hospital not found."}, status=status.HTTP_404_NOT_FOUND)

    client.favorite_hospitals.add(hospital)
    client.save()

    return Response(
        {"message": f"Hospital '{hospital.name}' has been added to client {client.client_name}'s favorites."},
        status=status.HTTP_200_OK)


@api_view(['GET'])
def list_favorite_hospitals(request, client_id):
    try:
        client = Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        return Response({"error": "Client not found."}, status=status.HTTP_404_NOT_FOUND)

    favorite_hospitals = client.favorite_hospitals.all()

    serializer = HospitalSerializer(favorite_hospitals, many=True)

    return Response(serializer.data)


@api_view(['POST'])
def remove_favorite_medic(request):
    client_id = request.data.get('client_id')
    medic_id = request.data.get('medic_id')

    if not client_id or not medic_id:
        return Response({"error": "client_id and medic_id are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        client = Client.objects.get(id=client_id)
        medic = Medics.objects.get(id=medic_id)
    except (Client.DoesNotExist, Medics.DoesNotExist):
        return Response({"error": "Client or Medic not found."}, status=status.HTTP_404_NOT_FOUND)

    client.favorite_medics.remove(medic)
    client.save()

    return Response(
        {"message": f"Medic '{medic.medic_name}' has been removed from client {client.client_name}'s favorites."},
        status=status.HTTP_200_OK)


@api_view(['POST'])
def remove_favorite_hospital(request):
    client_id = request.data.get('client_id')
    hospital_id = request.data.get('hospital_id')

    if not client_id or not hospital_id:
        return Response({"error": "client_id and hospital_id are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        client = Client.objects.get(id=client_id)
        hospital = Hospital.objects.get(id=hospital_id)
    except (Client.DoesNotExist, Hospital.DoesNotExist):
        return Response({"error": "Client or Hospital not found."}, status=status.HTTP_404_NOT_FOUND)

    client.favorite_hospitals.remove(hospital)
    client.save()

    return Response(
        {"message": f"Hospital '{hospital.name}' has been removed from client {client.client_name}'s favorites."},
        status=status.HTTP_200_OK)


