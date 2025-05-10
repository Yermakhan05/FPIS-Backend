from django.urls import path
from . import views
from .views import UnavailableTimesView, get_or_create_group, get_messages_by_group

urlpatterns = [
    path('medics_all/', views.medics_all_list, name='medics_all_list'),
    path('medics/', views.medics_list, name='medics_list'),

    path('sessions/', views.sessions_list, name='sessions_list'),
    path('sessions/<str:pk>/', views.sessions_detail, name='sessions_detail'),

    path('clients/', views.client_list, name='client_list'),
    path('clients/<int:pk>/', views.client_detail, name='client_detail'),

    path('hospitals/', views.hospital_list, name='hospital_list'),
    path('pharmacy/', views.pharmacy_list, name='pharmacy_list'),

    path('add_favorite_medic/', views.add_favorite_medic, name='add_favorite_medic'),
    path('remove_favorite_medic/', views.remove_favorite_medic, name='remove_favorite_medic'),
    path('favorite_medics/<int:client_id>/', views.list_favorite_medics, name='list_favorite_medics'),

    path('add_favorite/', views.add_favorite_hospital, name='add_favorite_hospital'),
    path('remove_favorite_hospital/', views.remove_favorite_hospital, name='remove_favorite_hospital'),
    path('favorite_hospitals/<int:client_id>/', views.list_favorite_hospitals, name='list_favorite_hospitals'),

    path('unavailable-times/', UnavailableTimesView.as_view(), name='unavailable-times'),

    path('medic/register/', views.medic_register, name='medic_register'),
    path('medic/login/', views.medic_login, name='medic_login'),
    path('chats/<str:firebase_user_id>/', views.get_user_chats),

    path("register_firebase_user/", views.register_firebase_user),
    path("chat/save/", views.save_message),

    path('chat/group/<str:firebase_user_id>/<str:doctor_id>/', get_or_create_group),

    path('messages/group/<int:group_id>/', get_messages_by_group),
    path('', views.dashboard, name='dashboard'),
    path('appointments/', views.appointments_view, name='appointments'),
    path('schedule/', views.schedule_view, name='schedule'),

    path('chats/', views.chat_index, name='chat_index'),
    path('chat/<int:chat_id>/', views.chat_detail, name='chat_detail'),
    path('logout/', views.logout_view, name='logout'),

    path('consultation/create/', views.create_consultation, name='create_consultation'),
    path('documents/<int:document_id>/download/', views.download_document, name='download_document'),
    path('documents/<str:fid>/', views.list_documents, name='list_documents'),
]
