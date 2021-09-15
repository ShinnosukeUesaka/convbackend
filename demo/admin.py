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
    readonly_fields = ('created_at', )
    readonly_fields = ('type', )

class ConversationAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', )
    readonly_fields = ('id', )
    inlines = [
        LogitemInline,
    ]




#admin.site.register(Scenario, ScenarioAdmin)
admin.site.register(Scenario)
admin.site.register(Conversation, ConversationAdmin)
admin.site.register(LogItem, LogItemAdmin)
