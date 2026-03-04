from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),

    # Auth
    path('register/', views.register, name='register'), 
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),

    # Dashboards
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/mdb/', views.teacher_mdb_messages, name='mdb_message'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('teacher/keywords/', views.manage_keywords, name='manage_keywords'),
    path('teacher/mdb-messages/export-csv/', views.teacher_mdb_messages_export_csv, name='teacher_mdb_messages_export_csv'),


]
