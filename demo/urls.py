from django.urls import path
from . import views

urlpatterns = [
    path('conversation/', views.conversations_view, name='conversations_view'),
    path('conversation/scenario', views.scenario, name='scenario'),
    path('conversation/scenarios', views.scenarios, name='scenarios'),
    path('conversation/chat/', views.chat, name='chat'),
    path('conversation/log/view', views.log_view, name='log_view'),
    path('conversation/log/edit', views.log_edit, name='log_edit'),
    path('dictionary', views.dictionary, name='dictionary'),
    path('conversation/reload', views.reload, name='reload') # Not implemented Ending conversation, Regenerating Conversation and other actions
]
