from django.contrib import admin

# Register your models here.
from .models import Scenario, Conversation, LogItem


class ScenarioAdmin(admin.ModelAdmin):
    readonly_fields = ('id', )


class LogItemAdmin(admin.ModelAdmin):
    readonly_fields = ('type', )


admin.site.register(Scenario, ScenarioAdmin)
admin.site.register(Conversation)
admin.site.register(LogItem, LogItemAdmin)
