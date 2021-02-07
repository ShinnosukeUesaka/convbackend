from django.contrib import admin

# Register your models here.
from .models import Scenario, Conversation, Log

admin.site.register(Scenario)
admin.site.register(Conversation)
admin.site.register(Log)
