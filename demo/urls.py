from django.urls import path
from . import views

urlpatterns = [
    path('conversation/', views.conversations_view, name='conversations_view'),
    path('conversation/chat/', views.log_view, name='chat'),
    path('conversation/log/view', views.log_view, name='log_view'),
    path('conversation/log/edit', views.log_edit, name='edit_log')
]
