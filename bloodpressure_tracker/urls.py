"""bloodpressure_tracker URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from bloodpressure import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.blood_pressure_list, name='blood_pressure_list'),
    path('add/', views.add_blood_pressure, name='add_blood_pressure'),
    path('delete/<int:blood_pressure_id>/', views.delete_blood_pressure, name='delete_blood_pressure'),
    path('download/', views.download_data_excel, name='download_data_excel'),
    path('send_pdf_email/', views.generate_pdf_and_send_email, name='generate_pdf_and_send_email'),  
    path('download_pdf/', views.download_pdf, name='download_pdf'),  # Add this line for downloading the PDF
]
