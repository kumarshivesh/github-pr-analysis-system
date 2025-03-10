# django_app/django_app/urls.py
from django.contrib import admin
from django.urls import path
from home.views import create_analysis_task, get_task_status

urlpatterns = [
    path('api/tasks/create/', create_analysis_task),
    path('api/tasks/<task_id>/status/', get_task_status),
    path('admin/', admin.site.urls),
]