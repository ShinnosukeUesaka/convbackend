from django.urls import path
from . import views

urlpatterns = [
    path('conversation/', views.conversations_view, name='conversations_view'),
    path('conversation/scenario', views.scenario, name='scenario'),
    path('conversation/chat/', views.chat, name='chat'),
    path('conversation/log/view', views.log_view, name='log_view'),
    path('conversation/log/edit', views.log_edit, name='log_edit'),
    path('conversation/action', views.log_edit, name='trigger_action'), # Ending conversation, Regenerating Conversation and other actions.
    path('conversation/reload', views.log_edit, name='reload') # Ending conversation, Regenerating Conversation and other actions
]
