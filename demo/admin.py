from django.contrib import admin

# Register your models here.
from .models import Scenario, Conversation, Log, LogItem


class ScenarioAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)

class LogItemInline(admin.TabularInline):
    model = LogItem

class LogAdmin(admin.ModelAdmin):
    inlines = [
        LogItemInline,
    ]



admin.site.register(Scenario, ScenarioAdmin)
admin.site.register(Conversation)
admin.site.register(Log, LogAdmin)
admin.site.register(LogItem)
