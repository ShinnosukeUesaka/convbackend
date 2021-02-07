from django.contrib import admin

# Register your models here.
from .models import Scenario, Conversation, Log


class ScenarioAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    
admin.site.register(Scenario, ScenarioAdmin)
admin.site.register(Conversation)
admin.site.register(Log)
