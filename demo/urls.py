from django.urls import path
from . import views

urlpatterns = [
    path('conversation/', views.conversations_view, name='conversations_view'),
    path('conversation/<int:conversation_id>/', views.log_view, name='chat'),
    path('conversation/<int:conversation_id>/log/', views.log_view, name='log_view'),
    path('conversation/<int:conversation_id>/log/<int:logitem_id>/', views.edit_log, name='edit_log')
]
