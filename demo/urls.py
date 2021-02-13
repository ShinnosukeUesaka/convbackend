from django.urls import path
from . import views

urlpatterns = [
    path('conversation/', views.conversations_view, name='conversations_view'),
    path('conversation/chat/', views.log_view, name='chat'),
    path('conversation/log/', views.log_view, name='log_view'),
    path('conversation/log/<int:logitem_id>/', views.edit_log, name='edit_log')
]
