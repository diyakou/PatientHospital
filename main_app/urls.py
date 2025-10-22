from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('doctor_dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('nurse_dashboard/', views.nurse_dashboard, name='nurse_dashboard'),
    path('nurse_patients/', views.nurse_patient_list, name='nurse_patient_list'),
    path('nurses/', views.nurse_list, name='nurse_list'),
    path('nurse/<int:pk>/', views.nurse_detail, name='nurse_detail'),
    path('patient/<int:pk>/delete/', views.delete_patient, name='delete_patient'),
    path('patient/<int:pk>/edit/', views.edit_patient, name='edit_patient'),
    path('nurse/patient/<int:pk>/edit/', views.edit_patient_nr, name='edit_patient_nr'),
    path('add_patient/', views.add_patient, name='add_patient'),
    path('patient/<int:pk>/', views.patient_detail, name='patient_detail'),
    path('patient_nr/<int:pk>/', views.patient_detail_nr , name='patient_detail_nr'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('patients/', views.patient_list, name='patient_list'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('edit_medications/<int:pk>/', views.edit_medications, name='edit_medications'),
    path('upload_excel/', views.upload_excel, name='upload_excel'),
    path('export_patient_data/<int:pk>/', views.export_patient_data, name='export_patient_data'),
    path('edit_vital_signs/<int:patient_id>/', views.edit_vital_signs, name='edit_vital_signs'),
    path('edit_vital_signs/<int:patient_id>/<int:vs_id>/', views.edit_vital_signs, name='edit_vital_signs_with_id'),
    path('patient_nr/<int:pk>/ai_summary/', views.patient_ai_summary_nr, name='patient_ai_summary_nr'),
]
