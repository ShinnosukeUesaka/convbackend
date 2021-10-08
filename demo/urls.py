from django.urls import path
from . import views

urlpatterns = [
    path('conversation/scenarios', views.scenarios, name='scenarios'),
    path('conversation/chat/', views.chat, name='chat'),
    path('dictionary', views.dictionary, name='dictionary'),

    path('conversation/log/view', views.log_view, name='log_view'), # Not used
    path('conversation/', views.conversations_view, name='conversations_view'), # Not used
    path('conversation/scenario', views.scenario, name='scenario'), # Not used
]
