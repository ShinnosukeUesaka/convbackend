from django.contrib import admin

# Register your models here.
from .models import Scenario, Conversation, LogItem, Coupon


class FirstLogitemInline(admin.TabularInline):
    model = LogItem
    fk_name = "scenario_first"
    verbose_name = "First message"
    verbose_name_plural = "First messages"

class LastLogitemInline(admin.TabularInline):
    model = LogItem
    fk_name = "scenario_last"
    verbose_name = "Last message"
    verbose_name_plural = "Last messages"

class LogitemInline(admin.TabularInline):
    model = LogItem

class ScenarioAdmin(admin.ModelAdmin):
    readonly_fields = ('id', )
    inlines = [
        FirstLogitemInline,
        LastLogitemInline,
    ]

    #https://qiita.com/maisuto/items/e160bb17ef594f3c4d50
    list_display = (
        'title_en',
        'category',
    )
    list_filter = (
        'category',
    )


class LogItemAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', )
    readonly_fields = ('type', )

class ConversationAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', )
    readonly_fields = ('id', )
    inlines = [
        LogitemInline,
    ]

class CouponAdmin(admin.ModelAdmin):
    list_filter = [
        'used',
    ]




admin.site.register(Scenario, ScenarioAdmin)
#admin.site.register(Scenario)
admin.site.register(Conversation, ConversationAdmin)
admin.site.register(LogItem, LogItemAdmin)
admin.site.register(Coupon, CouponAdmin)
