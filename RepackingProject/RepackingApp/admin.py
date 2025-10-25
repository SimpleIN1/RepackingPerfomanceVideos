from django.contrib import admin

from RepackingApp.models import TypeMeetingModel, MeetingModel


@admin.register(TypeMeetingModel)
class TypeMeetingModelAdmin(admin.ModelAdmin):
    pass


@admin.register(MeetingModel)
class MeetingModelAdmin(admin.ModelAdmin):
    list_filter = ("type_meeting", )
    list_display = ("type_meeting", "datetime_created", "datetime_stopped", "status", )
