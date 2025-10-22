from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import django_jalali.db.models as jmodels

class Patient(models.Model):
    first_name = models.CharField(max_length=255, default='')
    last_name = models.CharField(max_length=255, default='')
    reason = models.TextField(default='')
    age = models.IntegerField(default=0)
    emergency = models.BooleanField(default=False)
    medications = models.TextField(default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
class VitalSigns(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    date = jmodels.jDateField()
    blood_pressure_systolic = models.IntegerField()
    blood_pressure_diastolic = models.IntegerField()
    heart_rate = models.IntegerField()
    blood_sugar = models.IntegerField()
    body_temperature = models.FloatField()

    def __str__(self):
        return f"Vital Signs for {self.patient} on {self.date}"

class ClinicalInfo(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    date = jmodels.jDateField()
    details = models.TextField()

    def __str__(self):
        return f"{self.patient.first_name} {self.patient.last_name} - {self.date}"

class Nurse(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30, default='')
    last_name = models.CharField(max_length=30, default='')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user.username

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30, default='')
    last_name = models.CharField(max_length=30, default='')
    specialization = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user.username
    

