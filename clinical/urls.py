from django.urls import path
from . import views

app_name = 'clinical'

urlpatterns = [
    path('patients/', views.patient_list_clinical, name='patient_list'),
    path('patients/<int:patient_id>/', views.patient_records, name='patient_records'),
    path('patients/<int:patient_id>/note/add/', views.add_clinical_note, name='add_clinical_note'),
    path('patients/<int:patient_id>/diagnosis/add/', views.add_diagnosis, name='add_diagnosis'),
    path('patients/<int:patient_id>/prescription/add/', views.add_prescription, name='add_prescription'),
    path('patients/<int:patient_id>/vitals/add/', views.add_vital_signs, name='add_vital_signs'),
]
