from django.contrib import admin

# Register your models here.
from .models import Scenario, Conversation, LogItem


class LogitemInline(admin.TabularInline):
    model = LogItem

class ScenarioAdmin(admin.ModelAdmin):
    readonly_fields = ('id', )
    inlines = [
        LogitemInline,
    ]


class LogItemAdmin(admin.ModelAdmin):
    readonly_fields = ('type', )




admin.site.register(Scenario, ScenarioAdmin)
admin.site.register(Conversation)
admin.site.register(LogItem, LogItemAdmin)
