from django.contrib.auth.models import User
from django.db import models


class Client(models.Model):
    client_name = models.CharField(max_length=255)
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    patient_number = models.CharField(max_length=20, unique=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.client_name


class Hospital(models.Model):
    name = models.CharField(max_length=255)
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    bed_count = models.PositiveIntegerField()
    image_url = models.URLField(max_length=500, blank=True)
    rating = models.FloatField()
    favorites = models.ManyToManyField(Client, related_name="favorite_hospitals", blank=True)

    def __str__(self):
        return self.name


class Pharmacy(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    image_url = models.URLField(max_length=500, blank=True)
    rating = models.FloatField()
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()

    def __str__(self):
        return self.name


class Medics(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='medic_profile', null=True, blank=True)
    medic_name = models.CharField(max_length=255, default="Dr. ")
    speciality = models.CharField(max_length=255, default="")
    medic_image = models.CharField(max_length=255, default="")
    price = models.IntegerField(default=0)
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True)
    favorites = models.ManyToManyField(Client, related_name="favorite_medics", blank=True)
    city = models.CharField(max_length=255, null=True)
    doctor_firebase_id = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.speciality + " " + self.medic_name



class ChatGroup(models.Model):
    firebase_user_id = models.CharField(max_length=255)
    doctor = models.ForeignKey("Medics", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    token_group = models.CharField(max_length=64, unique=True, null=True)

    def __str__(self):
        return f"Chat: {self.firebase_user_id} - {self.doctor.medic_name}"


class Message(models.Model):
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name='messages')
    sender_id = models.CharField(max_length=255)  # Firebase UID или doctor.id
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"From {self.sender_id}: {self.content[:20]}"


class FirebaseUser(models.Model):
    uid = models.CharField(max_length=128, unique=True)  # Firebase UID
    email = models.EmailField(max_length=255)
    full_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.email})"


class Sessions(models.Model):
    medics = models.ForeignKey(Medics, on_delete=models.CASCADE)
    client = models.ForeignKey(FirebaseUser, on_delete=models.CASCADE)
    appointment = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    fid = models.CharField(max_length=128, unique=True, null=True)

    def __str__(self):
        return f"{self.medics.medic_name} ({self.medics.speciality}) with {self.client.full_name}"


class Consultation(models.Model):
    appointment = models.ForeignKey(Sessions, on_delete=models.CASCADE, related_name='consultation')
    diagnosis = models.TextField()
    treatment = models.TextField()
    prescription = models.TextField(blank=True, null=True)
    follow_up_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"Consultation for {self.appointment}"


class Document(models.Model):
    title = models.CharField(max_length=100)
    patient = models.ForeignKey(FirebaseUser, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.patient.full_name}"


class Notification(models.Model):
    doctor = models.ForeignKey(Medics, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
