from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Nurse, Doctor, Patient, ClinicalInfo, VitalSigns
from django_jalali.forms import jDateField

class MedicationForm(forms.ModelForm):
    medications = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}))

    class Meta:
        model = Patient
        fields = ['medications']

class VitalSignsForm(forms.ModelForm):
    date = jDateField(widget=forms.DateInput(attrs={
        'class': 'form-control datepicker',
        'id': 'id_date'
    }))
    blood_pressure_systolic = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    blood_pressure_diastolic = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    heart_rate = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    blood_sugar = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    body_temperature = forms.FloatField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = VitalSigns
        fields = ['date', 'blood_pressure_systolic', 'blood_pressure_diastolic', 'heart_rate', 'blood_sugar', 'body_temperature']


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'reason', 'age', 'emergency', 'medications']

class ClinicalInfoForm(forms.ModelForm):
    date = jDateField(widget=forms.DateInput(attrs={'class': 'datepicker'}))
    details = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}))

    class Meta:
        model = ClinicalInfo
        fields = ['date', 'details']

class UserRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="نام")
    last_name = forms.CharField(max_length=30, required=True, label="نام خانوادگی")
    email = forms.EmailField(required=True, label="ایمیل")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        labels = {
            'username': 'نام کاربری',
            'password1': 'رمز عبور',
            'password2': 'تکرار رمز عبور',
        }

class NurseProfileForm(forms.ModelForm):
    class Meta:
        model = Nurse
        fields = ['phone_number', 'address']
        labels = {
            'phone_number': 'شماره تلفن',
            'address': 'آدرس',
        }

class DoctorProfileForm(forms.ModelForm):
    specialization = forms.CharField(max_length=100, required=True, label="تخصص")

    class Meta:
        model = Doctor
        fields = ['specialization', 'phone_number', 'address']
        labels = {
            'specialization': 'تخصص',
            'phone_number': 'شماره تلفن',
            'address': 'آدرس',
        }

class ExcelUploadForm(forms.Form):
    file = forms.FileField(label="فایل اکسل", widget=forms.FileInput(attrs={'accept': '.xlsx'}))
    patient = forms.ModelChoiceField(queryset=Patient.objects.all(), label="بیمار")