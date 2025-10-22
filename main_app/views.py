from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from .models import Patient, ClinicalInfo, Nurse, Doctor, VitalSigns
from .forms import ExcelUploadForm, UserRegisterForm, NurseProfileForm, DoctorProfileForm, PatientForm, ClinicalInfoForm, VitalSignsForm, MedicationForm , ExcelUploadForm
from django.contrib.auth.forms import AuthenticationForm
from .decorators import nurse_required
import pandas as pd
import tempfile
import os
from django.db.models import Max

from .services.ai_summary import generate_patient_summary

def home(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'nurse'):
            return redirect('nurse_dashboard')
        elif hasattr(request.user, 'doctor'):
            return redirect('doctor_dashboard')
    else:
        return redirect('login')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"خوش آمدید {user.username}")

            if hasattr(user, 'nurse'):
                return redirect('nurse_dashboard')
            elif hasattr(user, 'doctor'):
                return redirect('doctor_dashboard')
            else:
                return redirect('home')
    else:
        form = AuthenticationForm()
    
    return render(request, 'main_app/login.html', {'form': form})

def register(request):
    if request.method == 'POST':
        user_form = UserRegisterForm(request.POST)
        role = request.POST.get('role')
        nurse_form = NurseProfileForm(request.POST)
        doctor_form = DoctorProfileForm(request.POST)

        if user_form.is_valid() and ((role == 'nurse' and nurse_form.is_valid()) or (role == 'doctor' and doctor_form.is_valid())):
            user = user_form.save(commit=False)
            user.first_name = user_form.cleaned_data.get('first_name')
            user.last_name = user_form.cleaned_data.get('last_name')
            user.save()

            if role == 'nurse':
                profile = nurse_form.save(commit=False)
                profile.user = user
                profile.first_name = user.first_name
                profile.last_name = user.last_name
                profile.save()
            else:
                profile = doctor_form.save(commit=False)
                profile.user = user
                profile.first_name = user.first_name
                profile.last_name = user.last_name
                profile.save()

            login(request, user)
            messages.success(request, f"ثبت‌نام با موفقیت انجام شد!")
            return redirect('nurse_dashboard' if role == 'nurse' else 'doctor_dashboard')
    else:
        user_form = UserRegisterForm()
        nurse_form = NurseProfileForm()
        doctor_form = DoctorProfileForm()

    return render(request, 'main_app/register.html', {
        'user_form': user_form,
        'nurse_form': nurse_form,
        'doctor_form': doctor_form
    })

@login_required
@nurse_required
def nurse_dashboard(request):
    nurse = get_object_or_404(Nurse, user=request.user)
    patients = Patient.objects.all()
    emergency_patients = patients.filter(emergency=True)
    return render(request, 'main_app/nurse/nurse_dashboard.html', {
        'nurse': nurse, 
        'patients': patients,
        'emergency_patients': emergency_patients
    })

@login_required
@nurse_required
def edit_vital_signs(request, patient_id, vs_id=None):
    patient = get_object_or_404(Patient, pk=patient_id)
    
    if vs_id:
        vital_sign = get_object_or_404(VitalSigns, pk=vs_id)
    else:
        vital_sign = None

    if request.method == 'POST':
        if vital_sign:
            form = VitalSignsForm(request.POST, instance=vital_sign)
        else:
            form = VitalSignsForm(request.POST)
        if form.is_valid():
            new_vital_sign = form.save(commit=False)
            new_vital_sign.patient = patient
            new_vital_sign.save()
            return redirect('patient_detail_nr', pk=patient.id)
    else:
        if vital_sign:
            form = VitalSignsForm(instance=vital_sign)
        else:
            form = VitalSignsForm()

    return render(request, 'main_app/nurse/edit_vital_signs.html', {'form': form, 'patient': patient})
@login_required
@nurse_required

def add_patient(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        vitalSignsForm = VitalSignsForm(request.POST)
        if form.is_valid() and vitalSignsForm.is_valid():
            patient = form.save()
            vital = vitalSignsForm.save(commit=False)
            vital.patient = patient
            vital.save()
            messages.success(request, "بیمار با موفقیت اضافه شد!")
            return redirect('nurse_patient_list')
        else:
            print(form.errors)
            print(vitalSignsForm.errors)
    else:
        form = PatientForm()
        vitalSignsForm = VitalSignsForm()
    return render(request, 'main_app/nurse/add_patient.html', {'form': form, "Vital_signs_form": vitalSignsForm})

@login_required
@nurse_required
def nurse_patient_list(request):
    nurse = get_object_or_404(Nurse, user=request.user)
    patients = Patient.objects.all()
    return render(request, 'main_app/nurse/nurse_patient_list.html', {'nurse': nurse, 'patients': patients})

@login_required
@nurse_required
def delete_patient(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        patient.delete()
        messages.success(request, "بیمار با موفقیت حذف شد!")
        return redirect('nurse_patient_list')
    return render(request, 'main_app/nurse/delete_patient_confirm.html', {'patient': patient})

@login_required
@nurse_required
def patient_detail_nr(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    # Limit records for faster render and smaller JSON payloads
    vital_signs_qs = VitalSigns.objects.filter(patient=patient).order_by('-date')[:200]
    vital_signs_list = list(vital_signs_qs)

    # Build chart arrays in chronological order
    dates = [vs.date.strftime('%Y-%m-%d') for vs in reversed(vital_signs_list)]
    systolic_bp = [vs.blood_pressure_systolic for vs in reversed(vital_signs_list)]
    diastolic_bp = [vs.blood_pressure_diastolic for vs in reversed(vital_signs_list)]
    heart_rates = [vs.heart_rate for vs in reversed(vital_signs_list)]
    blood_sugars = [vs.blood_sugar for vs in reversed(vital_signs_list)]
    body_temperatures = [vs.body_temperature for vs in reversed(vital_signs_list)]

    context = {
        'patient': patient,
        'vital_signs': vital_signs_qs,
        'dates': dates,
        'systolic_bp': systolic_bp,
        'diastolic_bp': diastolic_bp,
        'heart_rates': heart_rates,
        'blood_sugars': blood_sugars,
        'body_temperatures': body_temperatures,
    }

    return render(request, 'main_app/nurse/patient_detail.html', context)

# Async endpoint to fetch AI summary after page load
@login_required
def patient_ai_summary_nr(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    # Limit records for faster AI prompt creation
    vital_signs = VitalSigns.objects.filter(patient=patient).order_by('-date')[:50]
    summary, error = generate_patient_summary(patient, vital_signs)
    return JsonResponse({'summary': summary, 'error': error})

def check_alerts(vital_signs):
    alerts = []
    if vital_signs.blood_pressure_systolic > 120 or vital_signs.blood_pressure_diastolic > 80:
        alerts.append(f"بیمار {vital_signs.patient} فشار خون بیش از حد مجاز")
    if vital_signs.body_temperature > 38:
        alerts.append(f"بیمار {vital_signs.patient} دمای بدن بیش از حد مجاز (تب)")
    if vital_signs.body_temperature > 40:
        alerts.append(f"بیمار {vital_signs.patient} خطر تشنج")
    if vital_signs.body_temperature < 35:
        alerts.append(f"بیمار {vital_signs.patient} خطر افت دما")

    age = vital_signs.patient.age
    if age <= 30 and vital_signs.blood_sugar > 100:
        alerts.append(f"قند خون بیمار {vital_signs.patient} در حالت غیر طبیعی")
    elif age > 30 and age <= 40 and vital_signs.blood_sugar > 108:
        alerts.append(f"قند خون بیمار {vital_signs.patient} در حالت غیر طبیعی")
    elif age > 40 and vital_signs.blood_sugar > 160:
        alerts.append(f"قند خون بیمار {vital_signs.patient} در حالت غیر طبیعی")
    
    return alerts
@login_required
@nurse_required
def edit_patient_nr(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        form = VitalSignsForm(request.POST)
        if form.is_valid():
            vital_signs = form.save(commit=False)
            vital_signs.patient = patient
            vital_signs.save()
            check_alerts(vital_signs)
            messages.success(request, "علائم بالینی با موفقیت ثبت شد!")
            return redirect('patient_detail', pk=pk)
    else:
        form = VitalSignsForm()
    return render(request, 'main_app/nurse/edit_patient.html', {'form': form, 'patient': patient})


@login_required
def doctor_dashboard(request):
    doctor = get_object_or_404(Doctor, user=request.user)
    emergency_patients = Patient.objects.filter(emergency=True)
    patients = Patient.objects.all()

    # Get the latest vital signs for each patient
    latest_dates = VitalSigns.objects.values('patient').annotate(latest_date=Max('date'))
    latest_vital_signs = VitalSigns.objects.filter(
        date__in=[entry['latest_date'] for entry in latest_dates]
    )

    alerts = []
    for vs in latest_vital_signs:
        alerts.extend(check_alerts(vs))

    # Handle dismissing of alerts and emergency patients
    if request.method == 'POST':
        if 'dismiss_alert' in request.POST:
            alert_to_dismiss = request.POST.get('dismiss_alert')
            if alert_to_dismiss and alert_to_dismiss in alerts:
                alerts.remove(alert_to_dismiss)
                messages.success(request, f"هشدار '{alert_to_dismiss}' حذف شد.")
        elif 'dismiss_patient_alert' in request.POST:
            patient_id_to_dismiss = request.POST.get('dismiss_patient_alert')
            emergency_patients = emergency_patients.exclude(id=patient_id_to_dismiss)
            messages.success(request, f"بیمار اورژانسی با شناسه {patient_id_to_dismiss} حذف شد.")

    return render(request, 'main_app/dr/doctor_dashboard.html', {
        'doctor': doctor,
        'emergency_patients': emergency_patients,
        'patients': patients,
        'alerts': alerts
    })

@login_required
def edit_medications(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        form = MedicationForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, "داروهای بیمار با موفقیت به‌روزرسانی شد!")
            return redirect('doctor_dashboard')
    else:
        form = MedicationForm(instance=patient)
    return render(request, 'main_app/dr/edit_medications.html', {'form': form, 'patient': patient})

@login_required
def patient_list(request):
    patients = Patient.objects.all()
    return render(request, 'main_app/dr/patient_list.html', {'patients': patients})

@login_required
def nurse_list(request):
    nurses = Nurse.objects.all()
    return render(request, 'main_app/dr/nurse_list.html', {'nurses': nurses})

@login_required
def nurse_detail(request, pk):
    nurse = get_object_or_404(Nurse, pk=pk)
    return render(request, 'main_app/dr/nurse_detail.html', {
        'nurse': nurse,
        'phone_number': nurse.phone_number,
        'address': nurse.address,
    })

@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    clinical_infos = ClinicalInfo.objects.filter(patient=patient)
    vital_signs = VitalSigns.objects.filter(patient=patient).order_by('-date')

    dates = []
    systolic_bp = []
    diastolic_bp = []
    heart_rates = []
    blood_sugars = []
    body_temperatures = []

    for vs in vital_signs:
        dates.append(vs.date.strftime('%Y-%m-%d'))
        systolic_bp.append(vs.blood_pressure_systolic)
        diastolic_bp.append(vs.blood_pressure_diastolic)
        heart_rates.append(vs.heart_rate)
        blood_sugars.append(vs.blood_sugar)
        body_temperatures.append(vs.body_temperature)

    return render(request, 'main_app/dr/patient_detail.html', {
        'patient': patient,
        'clinical_infos': clinical_infos,
        'vital_signs': vital_signs,
        'dates': dates,
        'systolic_bp': systolic_bp,
        'diastolic_bp': diastolic_bp,
        'heart_rates': heart_rates,
        'blood_sugars': blood_sugars,
        'body_temperatures': body_temperatures,
    })
@login_required
def edit_patient(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, "بیمار با موفقیت ویرایش شد!")
            return redirect('patient_list')
    else:
        form = PatientForm(instance=patient)
    return render(request, 'main_app/dr/edit_patient.html', {'form': form, 'patient': patient})

@login_required
@nurse_required
def upload_excel(request):
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            patient = form.cleaned_data['patient']
            
            # Save the uploaded file to a temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            try:
                df = pd.read_excel(temp_file_path)
                errors = []
                for index, row in df.iterrows():
                    try:
                        # Ensure column names are correct
                        date = row['date']
                        blood_pressure_systolic = row['blood_pressure_systolic']
                        blood_pressure_diastolic = row['blood_pressure_diastolic']
                        heart_rate = row['heart_rate']
                        blood_sugar = row['blood_sugar']
                        body_temperature = row['body_temperature']

                        # Try to find existing vital signs for the given date
                        vital_sign, created = VitalSigns.objects.get_or_create(
                            patient=patient,
                            date=date,
                            defaults={
                                'blood_pressure_systolic': blood_pressure_systolic,
                                'blood_pressure_diastolic': blood_pressure_diastolic,
                                'heart_rate': heart_rate,
                                'blood_sugar': blood_sugar,
                                'body_temperature': body_temperature
                            }
                        )
                        if not created:
                            # If vital signs already exist for the given date, update them
                            vital_sign.blood_pressure_systolic = blood_pressure_systolic
                            vital_sign.blood_pressure_diastolic = blood_pressure_diastolic
                            vital_sign.heart_rate = heart_rate
                            vital_sign.blood_sugar = blood_sugar
                            vital_sign.body_temperature = body_temperature
                            vital_sign.save()
                    except KeyError as e:
                        errors.append(f"خطا در ردیف {index + 1}: ستون '{e.args[0]}' یافت نشد.")
                    except Exception as e:
                        errors.append(f"خطا در ردیف {index + 1}: {e}")

                if errors:
                    for error in errors:
                        messages.error(request, error)
                else:
                    messages.success(request, "فایل اکسل با موفقیت آپلود و پردازش شد.")
            except Exception as e:
                messages.error(request, f"خطا در پردازش فایل: {e}")
            finally:
                os.remove(temp_file_path)  # Remove the temporary file

            return redirect('nurse_dashboard')
    else:
        form = ExcelUploadForm()
    return render(request, 'main_app/upload_excel.html', {'form': form})
@login_required
def export_patient_data(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    vital_signs = VitalSigns.objects.filter(patient=patient).values()
    
    df = pd.DataFrame(list(vital_signs))
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={patient.first_name}_{patient.last_name}_data.xlsx'
    
    with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Vital Signs')
    
    return response