from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_pdf, name='upload_pdf'),
    path('upload/success/', views.upload_success, name='upload_success'),
    path('get_answer/', views.get_answer, name='get_answer'),
    path('get_url/', views.get_signed_url, name='get_signed_url'),
]
