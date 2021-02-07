from django.urls import path
from . import views

urlpatterns = [
    path('conversation/', views.create_conversation, name='create_conversation'),
    path('conversation/<int:conversation_id>/chat', views.chat, name='chat'),
    path('conversation/<int:conversation_id>/logs/', views.edit_log, name='get_log'),
    path('conversation/<int:conversation_id>/logs/<int:logitem_id>/', views.edit_log, name='edit_log')
]
