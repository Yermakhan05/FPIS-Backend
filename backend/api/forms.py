from django import forms
from .models import Client, Sessions, Consultation, Document


class PatientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['client_name', 'patient_number', 'gender', 'date_of_birth', 'email']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Sessions
        fields = ['client', 'appointment', 'notes']
        widgets = {
            'appointment': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Generate a unique visit number
        from django.utils import timezone
        import random
        if not self.instance.pk:
            self.initial['visit_no'] = f"#{random.randint(100000, 999999)}"


class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['diagnosis', 'treatment', 'prescription', 'follow_up_date']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'rows': 3}),
            'treatment': forms.Textarea(attrs={'rows': 3}),
            'prescription': forms.Textarea(attrs={'rows': 3}),
            'follow_up_date': forms.DateInput(attrs={'type': 'date'}),
        }


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'patient', 'file']
